import re

from app.extractors.deadline_extractor import extract_deadline
from app.extractors.registration_link_extractor import extract_registration_link


FIELD_LABELS = [
    "time",
    "interview time",
    "reporting time",
    "venue",
    "interview venue",
    "mode",
    "interview mode",
    "interviewer",
    "panel",
    "instructions",
    "note",
    "meeting link",
    "date",
    "interview date",
]


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize spaces
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def clean_value(value: str) -> str:
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value).strip()

    return value.strip(" \t\r\n:,-")


def stop_at_next_field(value: str) -> str:
    """
    Prevent one interview field from consuming
    the following fields.
    """

    if not value:
        return ""

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

    return clean_value(value)


def extract_labelled(text: str, labels, max_length: int = 250) -> str:
    label_pattern = "|".join(
        re.escape(label) for label in labels
    )

    pattern = (
        rf"\b(?:{label_pattern})\s*[:\-]\s*(.+)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if not match:
        return ""

    value = stop_at_next_field(match.group(1))

    if len(value) > max_length:
        return ""

    return value


def extract_interview_type(text: str) -> str:
    """
    Detect the specific interview/selection round.
    """

    patterns = [
        ("Technical Interview", r"\btechnical interview\b"),
        ("HR Interview", r"\bhr interview\b"),
        ("Managerial Interview", r"\bmanagerial interview\b"),
        ("Panel Interview", r"\bpanel interview\b"),
        ("Final Interview", r"\bfinal interview\b"),
        ("Group Discussion", r"\bgroup discussion\b"),
    ]

    for label, pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return label

    # Generic interview
    if re.search(r"\binterview\b", text, re.IGNORECASE):
        return "Interview"

    return ""


def extract_interview_time(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Interview Time",
            "Reporting Time",
            "Time",
        ],
        max_length=100,
    )


def extract_venue(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Interview Venue",
            "Venue",
        ],
        max_length=200,
    )


def extract_mode(text: str) -> str:
    # First check an explicit mode field.
    value = extract_labelled(
        text,
        [
            "Interview Mode",
            "Mode",
        ],
        max_length=100,
    )

    if value:
        lower = value.lower()

        if "hybrid" in lower:
            return "Hybrid"

        if "virtual" in lower:
            return "Virtual"

        if "online" in lower:
            return "Online"

        if "offline" in lower:
            return "Offline"

    # Then look for strong interview-specific phrases.
    lower = text.lower()

    if re.search(
        r"\b(?:online|virtual)\s+interview\b",
        lower,
    ):
        return "Virtual" if "virtual interview" in lower else "Online"

    if re.search(
        r"\binterview\b.{0,80}\b(?:online|virtual)\b",
        lower,
    ):
        return "Virtual" if "virtual" in lower else "Online"

    if re.search(
        r"\boffline\s+interview\b",
        lower,
    ):
        return "Offline"

    return ""


def extract_interviewer(text: str) -> str:
    value = extract_labelled(
        text,
        [
            "Interviewer",
            "Panel",
        ],
        max_length=200,
    )

    return value


def extract_instructions(text: str) -> str:
    value = extract_labelled(
        text,
        [
            "Instructions",
            "Note",
        ],
        max_length=400,
    )

    return value


def extract_interview_details(text: str) -> dict:
    """
    Extract interview-specific details.
    """

    if not text:
        return {
            "interview_type": "",
            "interview_date": "",
            "interview_time": "",
            "mode": "",
            "venue": "",
            "interviewer": "",
            "instructions": "",
            "meeting_link": "",
        }

    text = clean(text)

    return {
        "interview_type": extract_interview_type(text),

        # Reuse the safer common deadline extractor.
        "interview_date": extract_deadline(text),

        "interview_time": extract_interview_time(text),

        "mode": extract_mode(text),

        "venue": extract_venue(text),

        "interviewer": extract_interviewer(text),

        "instructions": extract_instructions(text),

        # Registration-link extractor now scores useful links
        # instead of blindly taking the first URL.
        "meeting_link": extract_registration_link(text),
    }