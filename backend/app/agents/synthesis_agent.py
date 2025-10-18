"""Synthesis agent for combining and synthesizing results from all agents."""

import logging
from typing import Any, Dict, List, Optional

from app.agents.state import SynthesisInput, SynthesisOutput
from app.services.vertex_ai_service import get_vertex_ai_service

logger = logging.getLogger(__name__)


async def detect_conflicts(
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
    query: str,
) -> tuple[bool, str]:
    """
    Detect contradictory conclusions in top-k results.

    Args:
        research_results: Research results
        clinical_results: Clinical trial results
        drug_results: Drug information results
        query: Original query

    Returns:
        Tuple of (conflicts_detected, consensus_summary)
    """
    all_results = (research_results or [])[:5] + (clinical_results or [])[:3] + (drug_results or [])[:2]

    if len(all_results) < 2:
        return False, ""

    try:
        vertex_ai_service = get_vertex_ai_service()

        # Build conflict detection prompt
        prompt_parts = [
            f"Query: {query}\n\n",
            "Analyze the following research findings for contradictions or consensus:\n\n"
        ]

        for i, result in enumerate(all_results, 1):
            title = result.get("title", "")
            abstract = result.get("abstract", "")[:300]
            conclusion = result.get("conclusion", "")[:200]

            prompt_parts.append(f"[{i}] {title}\n")
            if abstract:
                prompt_parts.append(f"   Abstract: {abstract}...\n")
            if conclusion:
                prompt_parts.append(f"   Conclusion: {conclusion}...\n")
            prompt_parts.append("\n")

        prompt_parts.append(
            "\nAnalyze these findings and respond in JSON format:\n"
            '{"conflicts_detected": true/false, "consensus_summary": "brief summary"}\n\n'
            "Conflicts exist if studies reach opposite conclusions on the same question. "
            "Consensus exists if most studies agree. "
            "If conflicts exist, summarize both sides. If consensus, state the agreement."
        )

        response = await vertex_ai_service.generate_chat_response(
            prompt="".join(prompt_parts),
            system_instruction="You are a medical research analyst. Detect contradictions and consensus in research findings.",
            temperature=0.0,
            max_output_tokens=500,
        )

        # Parse JSON response
        import json
        import re

        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response)
        if json_match:
            result = json.loads(json_match.group())
            conflicts = result.get("conflicts_detected", False)
            summary = result.get("consensus_summary", "")
            return conflicts, summary

        return False, ""

    except Exception as e:
        logger.warning(f"Conflict detection failed: {e}")
        return False, ""


def calculate_confidence_score(
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
) -> float:
    """
    Calculate overall confidence score based on results.

    Args:
        research_results: Research results
        clinical_results: Clinical trial results
        drug_results: Drug information results

    Returns:
        Confidence score (0-1)
    """
    # Handle None values
    research_results = research_results or []
    clinical_results = clinical_results or []
    drug_results = drug_results or []

    total_results = len(research_results) + len(clinical_results) + len(drug_results)

    if total_results == 0:
        return 0.0

    # Base confidence on number and quality of results
    base_score = min(total_results / 10.0, 0.7)  # Max 0.7 from quantity

    # Add quality bonus from relevance scores
    all_scores = []
    for result in research_results + clinical_results + drug_results:
        score = result.get("relevance_score", 0.5)
        all_scores.append(score)

    if all_scores:
        avg_relevance = sum(all_scores) / len(all_scores)
        quality_bonus = avg_relevance * 0.3  # Max 0.3 from quality
    else:
        quality_bonus = 0.0

    final_score = min(base_score + quality_bonus, 1.0)

    return round(final_score, 2)


def get_confidence_band(confidence_score: float, result_count: int, recency_score: float = 0.5) -> str:
    """
    Derive confidence band from evidence count, agreement, and recency.

    Args:
        confidence_score: Overall confidence score (0-1)
        result_count: Number of supporting results
        recency_score: Recency score (0-1, where 1 is most recent)

    Returns:
        Confidence band: "Low", "Medium", or "High"
    """
    # Weighted score combining multiple factors
    weighted_score = (
        confidence_score * 0.5 +  # 50% from confidence
        min(result_count / 10.0, 1.0) * 0.3 +  # 30% from result count
        recency_score * 0.2  # 20% from recency
    )

    if weighted_score >= 0.7:
        return "High"
    elif weighted_score >= 0.4:
        return "Medium"
    else:
        return "Low"


def calculate_recency_score(results: List[Dict[str, Any]]) -> float:
    """
    Calculate recency score based on publication dates.

    Args:
        results: List of results with publication_date field

    Returns:
        Recency score (0-1)
    """
    from datetime import datetime

    if not results:
        return 0.5

    current_year = datetime.now().year
    recency_scores = []

    for result in results:
        pub_date = result.get("publication_date", "")
        if pub_date:
            try:
                # Extract year from various date formats
                if len(pub_date) >= 4:
                    year = int(pub_date[:4])
                    years_old = current_year - year
                    # Score: 1.0 for current year, decreasing by 0.1 per year
                    score = max(1.0 - (years_old * 0.1), 0.0)
                    recency_scores.append(score)
            except (ValueError, TypeError):
                continue

    if recency_scores:
        return sum(recency_scores) / len(recency_scores)
    return 0.5


def extract_citations(
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract and format citations from all results.

    Args:
        research_results: Research results
        clinical_results: Clinical trial results
        drug_results: Drug information results

    Returns:
        List of formatted citations
    """
    # Handle None values
    research_results = research_results or []
    clinical_results = clinical_results or []
    drug_results = drug_results or []

    citations = []

    # Add research citations
    for i, result in enumerate(research_results[:5], 1):
        citation = {
            "id": result.get("id", f"research_{i}"),
            "source_type": "pubmed",
            "title": result.get("title", ""),
            "authors": result.get("authors", []),
            "journal": result.get("journal", ""),
            "publication_date": result.get("publication_date", ""),
            "doi": result.get("doi", ""),
            "pmid": result.get("pmid", ""),
            "relevance_score": result.get("relevance_score", 0.5),
            "confidence_score": result.get("final_score", result.get("relevance_score", 0.5)),
        }
        citations.append(citation)

    # Add clinical trial citations
    for i, result in enumerate(clinical_results[:3], 1):
        citation = {
            "id": result.get("id", f"clinical_{i}"),
            "source_type": "clinical_trial",
            "title": result.get("title", ""),
            "nct_id": result.get("nct_id", ""),
            "phase": result.get("phase", ""),
            "status": result.get("status", ""),
            "relevance_score": result.get("relevance_score", 0.5),
            "confidence_score": result.get("final_score", result.get("relevance_score", 0.5)),
        }
        citations.append(citation)

    # Add drug citations
    for i, result in enumerate(drug_results[:3], 1):
        citation = {
            "id": result.get("id", f"drug_{i}"),
            "source_type": "fda_drug",
            "title": result.get("title", ""),
            "generic_name": result.get("generic_name", ""),
            "manufacturer": result.get("manufacturer", ""),
            "approval_date": result.get("approval_date", ""),
            "relevance_score": result.get("relevance_score", 0.5),
            "confidence_score": result.get("final_score", result.get("relevance_score", 0.5)),
        }
        citations.append(citation)

    return citations


async def synthesize_results(
    query: str,
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
    use_escalation: bool = False,
    conversation_history: List[Dict[str, str]] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> SynthesisOutput:
    """
    Synthesize results from all agents into a coherent response.

    Args:
        query: Original user query
        research_results: Results from research agent
        clinical_results: Results from clinical trials agent
        drug_results: Results from drug information agent
        use_escalation: Whether to use escalation model (Pro vs Flash)
        conversation_history: Previous Q&A pairs for context

    Returns:
        Synthesized response with citations and confidence score
    """
    logger.info("Synthesizing results from all agents...")

    # Handle conversation history
    conversation_history = conversation_history or []

    vertex_ai_service = get_vertex_ai_service()

    # Handle None values
    research_results = research_results or []
    clinical_results = clinical_results or []
    drug_results = drug_results or []

    # Check if we have any results
    total_results = len(research_results) + len(clinical_results) + len(drug_results)

    if total_results == 0:
        logger.warning("No results found from any agent")

        # Build context-aware no-results message
        context_msg = ""
        if conversation_history:
            context_msg = f"\n\nNote: This is a follow-up to our previous conversation about {conversation_history[-1].get('query', 'your earlier question')}."

        # Fetch live corpus sizes to avoid misleading '0' claims
        try:
            from app.services.elasticsearch_service import get_elasticsearch_service
            es_service = await get_elasticsearch_service()
            index_counts = await es_service.get_index_counts()
        except Exception:
            index_counts = {"pubmed": 0, "trials": 0, "drugs": 0}

        return SynthesisOutput(
            final_response=(
                f"I couldn't find results for this specific query: \"{query}\".{context_msg}\n\n"
                "This query returned 0 matches across sources.\n"
                f"Current corpus sizes — PubMed: {index_counts['pubmed']}, Clinical trials: {index_counts['trials']}, FDA drugs: {index_counts['drugs']}.\n\n"
                "Suggestions:\n"
                "- Try alternative medical terms (e.g., use the clinical name)\n"
                "- Break the question into smaller, focused parts\n"
                "- Ask about related topics that may have more literature\n"
                "- Start broader, then narrow down (use filters if needed)"
            ),
            citations=[],
            confidence_score=0.0,
            key_findings=[],
        )

    # Calculate confidence score
    confidence_score = calculate_confidence_score(
        research_results, clinical_results, drug_results
    )

    # Early relevance guardrail: if user asks for adverse effects (and optionally geriatrics)
    # but retrieved evidence does not contain clear safety content, return a helpful
    # "insufficient direct evidence" message instead of a generic answer.
    def _intent(q: str) -> dict:
        ql = q.lower()
        return {
            "side_effects": any(k in ql for k in ["side effect", "adverse", "reaction", "safety", "warning", "precaution"]),
            "geriatrics": any(k in ql for k in ["elder", "older", "geriatr", "65", "senior"]),
        }

    user_intent = _intent(query)

    def _coverage() -> int:
        tokens = ["adverse", "side effect", "warning", "precaution", "geriat", "elder", "older", "65"]
        text_chunks: List[str] = []
        for r in (drug_results or [])[:5]:
            text_chunks.append(r.get("adverse_reactions", ""))
            text_chunks.append(r.get("warnings", ""))
            text_chunks.append(r.get("indications", ""))
        for r in (research_results or [])[:3]:
            text_chunks.append(r.get("abstract", ""))
        aggregate = " \n".join([t for t in text_chunks if t])[:4000]
        score = sum(1 for t in tokens if t in aggregate.lower())
        return score

    if user_intent.get("side_effects") and _coverage() < 2:
        # Build a structured, honest response using whatever we have
        general_adverse = []
        for r in (drug_results or [])[:3]:
            if r.get("adverse_reactions"):
                general_adverse.append(r.get("adverse_reactions")[:200])
        general_text = " ".join(general_adverse)[:400]
        tips = (
            "I couldn’t find drug label sections that directly discuss side effects in older adults for this query. "
            "Here’s what I can provide based on available safety text, and how you can refine the search:"
        )
        suggestion_lines = [
            "Use terms like ‘geriatric use’, ‘older adults’, or ‘65 years’ with the drug name",
            "Ask specifically for ‘adverse reactions’ or ‘warnings’",
            "Include a condition or context (e.g., renal impairment) if relevant",
        ]
        advisory = (
            f"{tips}\n\n"
            + (f"General adverse reaction notes (not specific to older adults): {general_text}\n\n" if general_text else "")
            + "Suggestions to refine: \n- " + "\n- ".join(suggestion_lines)
        )
        citations = extract_citations(research_results, clinical_results, drug_results)
        return SynthesisOutput(
            final_response=advisory + "\n\n⚕ Medical Disclaimer: Educational only; not medical advice.",
            citations=citations,
            confidence_score=max(confidence_score - 0.2, 0.0),
            confidence_band="Low",
            key_findings=[],
            conflicts_detected=False,
        )

    # Calculate recency score
    all_results = research_results + clinical_results + drug_results
    recency_score = calculate_recency_score(all_results)

    # Get confidence band
    confidence_band = get_confidence_band(confidence_score, total_results, recency_score)

    # Detect conflicts
    conflicts_detected, consensus_summary = await detect_conflicts(
        research_results, clinical_results, drug_results, query
    )

    # Extract citations
    citations = extract_citations(research_results, clinical_results, drug_results)

    # Build synthesis prompt
    prompt = _build_synthesis_prompt(
        query, research_results, clinical_results, drug_results, conflicts_detected, consensus_summary, filters
    )

    try:
        # Build context from conversation history
        context_section = ""
        if conversation_history:
            context_section = "\n\nCONVERSATION CONTEXT:\n"
            for i, conv in enumerate(conversation_history[-3:], 1):  # Last 3 exchanges
                context_section += f"Previous Q{i}: {conv.get('query', '')}\n"
                context_section += f"Previous A{i}: {conv.get('response', '')[:200]}...\n\n"
            context_section += f"Current question is a follow-up. Use this context to provide a coherent response.\n"

        # Generate synthesis using Vertex AI
        final_response = await vertex_ai_service.generate_chat_response(
            prompt=prompt + context_section,
            system_instruction=f"""You are an intelligent medical research assistant. Answer this specific question: "{query}"

INTELLIGENCE GUIDELINES:
1. **Be Specific**: Answer the EXACT question asked, not generic information
2. **Handle Partial Data Intelligently**:
   - If you have SOME relevant data, provide it and clearly state what's missing
   - Example: "While I found information about X [1,2], I don't have specific data about Y in the current research"
   - Offer related information that might be helpful
3. **Cite Sources**: Use [1], [2], etc. for all factual claims
4. **Be Honest About Limitations**:
   - If no direct answer exists, say: "The available research doesn't directly address [specific aspect], but here's related information..."
   - If data is limited, say: "Based on limited available research [1,2]..."
   - If results are preliminary, mention: "Early research suggests [1], but more studies are needed"
5. **Use Conversation Context**: If this is a follow-up question, reference previous discussion naturally
6. **Provide Actionable Insights**:
   - Summarize key findings
   - Note consensus vs. conflicting evidence
   - Highlight gaps in current research
7. **Professional Tone**: Clear, concise (2-4 paragraphs), no medical advice
8. **Avoid Repetition**: Each response should be unique and tailored to the specific query

Remember: It's better to provide partial, accurate information with clear limitations than to give generic or irrelevant responses.""",
            temperature=0.6,
            max_output_tokens=2048,
            use_escalation=use_escalation,
        )

        # Extract key findings
        key_findings = _extract_key_findings(final_response)

        return SynthesisOutput(
            final_response=final_response.strip(),
            citations=citations,
            confidence_score=confidence_score,
            confidence_band=confidence_band,
            key_findings=key_findings,
            conflicts_detected=conflicts_detected,
            consensus_summary=consensus_summary if conflicts_detected else None,
        )

    except Exception as e:
        logger.error(f"Error in synthesis: {e}")

        # Fallback to simple concatenation
        fallback_response = _generate_fallback_response(
            query, research_results, clinical_results, drug_results
        )

        return SynthesisOutput(
            final_response=fallback_response,
            citations=citations,
            confidence_score=max(confidence_score - 0.2, 0.0),
            confidence_band="Low",
            key_findings=[],
            conflicts_detected=False,
        )


def _build_synthesis_prompt(
    query: str,
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
    conflicts_detected: bool = False,
    consensus_summary: str = "",
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """Build the synthesis prompt for Vertex AI."""
    prompt_parts = [f"Query: {query}\n\n"]

    # Add filter information if present
    if filters:
        prompt_parts.append("🔍 Applied Filters:\n")
        if "year_range" in filters:
            year_range = filters["year_range"]
            start = year_range.get("start", "")
            end = year_range.get("end", "")
            if start or end:
                prompt_parts.append(f"  - Year range: {start or 'any'} to {end or 'current'}\n")
        if "study_types" in filters and filters["study_types"]:
            prompt_parts.append(f"  - Study types: {', '.join(filters['study_types'])}\n")
        if "sources" in filters and filters["sources"]:
            prompt_parts.append(f"  - Sources: {', '.join(filters['sources'])}\n")
        prompt_parts.append("\nNOTE: All results below have been filtered according to these criteria.\n\n")

    # Add conflict/consensus information if detected
    if conflicts_detected and consensus_summary:
        prompt_parts.append("⚠️ IMPORTANT - Contradictory Evidence Detected:\n")
        prompt_parts.append(f"{consensus_summary}\n\n")
        prompt_parts.append("Please address both perspectives in your synthesis and explain the contradictions.\n\n")

    # Add research findings
    if research_results:
        prompt_parts.append("Research Findings (PubMed):\n")
        for i, result in enumerate(research_results[:5], 1):
            prompt_parts.append(f"[{i}] {result.get('title', '')}\n")
            abstract = result.get("abstract", "")[:300]
            pub_date = result.get("publication_date", "")
            prompt_parts.append(f"   Published: {pub_date}\n")
            prompt_parts.append(f"   {abstract}...\n\n")

    # Add clinical trial findings
    if clinical_results:
        prompt_parts.append("Clinical Trials:\n")
        for i, result in enumerate(clinical_results[:3], len(research_results[:5]) + 1):
            prompt_parts.append(f"[{i}] {result.get('title', '')}\n")
            prompt_parts.append(f"   Phase: {result.get('phase', 'Unknown')}\n")
            prompt_parts.append(f"   Status: {result.get('status', 'Unknown')}\n\n")

    # Add drug information
    if drug_results:
        prompt_parts.append("Drug Information:\n")
        for i, result in enumerate(
            drug_results[:3], len(research_results[:5]) + len(clinical_results[:3]) + 1
        ):
            prompt_parts.append(f"[{i}] {result.get('title', '')} ({result.get('generic_name', '')})\n")
            indications = result.get("indications", "")[:200]
            prompt_parts.append(f"   Indications: {indications}...\n\n")

    prompt_parts.append(
        "\nSynthesize these findings into a comprehensive response to the query. "
        "CRITICAL: Use citation numbers [1], [2], etc. for EVERY factual claim. "
        "No claim should appear without at least one citation."
    )

    if conflicts_detected:
        prompt_parts.append(
            "\n\nIMPORTANT: Address the contradictory evidence noted above. "
            "Present both perspectives fairly and explain possible reasons for the discrepancy."
        )

    return "".join(prompt_parts)


def _generate_fallback_response(
    query: str,
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
) -> str:
    """Generate a fallback response if synthesis fails."""
    response_parts = [f"Based on the available research for '{query}':\n\n"]

    if research_results:
        response_parts.append(f"Found {len(research_results)} relevant research articles:\n")
        for i, result in enumerate(research_results[:3], 1):
            response_parts.append(f"{i}. {result.get('title', '')}\n")

    if clinical_results:
        response_parts.append(f"\nFound {len(clinical_results)} relevant clinical trials:\n")
        for i, result in enumerate(clinical_results[:3], 1):
            response_parts.append(
                f"{i}. {result.get('title', '')} (Phase: {result.get('phase', 'Unknown')})\n"
            )

    if drug_results:
        response_parts.append(f"\nFound {len(drug_results)} relevant drugs:\n")
        for i, result in enumerate(drug_results[:3], 1):
            response_parts.append(f"{i}. {result.get('title', '')} ({result.get('generic_name', '')})\n")

    if not (research_results or clinical_results or drug_results):
        response_parts.append("No relevant results found. Please try refining your query.")

    return "".join(response_parts)


def _extract_key_findings(response: str) -> List[str]:
    """Extract key findings from the synthesized response."""
    # Simple extraction: split by paragraphs and take first sentence of each
    paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]

    key_findings = []
    for para in paragraphs[:3]:  # Max 3 key findings
        # Get first sentence
        sentences = para.split(". ")
        if sentences:
            key_findings.append(sentences[0] + ".")

    return key_findings

