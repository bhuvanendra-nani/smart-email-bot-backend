import re


FIELD_LABELS = [
    "venue",
    "exam venue",
    "interview venue",
    "location of exam",
    "location",
    "city",
    "campus",
    "work location",
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


def is_valid_venue(value: str) -> bool:
    if not value:
        return False

    value = value.strip()

    # Prevent huge email-body captures
    if len(value) > 200:
        return False

    if len(value.split()) > 30:
        return False

    invalid_values = {
        "n/a",
        "na",
        "not mentioned",
        "not applicable",
        "nil",
        "none",
        "online",
        "virtual",
        "remote",
    }

    if value.lower() in invalid_values:
        return False

    return True


def stop_at_next_field(value: str) -> str:
    """
    Stop venue extraction when another structured field begins.
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


def extract_venue(text: str) -> str:
    if not text:
        return ""

    text = clean(text)

    # ==================================================
    # 1. EXPLICIT VENUE FIELDS
    # ==================================================

    patterns = [
        r"\bExam\s+Venue\s*[:\-]\s*(.+)",
        r"\bInterview\s+Venue\s*[:\-]\s*(.+)",
        r"\bLocation\s+of\s+Exam\s*[:\-]\s*(.+)",
        r"\bVenue\s*[:\-]\s*(.+)",
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

        if is_valid_venue(value):
            return value

    # ==================================================
    # 2. NATURAL LANGUAGE
    # ==================================================

    natural_patterns = [
        r"\bVenue\s+is\s+(.+)",
        r"\bThe\s+venue\s+is\s+(.+)",
        r"\bExam\s+will\s+be\s+held\s+at\s+(.+)",
        r"\bInterview\s+will\s+be\s+held\s+at\s+(.+)",
        r"\b(?:test|exam|interview)\s+venue\s+is\s+(.+)",
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

        if is_valid_venue(value):
            return value

    return ""