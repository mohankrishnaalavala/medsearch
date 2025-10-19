"""Safety and guardrails for medical search."""

import hashlib
import logging
import re
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Medical disclaimer
MEDICAL_DISCLAIMER = (
    "⚕️ **Medical Disclaimer**: This information is for educational purposes only and is not medical advice. "
    "Always consult with a qualified healthcare professional for medical decisions, diagnosis, or treatment."
)

# Patterns for unsafe content
UNSAFE_PATTERNS = [
    # Self-harm and suicide
    r'\b(kill\s+myself|suicide|end\s+my\s+life|self\s*harm)\b',
    # Illegal drug manufacturing
    r'\b(make|manufacture|synthesize|cook)\s+(meth|cocaine|heroin|fentanyl)\b',
    # Prescription fraud
    r'\b(fake|forge|counterfeit)\s+(prescription|rx)\b',
]

# PII patterns to redact from logs
PII_PATTERNS = [
    # Email addresses
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    # Phone numbers (various formats)
    (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
    (r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b', '[PHONE]'),
    # SSN
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    # Credit card numbers (simple pattern)
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]'),
]


def check_unsafe_content(query: str) -> Tuple[bool, Optional[str]]:
    """
    Check if query contains unsafe content.

    Args:
        query: User query to check

    Returns:
        Tuple of (is_unsafe, reason)
    """
    query_lower = query.lower()

    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.warning(f"Unsafe content detected in query: {pattern}")
            return True, "Query contains potentially harmful content"

    return False, None


def redact_pii(text: str) -> str:
    """
    Redact PII from text for logging.

    Args:
        text: Text to redact

    Returns:
        Text with PII redacted
    """
    redacted = text

    for pattern, replacement in PII_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted)

    return redacted


def hash_user_id(user_id: str) -> str:
    """
    Hash user ID for privacy-preserving logging.

    Args:
        user_id: User identifier

    Returns:
        Hashed user ID
    """
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def log_search_audit(
    query: str,
    user_id: str,
    search_id: str,
    result_count: int,
    confidence_score: float,
    filters: Optional[dict] = None,
) -> None:
    """
    Log search for audit trail (PII-free).

    Args:
        query: User query (will be redacted)
        user_id: User identifier (will be hashed)
        search_id: Search session ID
        result_count: Number of results returned
        confidence_score: Confidence score
        filters: Applied filters
    """
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "search_id": search_id,
        "user_id_hash": hash_user_id(user_id),
        "query_redacted": redact_pii(query),
        "result_count": result_count,
        "confidence_score": confidence_score,
        "filters": filters or {},
    }

    logger.info(f"AUDIT: {audit_entry}")


def get_crisis_resources() -> str:
    """
    Get crisis resources message for sensitive queries.

    Returns:
        Crisis resources message
    """
    return (
        "\n\n🆘 **If you're in crisis:**\n"
        "- National Suicide Prevention Lifeline: 988 (US)\n"
        "- Crisis Text Line: Text HOME to 741741 (US)\n"
        "- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/\n"
        "- Emergency Services: 911 (US) or your local emergency number\n\n"
        "Please reach out to a mental health professional or crisis counselor immediately."
    )


def sanitize_response(response: str, query: str) -> str:
    """
    Sanitize response to ensure safety guardrails.

    Args:
        response: Generated response
        query: Original query

    Returns:
        Sanitized response with disclaimer
    """
    # Check if query was about sensitive topics
    query_lower = query.lower()
    sensitive_topics = ['suicide', 'self-harm', 'kill myself', 'end my life']

    is_sensitive = any(topic in query_lower for topic in sensitive_topics)

    # Build final response
    parts = []

    # Add crisis resources if sensitive
    if is_sensitive:
        parts.append(get_crisis_resources())

    # Add main response
    parts.append(response)

    # Add disclaimer
    parts.append(f"\n\n{MEDICAL_DISCLAIMER}")

    return "\n".join(parts)


def validate_filters(filters: Optional[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate search filters.

    Args:
        filters: Filter dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filters:
        return True, None

    # Validate year range
    if "year_range" in filters:
        year_range = filters["year_range"]
        if not isinstance(year_range, dict):
            return False, "year_range must be a dictionary"

        start = year_range.get("start")
        end = year_range.get("end")

        if start and end and start > end:
            return False, "Invalid year range: start year must be before end year"

        current_year = datetime.now().year
        if start and start > current_year:
            return False, f"Invalid year range: start year cannot be in the future"
        if end and end > current_year:
            return False, f"Invalid year range: end year cannot be in the future"

    # Validate study types
    if "study_types" in filters:
        valid_types = ["RCT", "Meta-Analysis", "Systematic Review", "Cohort", "Case-Control", "Case Report"]
        study_types = filters["study_types"]

        if not isinstance(study_types, list):
            return False, "study_types must be a list"

        for study_type in study_types:
            if study_type not in valid_types:
                return False, f"Invalid study type: {study_type}. Valid types: {', '.join(valid_types)}"

    return True, None

