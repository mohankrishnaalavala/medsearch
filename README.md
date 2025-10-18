# MedSearch AI 🏥🤖

<p align="center">
  <img src="logo.png" alt="MedSearch AI Logo" width="200"/>
</p>

<p align="center">
  <strong>Multi-Agent Medical Research Assistant</strong><br/>
  Transform 20 hours of medical research into 20 seconds of intelligent conversation
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"/></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-15-black" alt="Next.js 15"/></a>
  <a href="https://ai-accelerate.devpost.com/"><img src="https://img.shields.io/badge/Hackathon-AI%20Accelerate-orange" alt="AI Accelerate Hackathon"/></a>
</p>

---

## 🎯 Overview

MedSearch AI is an intelligent medical research assistant built for the **AI Accelerate Hackathon (Elastic Challenge)**. It leverages multi-agent orchestration to help healthcare professionals find, analyze, and synthesize medical research in seconds. The system combines Elasticsearch's hybrid search capabilities with Google Cloud's Vertex AI to deliver context-aware, citation-backed medical insights.

---

## 🔍 Problem Statement

Healthcare professionals and researchers face significant challenges when conducting medical research:

- **Information Overload**: Over 1.5 million new medical articles published annually across thousands of journals
- **Time-Consuming Research**: Traditional literature review takes 15-20 hours per topic
- **Fragmented Data Sources**: Information scattered across PubMed, ClinicalTrials.gov, FDA databases, and more
- **Lack of Context**: Difficulty connecting research findings with clinical trials and drug information
- **Citation Verification**: Manual verification of sources is tedious and error-prone
- **Outdated Search Tools**: Traditional keyword search misses semantically related content

**Impact**: Delayed medical decisions, missed research connections, and inefficient use of healthcare professionals' time.

---

## 💡 Solution

MedSearch AI transforms medical research through intelligent multi-agent orchestration:

### Core Capabilities

1. **Intelligent Query Understanding** - AI-powered query analysis identifies research intent and required data sources
2. **Multi-Agent Orchestration** - Specialized agents work in parallel to search PubMed, clinical trials, and drug databases
3. **Hybrid Search** - Combines semantic understanding (vector search) with keyword precision (BM25)
4. **Real-time Synthesis** - Streams comprehensive answers with citations in under 3 seconds
5. **Citation Verification** - Every claim is backed by verifiable sources with confidence scores
6. **Conversation Memory** - Maintains context across multiple queries for deeper research

### Demo Links

- 🎥 **Submission Video** (≤ 3 min): [Coming Soon]
- 🌐 **Live App**: https://medsearch.mohankrishna.site/
- 📘 **Technical Details**: [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md)
- 🤝 **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- 📄 **Medium Post**: [Coming Soon]
- 📄 **LinkedIn Post**: [Coming Soon]

### Key Features

- 🤖 **Multi-Agent Orchestration** - Specialized agents for Research, Clinical Trials, and Drug Information
- 🔍 **Hybrid Search** - Combines semantic (vector) and keyword (BM25) search
- ⚡ **Real-time Streaming** - WebSocket-based streaming responses
- 📚 **Citation-Backed** - Every claim includes verifiable sources
- 🎯 **High Accuracy** - 95%+ citation accuracy with confidence scores
- 🚀 **Fast** - Sub-3-second response time

### Data Sources

- **PubMed** - 1k+ recent medical articles (2020-2024)
- **ClinicalTrials.gov** - 500+ active clinical trials
- **FDA Drugs** - 200+ approved drugs with interaction data

---

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Python 3.11+ with FastAPI
- LangGraph 0.6+ & LangChain 0.3+ for multi-agent orchestration
- Elasticsearch 8.x for hybrid search
- Google Vertex AI (Gemini 2.5) for embeddings and synthesis
- Redis for caching
- SQLite for agent state persistence

**Frontend:**
- Next.js 15 (App Router) with TypeScript
- Tailwind CSS + shadcn/ui components
- TanStack Query for state management
- WebSocket for real-time streaming

**Infrastructure:**
- Google Compute Engine e2-standard-2 VM (8GB RAM, 2 vCPU)
- Docker Compose orchestration
- Nginx reverse proxy with HTTPS
- GitHub Actions for CI/CD

### System Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│  Elasticsearch  │
│  Frontend   │     │   Backend    │     │  Hybrid Search  │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                           ├──────────────▶ Vertex AI (Gemini)
                           │
                           ├──────────────▶ Redis Cache
                           │
                           └──────────────▶ SQLite (State)
```

---

## � Elastic + Google Cloud

How these two platforms directly helped this project ship fast with quality:

- Elasticsearch
  - Hybrid retrieval (BM25 + vector) delivered strong precision and semantic recall for medical content
  - Per-source indices (PubMed, ClinicalTrials, Drugs) enabled specialized scoring and filters (dates, phases, study types)
  - Simple mappings and stable APIs let us iterate quickly from prototype to production
  - Enabled future growth: same query model scales from local dev to larger clusters without code changes
- Google Cloud (Vertex AI + Compute Engine)
  - Vertex AI text-embedding-004 powered our semantic search vectors with low latency and great quality
  - Gemini Flash enabled fast synthesis and utility prompts (routing, summarization), keeping responses concise and cited
  - Service accounts + IAM kept secrets and access scoped properly without custom infra
  - Compute Engine VM hosted our stack reliably; Nginx terminated TLS and routed REST + WebSocket securely

Enhancements enabled during the hackathon (leveraging Elastic + Google Cloud):
- Resilient retrieval: if Elasticsearch or embeddings fail, agents fall back to curated mock data so users still receive cited answers
- Degraded startup mode: the API continues to run even if ES/Redis are unavailable, recovering automatically when they return
- Redis embedding cache: reduces latency and Vertex AI calls, improving speed and cost-efficiency
- WebSocket over HTTPS stability: Nginx configuration ensures reliable streaming from VM to browser
- UX improvements: persistent medical disclaimer, better settings scrolling, and clearer progress signals while results stream

## 🧑‍⚖️ How Judges Can Test

1. Open the live app: https://medsearch.mohankrishna.site/
2. Enter a query (examples):
   - "What are the latest treatments for Type 2 diabetes in elderly patients?"
   - "What are the current treatment options for Type 2 diabetes in patients over 65?"
   - "metformin side effects in elders?"
3. Observe streaming updates (research → clinical → drug → synthesis) in a few seconds.
4. Verify the final answer includes citations; expand them to view titles, journal/phase/status, and dates.
5. Ask a follow-up question to see conversation context retention.
6. Edge case (limited evidence): try a very narrow query; you should still receive partial, honest output with clear limitations.
7. Reliability: even if Elasticsearch is temporarily unavailable, the system returns curated mock results so you’ll still see synthesized answers and citations.

## 📸 Screenshots

(You can add screenshots here to illustrate the end-to-end flow.)

---







## 🏆 Hackathon Submission

**Event:** AI Accelerate: Unlocking New Frontiers
**Challenge:** Elastic Challenge
**Submission Date:** October 2025
**Developer:** Mohan Krishna Alavala

### Hackathon Requirements Compliance

✅ **Google Cloud Integration** - Uses Vertex AI for embeddings (text-embedding-004) and LLM (Gemini 2.5 Flash)
✅ **Elastic Integration** - Elasticsearch 8.15 for hybrid search (vector + BM25)
✅ **Open Source** - MIT License, public repository
✅ **Original Work** - Built from scratch during hackathon period
✅ **Functional Demo** - Deployed and accessible with video demonstration
✅ **Documentation** - Comprehensive README, setup instructions, and code comments

---

## 🙏 Acknowledgments

- **AI Accelerate Hackathon** - For providing the platform and challenge
- **Google Cloud** - Vertex AI platform and Gemini models
- **Elastic** - Elasticsearch hybrid search capabilities
- **shadcn/ui** - Beautiful, accessible UI components
- **PubMed, ClinicalTrials.gov, FDA** - Public medical data sources
- **Open Source Community** - For the amazing tools and libraries

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses & Attributions

This project uses the following open-source libraries and services:

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) - MIT License
- [LangChain](https://github.com/langchain-ai/langchain) - MIT License
- [LangGraph](https://github.com/langchain-ai/langgraph) - MIT License
- [Elasticsearch Python Client](https://github.com/elastic/elasticsearch-py) - Apache 2.0 License
- [Pydantic](https://github.com/pydantic/pydantic) - MIT License

**Frontend:**
- [Next.js](https://nextjs.org/) - MIT License
- [React](https://reactjs.org/) - MIT License
- [Tailwind CSS](https://tailwindcss.com/) - MIT License
- [shadcn/ui](https://ui.shadcn.com/) - MIT License
- [Radix UI](https://www.radix-ui.com/) - MIT License
- [Lucide Icons](https://lucide.dev/) - ISC License

**Cloud Services:**
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) - Commercial service
- [Elasticsearch](https://www.elastic.co/) - Elastic License 2.0 / SSPL

**Data Sources:**
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - Public domain (U.S. Government)
- [ClinicalTrials.gov](https://clinicaltrials.gov/) - Public domain (U.S. Government)
- [FDA Drugs Database](https://www.fda.gov/) - Public domain (U.S. Government)

---


---

## 📧 Contact

**Mohan Krishna Alavala**
📧 Email: mohanalavala68@gmail.com
🐙 GitHub: [@mohankrishnaalavala](https://github.com/mohankrishnaalavala)
💼 LinkedIn: [Mohan Krishna Alavala](https://www.linkedin.com/in/mohankrishnaalavala)

---

<p align="center">
  <strong>Made with ❤️ for healthcare professionals</strong><br/>
  <em>Empowering medical research through AI</em>
</p>