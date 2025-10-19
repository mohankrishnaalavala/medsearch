"""Elasticsearch service for hybrid search operations."""

import logging
import time
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Service for Elasticsearch operations with hybrid search."""

    def __init__(self) -> None:
        """Initialize Elasticsearch client."""
        self.client: Optional[AsyncElasticsearch] = None
        self.indices = {
            "pubmed": settings.ELASTICSEARCH_INDEX_PUBMED,
            "trials": settings.ELASTICSEARCH_INDEX_TRIALS,
            "drugs": settings.ELASTICSEARCH_INDEX_DRUGS,
        }

    async def connect(self) -> None:
        """Connect to Elasticsearch."""
        try:
            self.client = AsyncElasticsearch(
                [settings.ELASTICSEARCH_URL],
                basic_auth=("elastic", settings.ELASTICSEARCH_PASSWORD),
                verify_certs=False,
                request_timeout=30,
            )
            # Test connection
            await self.client.info()
            logger.info("Connected to Elasticsearch successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Elasticsearch."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Elasticsearch")

    async def create_indices(self) -> None:
        """Create Elasticsearch indices with mappings."""
        if not self.client:
            raise RuntimeError("Elasticsearch client not connected")

        # PubMed index mapping
        pubmed_mapping = {
            "mappings": {
                "properties": {
                    "pmid": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "abstract": {"type": "text", "analyzer": "english"},
                    "authors": {"type": "keyword"},
                    "journal": {"type": "keyword"},
                    "publication_date": {"type": "date"},
                    "doi": {"type": "keyword"},
                    "mesh_terms": {"type": "keyword"},
                    "keywords": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "english": {
                            "type": "standard",
                            "stopwords": "_english_",
                        }
                    }
                },
            },
        }

        # Clinical Trials index mapping
        trials_mapping = {
            "mappings": {
                "properties": {
                    "nct_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "brief_summary": {"type": "text", "analyzer": "english"},
                    "detailed_description": {"type": "text", "analyzer": "english"},
                    "conditions": {"type": "keyword"},
                    "interventions": {"type": "keyword"},
                    "phase": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "start_date": {"type": "date"},
                    "completion_date": {"type": "date"},
                    "locations": {"type": "keyword"},
                    "sponsors": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
        }

        # FDA Drugs index mapping
        drugs_mapping = {
            "mappings": {
                "properties": {
                    "drug_name": {"type": "text", "analyzer": "english"},
                    "generic_name": {"type": "keyword"},
                    "brand_names": {"type": "keyword"},
                    "application_number": {"type": "keyword"},
                    "manufacturer": {"type": "keyword"},
                    "approval_date": {"type": "date"},
                    "indications": {"type": "text", "analyzer": "english"},
                    "warnings": {"type": "text", "analyzer": "english"},
                    "adverse_reactions": {"type": "text", "analyzer": "english"},
                    "drug_class": {"type": "keyword"},
                    "route": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
        }

        # Create indices
        for index_name, mapping in [
            (self.indices["pubmed"], pubmed_mapping),
            (self.indices["trials"], trials_mapping),
            (self.indices["drugs"], drugs_mapping),
        ]:
            try:
                exists = await self.client.indices.exists(index=index_name)
                if not exists:
                    await self.client.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created index: {index_name}")
                else:
                    logger.info(f"Index already exists: {index_name}")
            except Exception as e:
                logger.error(f"Error creating index {index_name}: {e}")
                raise

    async def hybrid_search(
        self,
        index_name: str,
        query_text: str,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        size: int = 10,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
        fusion_strategy: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and vector similarity.

        Args:
            index_name: Name of the index to search
            query_text: Text query for BM25 search
            query_embedding: Query embedding for semantic search
            filters: Optional filters to apply
            size: Number of results to return
            keyword_weight: Weight for BM25 score (0-1)
            semantic_weight: Weight for semantic score (0-1)
            fusion_strategy: 'weighted' (default) or 'rrf'

        Returns:
            List of search results with combined scores
        """
        if not self.client:
            raise RuntimeError("Elasticsearch client not connected")

        # Optionally expand common medical abbreviations at query time (no reindex needed)
        if settings.QUERY_SYNONYMS_ENABLED:
            synonyms = {
                "t2dm": ["type 2 diabetes", "type ii diabetes", "type-2 diabetes"],
                "mi": ["myocardial infarction", "heart attack"],
                "htn": ["hypertension", "high blood pressure"],
                "hf": ["heart failure", "congestive heart failure"],
                "ckd": ["chronic kidney disease"],
                "copd": ["chronic obstructive pulmonary disease"],
            }
            tokens = query_text.split()
            expanded_terms = []
            for t in tokens:
                lower = t.lower()
                if lower in synonyms:
                    expanded_terms.append("(" + " OR ".join([t] + synonyms[lower]) + ")")
                else:
                    expanded_terms.append(t)
            query_text = " ".join(expanded_terms)

        # Build filter clauses
        filter_clauses: List[Dict[str, Any]] = []
        if filters:
            if "date_range" in filters and filters["date_range"]:
                date_field = "publication_date" if index_name == self.indices["pubmed"] else "start_date"
                filter_clauses.append({
                    "range": {
                        date_field: {
                            "gte": filters["date_range"].get("start"),
                            "lte": filters["date_range"].get("end"),
                        }
                    }
                })

        # Build BM25 query with fields tailored per index
        bm25_fields = ["title^2", "abstract", "brief_summary", "detailed_description"]
        try:
            # If searching the drugs index, use drug-specific fields
            if index_name == self.indices["drugs"]:
                bm25_fields = [
                    "drug_name^3",
                    "generic_name^3",
                    "brand_names^2",
                    "indications^2",
                    "warnings^4",
                    "adverse_reactions^4",
                ]
        except Exception:
            # Fallback to default fields if indices not initialized yet
            bm25_fields = ["title^2", "abstract", "brief_summary", "detailed_description"]

        bm25_query = {
            "multi_match": {
                "query": query_text,
                "fields": bm25_fields,
                "type": "best_fields",
            }
        }
        if filter_clauses:
            bm25_query = {"bool": {"must": [bm25_query], "filter": filter_clauses}}

        # Build kNN query for vector search
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": max(size * 2, 50),
            "num_candidates": max(size * 10, 200),
        }
        if filter_clauses:
            knn_query["filter"] = filter_clauses

        try:
            t0 = time.monotonic()
            # kNN search (semantic)
            knn_body = {"knn": knn_query, "size": knn_query["k"], "_source": True}
            knn_response = await self.client.search(index=index_name, body=knn_body)
            t1 = time.monotonic()

            # BM25 search (keyword)
            bm25_body = {"query": bm25_query, "size": knn_query["k"], "_source": True}
            bm25_response = await self.client.search(index=index_name, body=bm25_body)
            t2 = time.monotonic()

            def _to_map(hits: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
                out: Dict[str, Dict[str, Any]] = {}
                for i, h in enumerate(hits, start=1):
                    out[h["_id"]] = {
                        "_source": h["_source"],
                        "score": h.get("_score", 0.0),
                        "rank": i,
                    }
                return out

            knn_hits = knn_response.get("hits", {}).get("hits", [])
            bm25_hits = bm25_response.get("hits", {}).get("hits", [])
            knn_map = _to_map(knn_hits)
            bm25_map = _to_map(bm25_hits)

            strategy = (fusion_strategy or settings.HYBRID_FUSION_STRATEGY).lower()
            combined: List[Dict[str, Any]] = []

            all_ids = set(knn_map.keys()) | set(bm25_map.keys())
            if strategy == "rrf":
                # Reciprocal Rank Fusion
                k = max(1, settings.RRF_K)
                for doc_id in all_ids:
                    r_knn = knn_map.get(doc_id, {}).get("rank")
                    r_bm25 = bm25_map.get(doc_id, {}).get("rank")
                    score = 0.0
                    if r_knn is not None:
                        score += 1.0 / (k + r_knn)
                    if r_bm25 is not None:
                        score += 1.0 / (k + r_bm25)
                    src = (knn_map.get(doc_id) or bm25_map.get(doc_id))["_source"]
                    src = dict(src)
                    src["_score"] = score
                    src["_id"] = doc_id
                    combined.append(src)
            else:
                # Default: normalized weighted sum
                max_knn = max([v["score"] for v in knn_map.values()], default=1.0) or 1.0
                max_bm25 = max([v["score"] for v in bm25_map.values()], default=1.0) or 1.0
                for doc_id in all_ids:
                    knn_norm = (knn_map.get(doc_id, {}).get("score", 0.0) / max_knn) if doc_id in knn_map else 0.0
                    bm25_norm = (bm25_map.get(doc_id, {}).get("score", 0.0) / max_bm25) if doc_id in bm25_map else 0.0
                    fused_score = semantic_weight * knn_norm + keyword_weight * bm25_norm
                    src = (knn_map.get(doc_id) or bm25_map.get(doc_id))["_source"]
                    src = dict(src)
                    src["_score"] = fused_score
                    src["_id"] = doc_id
                    combined.append(src)

            combined.sort(key=lambda x: x.get("_score", 0.0), reverse=True)
            results = combined[:size]

            if settings.LOG_SEARCH_METRICS:
                logger.info(
                    "Hybrid search %s: size=%d, knn_hits=%d, bm25_hits=%d, t_knn=%.3fs t_bm25=%.3fs",
                    strategy,
                    size,
                    len(knn_hits),
                    len(bm25_hits),
                    t1 - t0,
                    t2 - t1,
                )
            return results

        except NotFoundError:
            logger.warning(f"Index not found: {index_name}")
            return []
        except Exception as e:
            logger.error(f"Error performing hybrid search: {e}")
            raise

    async def index_document(
        self, index_name: str, document_id: str, document: Dict[str, Any]
    ) -> None:
        """Index a single document."""
        if not self.client:
            raise RuntimeError("Elasticsearch client not connected")

        try:
            await self.client.index(index=index_name, id=document_id, body=document)
            logger.debug(f"Indexed document {document_id} in {index_name}")
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise

    async def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> None:
        """Bulk index documents."""
        if not self.client:
            raise RuntimeError("Elasticsearch client not connected")

        from elasticsearch.helpers import async_bulk

        actions = [
            {
                "_index": index_name,
                "_id": doc.get("_id", None),
                "_source": doc,
            }
            for doc in documents
        ]

        try:
            success, failed = await async_bulk(self.client, actions)
            logger.info(f"Bulk indexed {success} documents, {failed} failed")
        except Exception as e:
            logger.error(f"Error bulk indexing: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch health."""
        if not self.client:
            return {"status": "down", "message": "Client not connected"}

        try:
            health = await self.client.cluster.health()
            return {
                "status": "up" if health["status"] in ["green", "yellow"] else "degraded",
                "cluster_status": health["status"],
                "number_of_nodes": health["number_of_nodes"],
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return {"status": "down", "message": str(e)}

    async def get_index_counts(self) -> Dict[str, int]:
        """Return document counts for each known index.

        Returns a dict with keys 'pubmed', 'trials', 'drugs'.
        Any failure returns 0 for that index.
        """
        if not self.client:
            raise RuntimeError("Elasticsearch client not connected")
        counts: Dict[str, int] = {"pubmed": 0, "trials": 0, "drugs": 0}
        for key, index_name in self.indices.items():
            try:
                resp = await self.client.count(index=index_name)
                counts[key] = int(resp.get("count", 0))
            except NotFoundError:
                logger.warning(f"Index not found when counting: {index_name}")
                counts[key] = 0
            except Exception as e:
                logger.error(f"Error getting count for {index_name}: {e}")
                counts[key] = 0
        return counts


# Global Elasticsearch service instance
_es_service: Optional[ElasticsearchService] = None


async def get_elasticsearch_service() -> ElasticsearchService:
    """Get global Elasticsearch service instance."""
    global _es_service
    if _es_service is None:
        _es_service = ElasticsearchService()
        await _es_service.connect()
        await _es_service.create_indices()
    return _es_service

