import re

from app.extractors.deadline_extractor import extract_deadline
from app.extractors.registration_link_extractor import extract_registration_link


FIELD_LABELS = [
    "workshop",
    "workshop name",
    "title",
    "speaker",
    "resource person",
    "chief guest",
    "organized by",
    "organizer",
    "conducted by",
    "venue",
    "location",
    "time",
    "timing",
    "mode",
    "workshop mode",
    "certificate",
    "prerequisites",
    "requirements",
    "contact",
    "coordinator",
    "registration link",
]


def clean(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def clean_value(value: str) -> str:
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value).strip()

    return value.strip(" \t\r\n:,-")


def stop_at_next_field(value: str) -> str:
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

    pattern = rf"\b(?:{label_pattern})\s*[:\-]\s*(.+)"

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


def extract_workshop_name(text: str) -> str:
    value = extract_labelled(
        text,
        [
            "Workshop Name",
            "Workshop",
            "Title",
        ],
        max_length=200,
    )

    if value:
        return value

    # Natural-language workshop title.
    patterns = [
        r"\bworkshop\s+on\s+([^.\n]{3,150})",
        r"\bworkshop\s*-\s*([^.\n]{3,150})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = clean_value(match.group(1))

            if len(value) <= 200:
                return value

    return ""


def extract_speaker(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Speaker",
            "Resource Person",
            "Chief Guest",
        ],
        max_length=200,
    )


def extract_organizer(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Organized By",
            "Organizer",
            "Conducted By",
        ],
        max_length=200,
    )


def extract_venue(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Venue",
        ],
        max_length=200,
    )


def extract_workshop_time(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Workshop Time",
            "Timing",
            "Time",
        ],
        max_length=100,
    )


def extract_mode(text: str) -> str:
    # Prefer explicit mode field.
    value = extract_labelled(
        text,
        [
            "Workshop Mode",
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

    # Only detect online/offline when connected
    # to the workshop/event itself.
    lower = text.lower()

    if re.search(
        r"\b(?:online|virtual)\s+workshop\b",
        lower,
    ):
        return "Virtual" if "virtual workshop" in lower else "Online"

    if re.search(
        r"\boffline\s+workshop\b",
        lower,
    ):
        return "Offline"

    if re.search(
        r"\bworkshop\b.{0,80}\b(?:online|virtual)\b",
        lower,
    ):
        return "Virtual" if "virtual" in lower else "Online"

    if re.search(
        r"\bworkshop\b.{0,80}\boffline\b",
        lower,
    ):
        return "Offline"

    return ""


def extract_certificate(text: str) -> str:
    lower = text.lower()

    # Strong explicit statements first.
    if re.search(
        r"\bcertificate\s+will\s+be\s+provided\b",
        lower,
    ):
        return "Yes"

    if re.search(
        r"\bparticipation\s+certificate\b",
        lower,
    ):
        return "Participation Certificate"

    if re.search(
        r"\bcertificate\s+(?:provided|available|issued|awarded)\b",
        lower,
    ):
        return "Available"

    return ""


def extract_prerequisites(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Prerequisites",
            "Requirements",
        ],
        max_length=400,
    )


def extract_contact(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Contact",
            "Coordinator",
        ],
        max_length=200,
    )


def extract_workshop_details(text: str) -> dict:
    """
    Extract workshop-specific information safely.
    """

    if not text:
        return {
            "workshop_name": "",
            "speaker": "",
            "organizer": "",
            "date": "",
            "time": "",
            "venue": "",
            "mode": "",
            "certificate": "",
            "prerequisites": "",
            "registration_link": "",
            "contact": "",
        }

    text = clean(text)

    return {
        "workshop_name": extract_workshop_name(text),

        "speaker": extract_speaker(text),

        "organizer": extract_organizer(text),

        "date": extract_deadline(text),

        "time": extract_workshop_time(text),

        "venue": extract_venue(text),

        "mode": extract_mode(text),

        "certificate": extract_certificate(text),

        "prerequisites": extract_prerequisites(text),

        "registration_link": extract_registration_link(text),

        "contact": extract_contact(text),
    }