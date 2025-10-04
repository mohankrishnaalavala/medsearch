"""Main orchestration script for data ingestion."""

import asyncio
import logging
import os
import sys
from typing import Dict

from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch

from clinical_trials_ingester import ClinicalTrialsIngester
from embeddings_generator import get_embedding_generator
from fda_drugs_ingester import FDADrugsIngester
from pubmed_ingester import PubMedIngester

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_elasticsearch_indices(es_client: AsyncElasticsearch) -> None:
    """Create Elasticsearch indices with proper mappings."""
    # PubMed index
    pubmed_mapping = {
        "mappings": {
            "properties": {
                "pmid": {"type": "keyword"},
                "title": {"type": "text"},
                "abstract": {"type": "text"},
                "authors": {"type": "keyword"},
                "journal": {"type": "keyword"},
                "publication_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM||yyyy"},
                "doi": {"type": "keyword"},
                "mesh_terms": {"type": "keyword"},
                "keywords": {"type": "keyword"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
                "indexed_at": {"type": "date"},
            }
        }
    }

    # Clinical Trials index
    trials_mapping = {
        "mappings": {
            "properties": {
                "nct_id": {"type": "keyword"},
                "title": {"type": "text"},
                "brief_summary": {"type": "text"},
                "detailed_description": {"type": "text"},
                "status": {"type": "keyword"},
                "phase": {"type": "keyword"},
                "conditions": {"type": "keyword"},
                "interventions": {"type": "keyword"},
                "locations": {"type": "keyword"},
                "sponsors": {"type": "keyword"},
                "start_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM||yyyy"},
                "completion_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM||yyyy"},
                "enrollment": {"type": "integer"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
                "indexed_at": {"type": "date"},
            }
        }
    }

    # FDA Drugs index
    drugs_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "drug_name": {"type": "text"},
                "generic_name": {"type": "text"},
                "brand_names": {"type": "keyword"},
                "manufacturer": {"type": "keyword"},
                "application_number": {"type": "keyword"},
                "drug_class": {"type": "text"},
                "route": {"type": "keyword"},
                "indications": {"type": "text"},
                "warnings": {"type": "text"},
                "adverse_reactions": {"type": "text"},
                "dosage": {"type": "text"},
                "interactions": {"type": "text"},
                "approval_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM||yyyy"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine",
                },
                "indexed_at": {"type": "date"},
            }
        }
    }

    # Create indices
    indices = {
        "medsearch-pubmed": pubmed_mapping,
        "medsearch-trials": trials_mapping,
        "medsearch-drugs": drugs_mapping,
    }

    for index_name, mapping in indices.items():
        try:
            # Delete if exists
            if await es_client.indices.exists(index=index_name):
                await es_client.indices.delete(index=index_name)
                logger.info(f"Deleted existing index: {index_name}")

            # Create new index
            await es_client.indices.create(index=index_name, body=mapping)
            logger.info(f"Created index: {index_name}")

        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            raise


async def ingest_all_data() -> Dict[str, Dict[str, int]]:
    """Ingest data from all sources."""
    # Get configuration from environment
    pubmed_api_key = os.getenv("PUBMED_API_KEY", "")
    fda_api_key = os.getenv("FDA_API_KEY", "")
    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    es_username = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
    es_password = os.getenv("ELASTICSEARCH_PASSWORD", "changeme")
    google_project = os.getenv("GOOGLE_CLOUD_PROJECT", "medsearch-ai")

    logger.info("Starting data ingestion pipeline")
    logger.info(f"Elasticsearch URL: {es_url}")
    logger.info(f"Google Cloud Project: {google_project}")

    # Initialize Elasticsearch client
    es_client = AsyncElasticsearch(
        [es_url],
        basic_auth=(es_username, es_password),
        verify_certs=False,
    )

    try:
        # Test connection
        info = await es_client.info()
        logger.info(f"Connected to Elasticsearch: {info['version']['number']}")

        # Create indices
        logger.info("Creating Elasticsearch indices...")
        await create_elasticsearch_indices(es_client)

        # Initialize embedding generator
        logger.info("Initializing embedding generator...")
        embedding_generator = get_embedding_generator(project_id=google_project)
        embedding_generator.initialize()

        results = {}

        # 1. Ingest PubMed articles
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: PubMed Articles Ingestion")
        logger.info("=" * 80)

        pubmed_ingester = PubMedIngester(
            api_key=pubmed_api_key,
            es_client=es_client,
            embedding_generator=embedding_generator,
        )

        pubmed_stats = await pubmed_ingester.ingest(
            query="diabetes treatment OR cancer therapy OR hypertension",
            max_articles=1000,
        )
        results["pubmed"] = pubmed_stats

        # 2. Ingest Clinical Trials
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Clinical Trials Ingestion")
        logger.info("=" * 80)

        trials_ingester = ClinicalTrialsIngester(
            es_client=es_client,
            embedding_generator=embedding_generator,
        )

        trials_stats = await trials_ingester.ingest(
            query="diabetes OR cancer OR hypertension OR alzheimer",
            max_trials=500,
        )
        results["clinical_trials"] = trials_stats

        # 3. Ingest FDA Drugs
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: FDA Drugs Ingestion")
        logger.info("=" * 80)

        fda_ingester = FDADrugsIngester(
            api_key=fda_api_key,
            es_client=es_client,
            embedding_generator=embedding_generator,
        )

        fda_stats = await fda_ingester.ingest(
            search_term="",  # Get all drugs
            max_drugs=200,
        )
        results["fda_drugs"] = fda_stats

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 80)

        for source, stats in results.items():
            logger.info(f"\n{source.upper()}:")
            logger.info(f"  Fetched: {stats['fetched']}")
            logger.info(f"  Indexed: {stats['indexed']}")
            logger.info(f"  Errors: {stats['errors']}")

        total_indexed = sum(stats["indexed"] for stats in results.values())
        total_errors = sum(stats["errors"] for stats in results.values())

        logger.info(f"\nTOTAL INDEXED: {total_indexed}")
        logger.info(f"TOTAL ERRORS: {total_errors}")

        return results

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise

    finally:
        await es_client.close()


def main() -> None:
    """Main entry point."""
    try:
        results = asyncio.run(ingest_all_data())

        # Check if we met success criteria
        pubmed_indexed = results.get("pubmed", {}).get("indexed", 0)
        trials_indexed = results.get("clinical_trials", {}).get("indexed", 0)
        drugs_indexed = results.get("fda_drugs", {}).get("indexed", 0)

        success = (
            pubmed_indexed >= 1000
            and trials_indexed >= 500
            and drugs_indexed >= 200
        )

        if success:
            logger.info("\n✅ SUCCESS: All ingestion targets met!")
            sys.exit(0)
        else:
            logger.warning("\n⚠️  WARNING: Some ingestion targets not met")
            logger.warning(f"PubMed: {pubmed_indexed}/1000")
            logger.warning(f"Clinical Trials: {trials_indexed}/500")
            logger.warning(f"FDA Drugs: {drugs_indexed}/200")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ ERROR: Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

