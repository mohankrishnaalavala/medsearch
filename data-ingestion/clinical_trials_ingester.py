"""Clinical Trials data ingestion from ClinicalTrials.gov API."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp
from elasticsearch import AsyncElasticsearch

from embeddings_generator import EmbeddingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClinicalTrialsIngester:
    """Ingest clinical trials into Elasticsearch."""

    def __init__(
        self,
        es_client: AsyncElasticsearch,
        embedding_generator: EmbeddingGenerator,
        index_name: str = "medsearch-trials",
        rate_limit: float = 1.0,  # 1 second between requests
    ) -> None:
        """
        Initialize Clinical Trials ingester.

        Args:
            es_client: Elasticsearch client
            embedding_generator: Embedding generator
            index_name: Elasticsearch index name
            rate_limit: Seconds between requests
        """
        self.es_client = es_client
        self.embedding_generator = embedding_generator
        self.index_name = index_name
        self.rate_limit = rate_limit

        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.stats = {"fetched": 0, "indexed": 0, "errors": 0}

    async def search_trials(
        self,
        query: str = "diabetes OR cancer OR hypertension",
        max_results: int = 500,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search for clinical trials.

        Args:
            query: Search query
            max_results: Maximum number of results
            page_size: Results per page

        Returns:
            List of trial dictionaries
        """
        all_trials = []
        page_token = None

        async with aiohttp.ClientSession() as session:
            while len(all_trials) < max_results:
                params = {
                    "query.term": query,
                    "pageSize": min(page_size, max_results - len(all_trials)),
                    "format": "json",
                }

                if page_token:
                    params["pageToken"] = page_token

                try:
                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()

                            studies = data.get("studies", [])
                            for study in studies:
                                trial = self._extract_trial_data(study)
                                if trial:
                                    all_trials.append(trial)

                            logger.info(f"Fetched {len(all_trials)} trials so far")

                            # Check for next page
                            page_token = data.get("nextPageToken")
                            if not page_token:
                                break

                            # Rate limiting
                            await asyncio.sleep(self.rate_limit)

                        else:
                            logger.error(f"Search failed with status {response.status}")
                            break

                except Exception as e:
                    logger.error(f"Error fetching trials: {e}")
                    self.stats["errors"] += 1
                    break

        self.stats["fetched"] = len(all_trials)
        logger.info(f"Total trials fetched: {len(all_trials)}")
        return all_trials

    def _extract_trial_data(self, study: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract trial data from API response."""
        try:
            protocol_section = study.get("protocolSection", {})
            identification_module = protocol_section.get("identificationModule", {})
            status_module = protocol_section.get("statusModule", {})
            description_module = protocol_section.get("descriptionModule", {})
            conditions_module = protocol_section.get("conditionsModule", {})
            design_module = protocol_section.get("designModule", {})
            arms_interventions_module = protocol_section.get("armsInterventionsModule", {})
            contacts_locations_module = protocol_section.get("contactsLocationsModule", {})
            sponsor_collaborators_module = protocol_section.get("sponsorCollaboratorsModule", {})

            # NCT ID
            nct_id = identification_module.get("nctId", "")

            # Title
            title = identification_module.get("officialTitle") or identification_module.get(
                "briefTitle", ""
            )

            # Brief summary
            brief_summary = description_module.get("briefSummary", "")

            # Detailed description
            detailed_description = description_module.get("detailedDescription", "")

            # Status
            status = status_module.get("overallStatus", "")

            # Phase
            phases = design_module.get("phases", [])
            phase = ", ".join(phases) if phases else "N/A"

            # Conditions
            conditions = conditions_module.get("conditions", [])

            # Interventions
            interventions = []
            for intervention in arms_interventions_module.get("interventions", []):
                interventions.append(intervention.get("name", ""))

            # Locations
            locations = []
            for location in contacts_locations_module.get("locations", []):
                city = location.get("city", "")
                country = location.get("country", "")
                if city and country:
                    locations.append(f"{city}, {country}")

            # Sponsors
            lead_sponsor = sponsor_collaborators_module.get("leadSponsor", {})
            sponsor_name = lead_sponsor.get("name", "")

            # Dates
            start_date_struct = status_module.get("startDateStruct", {})
            start_date = start_date_struct.get("date", "")

            completion_date_struct = status_module.get("completionDateStruct", {})
            completion_date = completion_date_struct.get("date", "")

            # Enrollment
            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment_count = enrollment_info.get("count", 0)

            return {
                "nct_id": nct_id,
                "title": title,
                "brief_summary": brief_summary,
                "detailed_description": detailed_description,
                "status": status,
                "phase": phase,
                "conditions": conditions,
                "interventions": interventions,
                "locations": locations,
                "sponsors": [sponsor_name] if sponsor_name else [],
                "start_date": start_date,
                "completion_date": completion_date,
                "enrollment": enrollment_count,
            }

        except Exception as e:
            logger.error(f"Error extracting trial data: {e}")
            return None

    async def index_trials(self, trials: List[Dict[str, Any]]) -> int:
        """
        Index trials into Elasticsearch with embeddings.

        Args:
            trials: List of trial dictionaries

        Returns:
            Number of trials indexed
        """
        if not trials:
            return 0

        # Generate embeddings
        texts = [
            f"{trial['title']} {trial['brief_summary']}" for trial in trials
        ]
        embeddings = self.embedding_generator.generate_embeddings_batch_sync(texts)

        # Index trials
        indexed_count = 0
        for trial, embedding in zip(trials, embeddings):
            try:
                doc = {
                    **trial,
                    "embedding": embedding,
                    "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

                await self.es_client.index(
                    index=self.index_name, id=trial["nct_id"], document=doc
                )

                indexed_count += 1
                self.stats["indexed"] += 1

            except Exception as e:
                logger.error(f"Error indexing trial {trial.get('nct_id')}: {e}")
                self.stats["errors"] += 1

        logger.info(f"Indexed {indexed_count} trials")
        return indexed_count

    async def ingest(
        self, query: str = "diabetes OR cancer OR hypertension", max_trials: int = 500
    ) -> Dict[str, int]:
        """
        Ingest clinical trials.

        Args:
            query: Search query
            max_trials: Maximum number of trials to ingest

        Returns:
            Statistics dictionary
        """
        logger.info(f"Starting Clinical Trials ingestion for query: {query}")
        logger.info(f"Target: {max_trials} trials")

        # Search for trials
        trials = await self.search_trials(query, max_trials)

        if not trials:
            logger.warning("No trials found")
            return self.stats

        # Index trials in batches
        batch_size = 50
        for i in range(0, len(trials), batch_size):
            batch = trials[i : i + batch_size]
            await self.index_trials(batch)

            logger.info(
                f"Progress: {min(i + batch_size, len(trials))}/{len(trials)} trials"
            )

        logger.info(f"Ingestion complete: {self.stats}")
        return self.stats

