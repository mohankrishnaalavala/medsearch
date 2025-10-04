"""Elasticsearch service for hybrid search operations."""

import logging
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

        Returns:
            List of search results with combined scores
        """
        if not self.client:
            raise RuntimeError("Elasticsearch client not connected")

        # Build query
        must_clauses: List[Dict[str, Any]] = []
        should_clauses: List[Dict[str, Any]] = []

        # BM25 query
        should_clauses.append({
            "multi_match": {
                "query": query_text,
                "fields": ["title^2", "abstract", "brief_summary", "detailed_description"],
                "type": "best_fields",
                "boost": keyword_weight,
            }
        })

        # Vector similarity query
        should_clauses.append({
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": f"cosineSimilarity(params.query_vector, 'embedding') * {semantic_weight}",
                    "params": {"query_vector": query_embedding},
                },
            }
        })

        # Apply filters
        if filters:
            if "date_range" in filters and filters["date_range"]:
                date_field = "publication_date" if index_name == self.indices["pubmed"] else "start_date"
                must_clauses.append({
                    "range": {
                        date_field: {
                            "gte": filters["date_range"].get("start"),
                            "lte": filters["date_range"].get("end"),
                        }
                    }
                })

        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "should": should_clauses,
                "minimum_should_match": 1,
            }
        }

        try:
            response = await self.client.search(
                index=index_name,
                body={"query": query, "size": size, "_source": True},
            )

            results = []
            for hit in response["hits"]["hits"]:
                result = hit["_source"]
                result["_score"] = hit["_score"]
                result["_id"] = hit["_id"]
                results.append(result)

            logger.info(f"Hybrid search returned {len(results)} results from {index_name}")
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

