"""Data ingestion pipeline for MedSearch AI."""

from data-ingestion.clinical_trials_ingester import ClinicalTrialsIngester
from data-ingestion.embeddings_generator import EmbeddingGenerator, get_embedding_generator
from data-ingestion.fda_drugs_ingester import FDADrugsIngester
from data-ingestion.pubmed_ingester import PubMedIngester

__all__ = [
    "EmbeddingGenerator",
    "get_embedding_generator",
    "PubMedIngester",
    "ClinicalTrialsIngester",
    "FDADrugsIngester",
]

