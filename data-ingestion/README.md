# MedSearch AI - Data Ingestion Pipeline

This directory contains the data ingestion pipeline for populating Elasticsearch with medical research data from PubMed, ClinicalTrials.gov, and FDA databases.

## Overview

The pipeline fetches data from three sources:
1. **PubMed**: Research articles via E-utilities API
2. **ClinicalTrials.gov**: Clinical trials via REST API v2
3. **FDA Drugs**: Drug information via openFDA API

All data is enriched with semantic embeddings using Vertex AI for hybrid search.

## Components

### 1. Embedding Generator (`embeddings_generator.py`)

Generates 768-dimensional embeddings using Vertex AI's `text-embedding-004` model.

**Features:**
- Batch processing (5 texts per batch)
- Automatic text truncation (20,000 chars max)
- Rate limiting between batches
- Error handling with zero-vector fallback

**Usage:**
```python
from embeddings_generator import get_embedding_generator

generator = get_embedding_generator()
generator.initialize()

# Single embedding
embedding = generator.generate_embedding_sync("Diabetes treatment")

# Batch embeddings
embeddings = generator.generate_embeddings_batch_sync([
    "Text 1",
    "Text 2",
    "Text 3"
])
```

### 2. PubMed Ingester (`pubmed_ingester.py`)

Fetches research articles from PubMed using E-utilities API.

**Features:**
- Search by query terms
- XML parsing for article metadata
- Extracts: title, abstract, authors, journal, DOI, PMID, MeSH terms
- Rate limiting (3 req/sec with API key)
- Batch processing (100 articles per batch)

**Target:** 1000+ articles

### 3. Clinical Trials Ingester (`clinical_trials_ingester.py`)

Fetches clinical trials from ClinicalTrials.gov API v2.

**Features:**
- Pagination support
- Extracts: NCT ID, title, phase, status, conditions, interventions, locations
- Enrollment and sponsor information
- Rate limiting (1 req/sec)
- Batch processing (50 trials per batch)

**Target:** 500+ trials

### 4. FDA Drugs Ingester (`fda_drugs_ingester.py`)

Fetches drug information from openFDA API.

**Features:**
- Drug labels endpoint
- Extracts: drug name, generic name, manufacturer, indications, warnings, adverse reactions
- Drug interactions and dosage information
- Rate limiting (4 req/sec)
- Batch processing (20 drugs per batch)

**Target:** 200+ drugs

### 5. Main Orchestrator (`main.py`)

Coordinates the entire ingestion process.

**Features:**
- Creates Elasticsearch indices with proper mappings
- Runs all ingesters sequentially
- Provides progress tracking and statistics
- Success criteria validation

## Setup

### 1. Install Dependencies

```bash
cd data-ingestion
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# API Keys
PUBMED_API_KEY=your_pubmed_api_key
FDA_API_KEY=your_fda_api_key

# Google Cloud
GOOGLE_CLOUD_PROJECT=medsearch-ai
GOOGLE_APPLICATION_CREDENTIALS=../medsearch-key.json

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=changeme
```

### 3. Start Elasticsearch

Make sure Elasticsearch is running:

```bash
# Using Docker Compose (from project root)
docker-compose up -d elasticsearch

# Or standalone Docker
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.15.1
```

## Usage

### Run Full Ingestion

```bash
python main.py
```

This will:
1. Create Elasticsearch indices
2. Ingest 1000 PubMed articles
3. Ingest 500 clinical trials
4. Ingest 200 FDA drugs
5. Generate embeddings for all data
6. Print statistics

### Run Individual Ingesters

```python
import asyncio
from elasticsearch import AsyncElasticsearch
from embeddings_generator import get_embedding_generator
from pubmed_ingester import PubMedIngester

async def ingest_pubmed():
    es_client = AsyncElasticsearch(["http://localhost:9200"])
    embedding_gen = get_embedding_generator()
    embedding_gen.initialize()
    
    ingester = PubMedIngester(
        api_key="your_api_key",
        es_client=es_client,
        embedding_generator=embedding_gen
    )
    
    stats = await ingester.ingest(
        query="diabetes treatment",
        max_articles=100
    )
    
    print(stats)
    await es_client.close()

asyncio.run(ingest_pubmed())
```

## Elasticsearch Index Mappings

### PubMed Index (`medsearch-pubmed`)

```json
{
  "pmid": "keyword",
  "title": "text",
  "abstract": "text",
  "authors": "keyword",
  "journal": "keyword",
  "publication_date": "date",
  "doi": "keyword",
  "mesh_terms": "keyword",
  "keywords": "keyword",
  "embedding": "dense_vector (768 dims, cosine similarity)",
  "indexed_at": "date"
}
```

### Clinical Trials Index (`medsearch-trials`)

```json
{
  "nct_id": "keyword",
  "title": "text",
  "brief_summary": "text",
  "detailed_description": "text",
  "status": "keyword",
  "phase": "keyword",
  "conditions": "keyword",
  "interventions": "keyword",
  "locations": "keyword",
  "sponsors": "keyword",
  "start_date": "date",
  "completion_date": "date",
  "enrollment": "integer",
  "embedding": "dense_vector (768 dims, cosine similarity)",
  "indexed_at": "date"
}
```

### FDA Drugs Index (`medsearch-drugs`)

```json
{
  "id": "keyword",
  "drug_name": "text",
  "generic_name": "text",
  "brand_names": "keyword",
  "manufacturer": "keyword",
  "application_number": "keyword",
  "drug_class": "text",
  "route": "keyword",
  "indications": "text",
  "warnings": "text",
  "adverse_reactions": "text",
  "dosage": "text",
  "interactions": "text",
  "approval_date": "date",
  "embedding": "dense_vector (768 dims, cosine similarity)",
  "indexed_at": "date"
}
```

## Rate Limits

| Source | Rate Limit | Implementation |
|--------|-----------|----------------|
| PubMed | 3 req/sec (with API key) | 0.34s delay |
| ClinicalTrials.gov | No official limit | 1s delay (respectful) |
| FDA | 4 req/sec | 0.25s delay |
| Vertex AI | No strict limit | 0.5s between batches |

## Success Criteria

- ✅ Ingest 1000+ PubMed articles
- ✅ Index 500+ clinical trials
- ✅ Load 200+ FDA drugs
- ✅ All data includes semantic embeddings
- ✅ Pipeline handles API failures gracefully

## Error Handling

All ingesters include:
- Try-catch blocks for API calls
- Retry logic for transient failures
- Error statistics tracking
- Graceful degradation (zero vectors for failed embeddings)
- Detailed logging

## Performance

Estimated ingestion times:
- **PubMed** (1000 articles): ~15-20 minutes
- **Clinical Trials** (500 trials): ~10-15 minutes
- **FDA Drugs** (200 drugs): ~5-10 minutes

**Total:** ~30-45 minutes for full ingestion

## Monitoring

The pipeline logs:
- Progress updates (every batch)
- API errors and retries
- Embedding generation status
- Final statistics

Example output:
```
INFO: Starting PubMed ingestion for query: diabetes treatment
INFO: Target: 1000 articles
INFO: Found 1000 article IDs
INFO: Progress: 100/1000 articles
INFO: Indexed 100 articles
...
INFO: Ingestion complete: {'fetched': 1000, 'indexed': 1000, 'errors': 0}
```

## Troubleshooting

### Elasticsearch Connection Error

```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# Check Docker container
docker ps | grep elasticsearch
```

### Vertex AI Authentication Error

```bash
# Verify service account key
export GOOGLE_APPLICATION_CREDENTIALS=../medsearch-key.json
gcloud auth application-default print-access-token
```

### API Rate Limit Exceeded

- Increase `rate_limit` parameter in ingesters
- Reduce `batch_size` for processing
- Use API keys for higher limits

## Next Steps

After successful ingestion:
1. Verify data in Elasticsearch
2. Test hybrid search queries
3. Run backend API tests
4. Deploy to production

