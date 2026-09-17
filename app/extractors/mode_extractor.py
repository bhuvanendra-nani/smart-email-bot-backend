import re


VALID_MODES = {
    "Online",
    "Offline",
    "Virtual",
    "Hybrid",
}


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_mode(text: str) -> str:
    if not text:
        return ""

    text = clean(text)
    lower = text.lower()

    # ==================================================
    # 1. EXPLICIT MODE FIELD
    # ==================================================

    explicit_patterns = [
        r"\bmode\s*[:\-]\s*(online|offline|virtual|hybrid)\b",
        r"\bwork\s*mode\s*[:\-]\s*(online|offline|virtual|hybrid)\b",
        r"\binterview\s*mode\s*[:\-]\s*(online|offline|virtual|hybrid)\b",
        r"\btest\s*mode\s*[:\-]\s*(online|offline|virtual|hybrid)\b",
    ]

    for pattern in explicit_patterns:
        match = re.search(
            pattern,
            lower,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).capitalize()

    # ==================================================
    # 2. STRONG PHRASES
    # ==================================================

    if re.search(
        r"\b(?:conducted|held|conducting|organized|available)"
        r"\s+(?:entirely\s+)?online\b",
        lower,
    ):
        return "Online"

    if re.search(
        r"\b(?:conducted|held|conducting|organized)"
        r"\s+(?:entirely\s+)?offline\b",
        lower,
    ):
        return "Offline"

    if re.search(
        r"\b(?:conducted|held|available|offered)\s+virtually\b",
        lower,
    ):
        return "Virtual"

    if re.search(
        r"\b(?:both\s+)?online\s+and\s+offline\b",
        lower,
    ):
        return "Hybrid"

    if re.search(
        r"\boffline\s+and\s+online\b",
        lower,
    ):
        return "Hybrid"

    # ==================================================
    # 3. EVENT / INTERVIEW / TEST PHRASES
    # ==================================================

    if re.search(
        r"\b(?:online|virtual)\s+"
        r"(?:interview|test|assessment|exam|workshop|session|drive|event)\b",
        lower,
    ):
        if "virtual" in lower:
            return "Virtual"

        return "Online"

    if re.search(
        r"\boffline\s+"
        r"(?:interview|test|assessment|exam|workshop|session|drive|event)\b",
        lower,
    ):
        return "Offline"

    # ==================================================
    # 4. MEETING / WEBINAR
    # ==================================================

    if re.search(
        r"\b(?:virtual|online)\s+"
        r"(?:meeting|webinar|orientation|session)\b",
        lower,
    ):
        return "Virtual" if "virtual" in lower else "Online"

    # ==================================================
    # 5. HYBRID
    # ==================================================

    if re.search(
        r"\bhybrid\s+"
        r"(?:mode|event|workshop|session|drive|interview|work)\b",
        lower,
    ):
        return "Hybrid"

    return ""