import re


FIELD_LABELS = [
    "course codes",
    "course code",
    "important dates",
    "exam details",
    "mode",
    "mode of exam",
    "pattern",
    "duration",
    "venue",
    "syllabus",
    "rules",
    "rules & regulations",
    "rules and regulations",
    "note",
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
    Stop extraction when another known quiz field starts.
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


def find_field(text: str, labels, max_length: int = 500) -> str:
    """
    Safely extract a labelled field without consuming
    the rest of the email.
    """

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


def extract_course_codes(text: str) -> str:
    value = find_field(
        text,
        ["Course Codes", "Course Code"],
        max_length=250,
    )

    return value


def extract_important_dates(text: str) -> str:
    value = find_field(
        text,
        ["Important Dates", "Important Date"],
        max_length=500,
    )

    return value


def extract_mode(text: str) -> str:
    value = find_field(
        text,
        ["Mode of Exam", "Mode"],
        max_length=100,
    )

    if value:
        lower = value.lower()

        if "online" in lower:
            return "Online"

        if "offline" in lower:
            return "Offline"

        if "virtual" in lower:
            return "Virtual"

        if "hybrid" in lower:
            return "Hybrid"

        return value

    return ""


def extract_pattern(text: str) -> str:
    return find_field(
        text,
        ["Pattern"],
        max_length=250,
    )


def extract_duration(text: str) -> str:
    return find_field(
        text,
        ["Duration"],
        max_length=100,
    )


def extract_venue(text: str) -> str:
    return find_field(
        text,
        ["Venue"],
        max_length=200,
    )


def extract_syllabus(text: str) -> str:
    return find_field(
        text,
        ["Syllabus"],
        max_length=500,
    )


def extract_rules(text: str) -> str:
    return find_field(
        text,
        [
            "Rules & Regulations",
            "Rules and Regulations",
            "Rules",
        ],
        max_length=700,
    )


def extract_note(text: str) -> str:
    return find_field(
        text,
        ["NOTE", "Note"],
        max_length=500,
    )


def extract_quiz_details(text: str) -> dict:
    """
    Extract information from quiz/test emails.
    """

    if not text:
        return {}

    text = clean(text)

    return {
        "course_codes": extract_course_codes(text),
        "important_dates": extract_important_dates(text),
        "mode": extract_mode(text),
        "pattern": extract_pattern(text),
        "duration": extract_duration(text),
        "venue": extract_venue(text),
        "syllabus": extract_syllabus(text),
        "rules": extract_rules(text),
        "note": extract_note(text),
    }