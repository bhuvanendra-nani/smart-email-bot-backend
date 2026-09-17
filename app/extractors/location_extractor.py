import re


FIELD_LABELS = [
    "location",
    "city",
    "campus",
    "work location",
    "venue",
    "mode",
    "company",
    "role",
    "eligibility",
    "branches",
    "batch",
    "ctc",
    "stipend",
    "deadline",
    "last date",
    "registration",
    "process",
    "contact",
]


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text.strip()


def is_valid_location(value: str) -> bool:
    if not value:
        return False

    value = value.strip()

    # Prevent huge email-body captures
    if len(value) > 150:
        return False

    if len(value.split()) > 20:
        return False

    invalid_values = {
        "n/a",
        "na",
        "not mentioned",
        "not applicable",
        "nil",
        "none",
        "online",
        "remote",
    }

    if value.lower() in invalid_values:
        return False

    return True


def stop_at_next_field(value: str) -> str:
    """
    Stop location extraction when another structured
    field starts.
    """

    pattern = (
        r"\s+(?="
        r"(?:"
        + "|".join(re.escape(label) for label in FIELD_LABELS)
        + r")\s*[:\-]"
        r")"
    )

    value = re.split(
        pattern,
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return value.strip(" \t\r\n,;|-:")


def extract_location(text: str) -> str:
    if not text:
        return ""

    text = clean(text)

    # ==================================================
    # 1. EXPLICIT LOCATION FIELDS
    # ==================================================

    patterns = [
        r"\bWork\s+Location\s*[:\-]\s*(.+)",
        r"\bLocation\s*[:\-]\s*(.+)",
        r"\bCity\s*[:\-]\s*(.+)",
        r"\bCampus\s*[:\-]\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = stop_at_next_field(match.group(1))

        if is_valid_location(value):
            return value

    # ==================================================
    # 2. NATURAL LANGUAGE LOCATION
    # ==================================================

    natural_patterns = [
        r"\b(?:work|job)\s+(?:location|located)\s+(?:is|:)\s*(.+)",
        r"\bthe\s+(?:job|work)\s+location\s+is\s+(.+)",
        r"\bposition\s+is\s+(?:based|located)\s+in\s+(.+)",
        r"\bbased\s+in\s+([A-Za-z][A-Za-z .,'-]{2,80})",
    ]

    for pattern in natural_patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = stop_at_next_field(match.group(1))

        if is_valid_location(value):
            return value

    return ""