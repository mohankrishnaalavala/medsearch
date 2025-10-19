# MedSearch AI - 3-Minute Demo Script

## Introduction (30 seconds)

"Hi, I'm [Your Name], and I'm excited to show you MedSearch AI - an intelligent medical research assistant that transforms 20 hours of research into 20 seconds of conversation.

Healthcare professionals today waste 15 to 20 hours per topic manually searching through over 1.5 million medical publications published every year. They have to jump between PubMed for research papers, ClinicalTrials.gov for ongoing trials, and FDA databases for drug information. Traditional keyword search misses semantically related content, and verifying citations is tedious and error-prone.

MedSearch AI solves this problem using a multi-agent system powered by Elasticsearch and Google Cloud Vertex AI."

## Live Demo - Part 1: Basic Search (45 seconds)

"Let me show you how it works. I'm going to log into our live application at medsearch.mohankrishna.site.

[Navigate to the site and log in with demo credentials]

Now, let's ask a real medical question: 'What are the latest treatments for Type 2 diabetes in elderly patients?'

[Type the query and submit]

Watch what happens. You can see our system is working in real-time:

- First, the Query Analyzer understands the medical intent
- Then, three specialized agents work in parallel:
  - The Research Agent searches PubMed for scientific papers
  - The Clinical Trials Agent searches ClinicalTrials.gov for ongoing trials
  - The Drug Information Agent searches FDA databases for approved medications

Notice how results are streaming in real-time. This isn't just a loading spinner - you're seeing actual progress as each agent finds and analyzes information.

Within 3 seconds, we have a comprehensive answer with citations from all three sources."

## Live Demo - Part 2: Citation Verification (30 seconds)

"Now, here's what makes this powerful - every single claim in this answer is backed by verifiable sources.

[Click to expand citations]

See these citations? Each one includes:
- The exact title of the research paper or trial
- The journal name or trial phase
- Publication date or trial status
- Direct links to the original sources

This means healthcare professionals can verify every piece of information instantly. No more hunting through dozens of tabs to find where information came from."

## Technical Deep Dive (45 seconds)

"Let me quickly explain the technology that makes this possible.

We use Elasticsearch's hybrid search, which combines two powerful techniques:
- BM25 for keyword precision - finding exact medical terms
- Vector search for semantic understanding - finding related concepts even if they use different terminology

For example, if you search for 'heart attack,' our system also finds papers about 'myocardial infarction' because it understands they're the same concept.

We enhanced this with Google Vertex AI in three ways:

First, we use Gemini embeddings to create those semantic vectors - turning medical text into mathematical representations that capture meaning.

Second, we implemented AI-powered reranking. After Elasticsearch returns results, Gemini models score them for relevance to your specific question, ensuring the most important information rises to the top.

Third, Gemini Flash synthesizes all the findings into a coherent answer, detecting conflicts between studies and highlighting the most current evidence."

## Live Demo - Part 3: Conversation Context (30 seconds)

"One more powerful feature - conversation memory.

[Ask a follow-up question like: 'What are the side effects of metformin in this population?']

Notice I didn't have to repeat 'elderly patients with Type 2 diabetes' - the system remembers our conversation context. This lets healthcare professionals have a natural dialogue, drilling deeper into topics without starting over each time.

And again, within seconds, we have a comprehensive answer with citations specific to elderly patients."

## Production Features (30 seconds)

"This isn't just a prototype - it's production-ready and deployed on Google Cloud.

We built in enterprise-grade features:
- Elastic APM monitors every transaction, so we can track performance and catch errors before they impact users
- Redis caching reduces response times and API costs by storing frequently asked queries
- Graceful degradation means even if a service goes down, users still get answers from cached or fallback data
- HTTPS and WebSocket security through Nginx with Let's Encrypt SSL

The entire system runs on a single Google Compute Engine VM with Docker containers, making it cost-effective and easy to scale."

## Closing & Impact (30 seconds)

"So, to recap what you just saw:

MedSearch AI takes a question that would normally require 15 to 20 hours of manual research across multiple databases and delivers a comprehensive, citation-backed answer in under 3 seconds.

The impact is significant:
- Healthcare professionals make faster, better-informed decisions
- Researchers discover connections across studies they might have missed
- Patients benefit from doctors who have access to the latest evidence

We achieved 95% citation accuracy, sub-3-second response times, and a system that's resilient, scalable, and ready for real-world use.

This is what's possible when you combine Elasticsearch's powerful search capabilities with Google Cloud's AI and infrastructure.

Thank you, and I'm happy to answer any questions!"

---

## Demo Tips

### Before You Start
1. Have the live site open in a browser tab
2. Be logged in with demo credentials
3. Clear any previous conversation history
4. Test your internet connection
5. Have backup queries ready in case of issues

### Backup Queries (if primary fails)
- "What is Dapagliflozin in Heart Failure with Preserved Ejection Fraction?"
- "Metformin side effects in elderly patients"
- "Latest clinical trials for Alzheimer's disease"
- "SGLT2 inhibitors for chronic kidney disease"

### Timing Breakdown
- Introduction: 30 seconds
- First demo (basic search): 45 seconds
- Citation verification: 30 seconds
- Technical explanation: 45 seconds
- Follow-up question: 30 seconds
- Production features: 30 seconds
- Closing: 30 seconds
- **Total: 3 minutes 30 seconds** (leaves 30 seconds buffer for transitions)

### What to Emphasize
1. **Speed**: "20 hours to 20 seconds" - repeat this
2. **Accuracy**: "95% citation accuracy" - show the citations
3. **Real-time**: Point out the streaming updates
4. **Production-ready**: Not just a demo, it's deployed and working
5. **Elastic + Google Cloud**: Mention both platforms throughout

### Common Questions & Answers

**Q: How much data is indexed?**
A: Currently 1,000+ PubMed articles, 500+ clinical trials, and 200+ FDA drugs. The architecture scales to millions with automated ingestion.

**Q: What's the cost to run this?**
A: About $50-100/month on Google Cloud for the VM, plus Vertex AI API costs which are minimal due to caching.

**Q: Can it handle medical specialties?**
A: Yes, the hybrid search works across all medical domains. We've tested cardiology, endocrinology, neurology, and oncology.

**Q: How do you ensure accuracy?**
A: Every claim is backed by citations. We don't generate unsupported information - if there's no evidence, we say so.

**Q: What about privacy/HIPAA?**
A: This is a research tool, not a patient data system. No PHI is stored or processed. For clinical use, we'd add HIPAA compliance.

### Troubleshooting During Demo

**If the site is slow:**
"You can see this is a live production system, so response times vary with load. Normally this is under 3 seconds."

**If a query fails:**
"Let me try a different query - this shows our error handling in action. In production, we have fallback mechanisms."

**If citations don't load:**
"The citations are there in the backend - this is a UI rendering issue. Let me refresh and show you."

### Body Language & Delivery
- Speak clearly and at a moderate pace
- Make eye contact with judges/camera
- Use hand gestures to emphasize key points
- Smile and show enthusiasm for the project
- Pause briefly after showing results to let them sink in
- Point to specific parts of the screen when explaining features

### Key Phrases to Use
- "Real-time streaming" (not "loading")
- "Citation-backed" (not "referenced")
- "Multi-agent orchestration" (shows technical depth)
- "Hybrid search" (Elasticsearch feature)
- "Semantic understanding" (AI capability)
- "Production-ready" (not just a prototype)
- "Graceful degradation" (resilience)

Good luck with your demo! 🚀

