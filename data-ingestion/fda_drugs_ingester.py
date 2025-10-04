"""FDA Drugs data ingestion from openFDA API."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp
from elasticsearch import AsyncElasticsearch

from embeddings_generator import EmbeddingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FDADrugsIngester:
    """Ingest FDA drugs into Elasticsearch."""

    def __init__(
        self,
        api_key: str,
        es_client: AsyncElasticsearch,
        embedding_generator: EmbeddingGenerator,
        index_name: str = "medsearch-drugs",
        rate_limit: float = 0.25,  # 4 requests/second
    ) -> None:
        """
        Initialize FDA Drugs ingester.

        Args:
            api_key: FDA API key
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

        self.base_url = "https://api.fda.gov/drug"
        self.stats = {"fetched": 0, "indexed": 0, "errors": 0}

    async def search_drugs(
        self, search_term: str = "", max_results: int = 200, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for FDA drugs.

        Args:
            search_term: Search term (empty for all)
            max_results: Maximum number of results
            limit: Results per request

        Returns:
            List of drug dictionaries
        """
        all_drugs = []
        skip = 0

        async with aiohttp.ClientSession() as session:
            while len(all_drugs) < max_results:
                # Use drug labels endpoint
                url = f"{self.base_url}/label.json"

                params = {
                    "api_key": self.api_key,
                    "limit": min(limit, max_results - len(all_drugs)),
                    "skip": skip,
                }

                # Add search if provided
                if search_term:
                    params["search"] = search_term

                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()

                            results = data.get("results", [])
                            for result in results:
                                drug = self._extract_drug_data(result)
                                if drug:
                                    all_drugs.append(drug)

                            logger.info(f"Fetched {len(all_drugs)} drugs so far")

                            # Check if we got fewer results than requested (end of data)
                            if len(results) < limit:
                                break

                            skip += limit

                            # Rate limiting
                            await asyncio.sleep(self.rate_limit)

                        elif response.status == 404:
                            # No more results
                            logger.info("No more results available")
                            break

                        else:
                            logger.error(f"Search failed with status {response.status}")
                            error_text = await response.text()
                            logger.error(f"Error: {error_text}")
                            break

                except Exception as e:
                    logger.error(f"Error fetching drugs: {e}")
                    self.stats["errors"] += 1
                    break

        self.stats["fetched"] = len(all_drugs)
        logger.info(f"Total drugs fetched: {len(all_drugs)}")
        return all_drugs

    def _extract_drug_data(self, label: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract drug data from FDA label."""
        try:
            # Drug name (brand name)
            brand_names = label.get("openfda", {}).get("brand_name", [])
            drug_name = brand_names[0] if brand_names else "Unknown"

            # Generic name
            generic_names = label.get("openfda", {}).get("generic_name", [])
            generic_name = generic_names[0] if generic_names else ""

            # Manufacturer
            manufacturers = label.get("openfda", {}).get("manufacturer_name", [])
            manufacturer = manufacturers[0] if manufacturers else ""

            # Application number
            application_numbers = label.get("openfda", {}).get("application_number", [])
            application_number = application_numbers[0] if application_numbers else ""

            # Drug class
            pharm_classes = label.get("openfda", {}).get("pharm_class_epc", [])
            drug_class = ", ".join(pharm_classes[:3]) if pharm_classes else ""

            # Route
            routes = label.get("openfda", {}).get("route", [])
            route = ", ".join(routes) if routes else ""

            # Indications and usage
            indications = label.get("indications_and_usage", [""])[0]

            # Warnings
            warnings_list = label.get("warnings", [])
            warnings = " ".join(warnings_list) if warnings_list else ""

            # Adverse reactions
            adverse_reactions_list = label.get("adverse_reactions", [])
            adverse_reactions = " ".join(adverse_reactions_list) if adverse_reactions_list else ""

            # Dosage and administration
            dosage_list = label.get("dosage_and_administration", [])
            dosage = " ".join(dosage_list) if dosage_list else ""

            # Drug interactions
            interactions_list = label.get("drug_interactions", [])
            interactions = " ".join(interactions_list) if interactions_list else ""

            # Effective time (approval date approximation)
            effective_time = label.get("effective_time", "")

            # Format approval date
            approval_date = ""
            if effective_time and len(effective_time) >= 8:
                # Format: YYYYMMDD
                approval_date = f"{effective_time[:4]}-{effective_time[4:6]}-{effective_time[6:8]}"

            # Create unique ID
            drug_id = application_number or f"{drug_name}_{manufacturer}".replace(" ", "_")

            return {
                "id": drug_id,
                "drug_name": drug_name,
                "generic_name": generic_name,
                "brand_names": brand_names,
                "manufacturer": manufacturer,
                "application_number": application_number,
                "drug_class": drug_class,
                "route": route,
                "indications": indications[:5000],  # Truncate long text
                "warnings": warnings[:5000],
                "adverse_reactions": adverse_reactions[:5000],
                "dosage": dosage[:2000],
                "interactions": interactions[:5000],
                "approval_date": approval_date,
            }

        except Exception as e:
            logger.error(f"Error extracting drug data: {e}")
            return None

    async def index_drugs(self, drugs: List[Dict[str, Any]]) -> int:
        """
        Index drugs into Elasticsearch with embeddings.

        Args:
            drugs: List of drug dictionaries

        Returns:
            Number of drugs indexed
        """
        if not drugs:
            return 0

        # Generate embeddings
        texts = [
            f"{drug['drug_name']} {drug['generic_name']} {drug['indications'][:500]}"
            for drug in drugs
        ]
        embeddings = self.embedding_generator.generate_embeddings_batch_sync(texts)

        # Index drugs
        indexed_count = 0
        for drug, embedding in zip(drugs, embeddings):
            try:
                doc = {
                    **drug,
                    "embedding": embedding,
                    "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

                await self.es_client.index(
                    index=self.index_name, id=drug["id"], document=doc
                )

                indexed_count += 1
                self.stats["indexed"] += 1

            except Exception as e:
                logger.error(f"Error indexing drug {drug.get('drug_name')}: {e}")
                self.stats["errors"] += 1

        logger.info(f"Indexed {indexed_count} drugs")
        return indexed_count

    async def ingest(
        self, search_term: str = "", max_drugs: int = 200
    ) -> Dict[str, int]:
        """
        Ingest FDA drugs.

        Args:
            search_term: Search term (empty for all)
            max_drugs: Maximum number of drugs to ingest

        Returns:
            Statistics dictionary
        """
        logger.info(f"Starting FDA Drugs ingestion")
        if search_term:
            logger.info(f"Search term: {search_term}")
        logger.info(f"Target: {max_drugs} drugs")

        # Search for drugs
        drugs = await self.search_drugs(search_term, max_drugs)

        if not drugs:
            logger.warning("No drugs found")
            return self.stats

        # Index drugs in batches
        batch_size = 20
        for i in range(0, len(drugs), batch_size):
            batch = drugs[i : i + batch_size]
            await self.index_drugs(batch)

            logger.info(
                f"Progress: {min(i + batch_size, len(drugs))}/{len(drugs)} drugs"
            )

        logger.info(f"Ingestion complete: {self.stats}")
        return self.stats

