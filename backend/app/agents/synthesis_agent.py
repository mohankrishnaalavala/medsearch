"""Synthesis agent for combining and synthesizing results from all agents."""

import logging
from typing import Any, Dict, List

from app.agents.state import SynthesisInput, SynthesisOutput
from app.services.vertex_ai_service import get_vertex_ai_service

logger = logging.getLogger(__name__)


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

        return SynthesisOutput(
            final_response=f"I apologize, but I couldn't find any relevant information in the medical databases for your query: \"{query}\".{context_msg}\n\nThis could be because:\n\n1. **Emerging or highly specific topic** - The research may not yet be indexed in our databases\n2. **Different terminology** - Medical terms vary; try alternative phrasing\n3. **Limited scope** - Our database contains {len(research_results)} PubMed articles, {len(clinical_results)} clinical trials, and {len(drug_results)} FDA drug entries\n\nSuggestions:\n- Rephrase using different medical terms\n- Break complex questions into simpler parts\n- Ask about related topics that might have more research\n- Try broader search terms first, then narrow down",
            citations=[],
            confidence_score=0.0,
            key_findings=[],
        )

    # Calculate confidence score
    confidence_score = calculate_confidence_score(
        research_results, clinical_results, drug_results
    )

    # Extract citations
    citations = extract_citations(research_results, clinical_results, drug_results)

    # Build synthesis prompt
    prompt = _build_synthesis_prompt(
        query, research_results, clinical_results, drug_results
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
            key_findings=key_findings,
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
            key_findings=[],
        )


def _build_synthesis_prompt(
    query: str,
    research_results: List[Dict[str, Any]],
    clinical_results: List[Dict[str, Any]],
    drug_results: List[Dict[str, Any]],
) -> str:
    """Build the synthesis prompt for Vertex AI."""
    prompt_parts = [f"Query: {query}\n\n"]

    # Add research findings
    if research_results:
        prompt_parts.append("Research Findings (PubMed):\n")
        for i, result in enumerate(research_results[:5], 1):
            prompt_parts.append(f"[{i}] {result.get('title', '')}\n")
            abstract = result.get("abstract", "")[:300]
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
        "Use citation numbers [1], [2], etc. to reference sources."
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

