import re


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_batch(value: str) -> str:
    if not value:
        return ""

    value = clean(value)

    # Keep only reasonable batch-related text
    if len(value) > 60:
        return ""

    return value.strip(" :-|,.")


def extract_batch(text: str) -> str:
    """
    Extract eligible graduating batch information.

    Examples:
        Batch: 2027
        2027 Batch
        Graduating Batch 2027
        2027 Graduating Students
        2026 Passouts
        Batch of 2027
        Final Year Students
    """

    if not text:
        return ""

    text = clean(text)

    # --------------------------------------------------
    # 1. Explicit "Batch: 2027"
    # --------------------------------------------------

    patterns = [
        r"\bbatch\s*[:\-]\s*(20\d{2})\b",

        # Batch of 2027
        r"\bbatch\s+of\s+(20\d{2})\b",

        # Graduating Batch 2027
        r"\bgraduating\s+batch\s+(20\d{2})\b",

        # 2027 Batch
        r"\b(20\d{2})\s+batch\b",

        # 2027 Graduating Students
        r"\b(20\d{2})\s+graduating\s+students?\b",

        # 2026 Passouts
        r"\b(20\d{2})\s+passouts?\b",

        # 2026 Graduates
        r"\b(20\d{2})\s+graduates?\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        year = match.group(1)

        # Sanity check
        if 2020 <= int(year) <= 2035:
            return year

    # --------------------------------------------------
    # 2. Final-year eligibility
    # --------------------------------------------------

    final_year_patterns = [
        r"\bfinal\s+year\s+students?\b",
        r"\bfinal\s+year\b",
        r"\bcurrently\s+in\s+final\s+year\b",
    ]

    for pattern in final_year_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "Final Year"

    return ""