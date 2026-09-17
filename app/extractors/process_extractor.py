import re


FIELD_LABELS = [
    "selection process",
    "hiring process",
    "recruitment process",
    "process",
    "eligibility",
    "eligible branches",
    "branches",
    "batch",
    "ctc",
    "stipend",
    "deadline",
    "last date",
    "registration",
    "registration link",
    "venue",
    "location",
    "mode",
    "contact",
    "company",
    "role",
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


def is_valid_process(value: str) -> bool:
    if not value:
        return False

    value = value.strip()

    # Prevent huge email-body captures
    if len(value) > 500:
        return False

    if len(value.split()) > 80:
        return False

    invalid_values = {
        "n/a",
        "na",
        "not mentioned",
        "not applicable",
        "nil",
        "none",
    }

    return value.lower() not in invalid_values


def stop_at_next_field(value: str) -> str:
    """
    Stop extraction when another structured field begins.
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


def extract_process(text: str) -> str:
    if not text:
        return ""

    text = clean(text)

    # ==================================================
    # 1. EXPLICIT PROCESS FIELDS
    # ==================================================

    patterns = [
        r"\bSelection\s+Process\s*[:\-]\s*(.+)",
        r"\bHiring\s+Process\s*[:\-]\s*(.+)",
        r"\bRecruitment\s+Process\s*[:\-]\s*(.+)",
        r"\bProcess\s*[:\-]\s*(.+)",
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

        if is_valid_process(value):
            return value

    # ==================================================
    # 2. NATURAL LANGUAGE PROCESS
    # ==================================================

    natural_patterns = [
        r"\bselection\s+process\s+(?:includes|consists\s+of)\s+(.+)",
        r"\bhiring\s+process\s+(?:includes|consists\s+of)\s+(.+)",
        r"\brecruitment\s+process\s+(?:includes|consists\s+of)\s+(.+)",
        r"\bthe\s+selection\s+process\s+is\s+(.+)",
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

        if is_valid_process(value):
            return value

    # ==================================================
    # 3. COMMON PROCESS PHRASES
    # ==================================================

    process_patterns = [
        r"\b(?:process|stages?)\s*[:\-]\s*"
        r"((?:online\s+test|aptitude|coding|technical\s+interview|hr\s+interview).{0,300})",
    ]

    for pattern in process_patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = stop_at_next_field(match.group(1))

        if is_valid_process(value):
            return value

    return ""