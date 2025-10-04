"""PubMed data ingestion using E-utilities API."""

import asyncio
import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import aiohttp
from elasticsearch import AsyncElasticsearch

from embeddings_generator import EmbeddingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedIngester:
    """Ingest PubMed articles into Elasticsearch."""

    def __init__(
        self,
        api_key: str,
        es_client: AsyncElasticsearch,
        embedding_generator: EmbeddingGenerator,
        index_name: str = "medsearch-pubmed",
        rate_limit: float = 0.34,  # 3 requests/second with API key
    ) -> None:
        """
        Initialize PubMed ingester.

        Args:
            api_key: PubMed API key
            es_client: Elasticsearch client
            embedding_generator: Embedding generator
            index_name: Elasticsearch index name
            rate_limit: Seconds between requests
        """
        self.api_key = api_key
        self.es_client = es_client
        self.embedding_generator = embedding_generator
        self.index_name = index_name
        self.rate_limit = rate_limit

        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.stats = {"fetched": 0, "indexed": 0, "errors": 0}

    async def search_articles(
        self, query: str, max_results: int = 1000, retstart: int = 0
    ) -> List[str]:
        """
        Search PubMed for article IDs.

        Args:
            query: Search query
            max_results: Maximum number of results
            retstart: Starting index

        Returns:
            List of PubMed IDs
        """
        url = f"{self.base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 10000),
            "retstart": retstart,
            "retmode": "json",
            "api_key": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    pmids = data.get("esearchresult", {}).get("idlist", [])
                    logger.info(f"Found {len(pmids)} article IDs")
                    return pmids
                else:
                    logger.error(f"Search failed with status {response.status}")
                    return []

    async def fetch_article_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch article details for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of article dictionaries
        """
        if not pmids:
            return []

        url = f"{self.base_url}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "api_key": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    return self._parse_pubmed_xml(xml_data)
                else:
                    logger.error(f"Fetch failed with status {response.status}")
                    return []

    def _parse_pubmed_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML response."""
        articles = []

        try:
            root = ET.fromstring(xml_data)

            for article_elem in root.findall(".//PubmedArticle"):
                try:
                    article = self._extract_article_data(article_elem)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing article: {e}")
                    self.stats["errors"] += 1

        except Exception as e:
            logger.error(f"Error parsing XML: {e}")

        return articles

    def _extract_article_data(self, article_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract article data from XML element."""
        try:
            # PMID
            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            # Title
            title_elem = article_elem.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Abstract
            abstract_parts = []
            for abstract_text in article_elem.findall(".//AbstractText"):
                if abstract_text.text:
                    abstract_parts.append(abstract_text.text)
            abstract = " ".join(abstract_parts)

            # Authors
            authors = []
            for author in article_elem.findall(".//Author"):
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and fore_name is not None:
                    authors.append(f"{fore_name.text} {last_name.text}")

            # Journal
            journal_elem = article_elem.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else ""

            # Publication date
            pub_date_elem = article_elem.find(".//PubDate")
            pub_date = ""
            if pub_date_elem is not None:
                year = pub_date_elem.find("Year")
                month = pub_date_elem.find("Month")
                day = pub_date_elem.find("Day")
                parts = []
                if year is not None:
                    parts.append(year.text)
                if month is not None:
                    parts.append(month.text)
                if day is not None:
                    parts.append(day.text)
                pub_date = "-".join(parts)

            # DOI
            doi = None
            for article_id in article_elem.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

            # MeSH terms
            mesh_terms = []
            for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            # Keywords
            keywords = []
            for keyword in article_elem.findall(".//Keyword"):
                if keyword.text:
                    keywords.append(keyword.text)

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "publication_date": pub_date,
                "doi": doi,
                "mesh_terms": mesh_terms,
                "keywords": keywords,
            }

        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None

    async def index_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        Index articles into Elasticsearch with embeddings.

        Args:
            articles: List of article dictionaries

        Returns:
            Number of articles indexed
        """
        if not articles:
            return 0

        # Generate embeddings for abstracts
        texts = [
            f"{article['title']} {article['abstract']}" for article in articles
        ]
        embeddings = self.embedding_generator.generate_embeddings_batch_sync(texts)

        # Index articles
        indexed_count = 0
        for article, embedding in zip(articles, embeddings):
            try:
                doc = {
                    **article,
                    "embedding": embedding,
                    "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

                await self.es_client.index(
                    index=self.index_name, id=article["pmid"], document=doc
                )

                indexed_count += 1
                self.stats["indexed"] += 1

            except Exception as e:
                logger.error(f"Error indexing article {article.get('pmid')}: {e}")
                self.stats["errors"] += 1

        logger.info(f"Indexed {indexed_count} articles")
        return indexed_count

    async def ingest(
        self, query: str = "diabetes OR cancer OR hypertension", max_articles: int = 1000
    ) -> Dict[str, int]:
        """
        Ingest PubMed articles.

        Args:
            query: Search query
            max_articles: Maximum number of articles to ingest

        Returns:
            Statistics dictionary
        """
        logger.info(f"Starting PubMed ingestion for query: {query}")
        logger.info(f"Target: {max_articles} articles")

        # Search for article IDs
        pmids = await self.search_articles(query, max_articles)
        self.stats["fetched"] = len(pmids)

        if not pmids:
            logger.warning("No articles found")
            return self.stats

        # Process in batches
        batch_size = 100
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]

            # Fetch article details
            articles = await self.fetch_article_details(batch_pmids)

            # Index articles
            await self.index_articles(articles)

            # Rate limiting
            await asyncio.sleep(self.rate_limit)

            logger.info(
                f"Progress: {min(i + batch_size, len(pmids))}/{len(pmids)} articles"
            )

        logger.info(f"Ingestion complete: {self.stats}")
        return self.stats

