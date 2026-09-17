import re

from app.extractors.deadline_extractor import extract_deadline
from app.extractors.registration_link_extractor import extract_registration_link


FIELD_LABELS = [
    "hackathon",
    "event",
    "event name",
    "title",
    "organized by",
    "organizer",
    "hosted by",
    "venue",
    "location",
    "mode",
    "event mode",
    "finale",
    "finale date",
    "event date",
    "prize pool",
    "prize",
    "registration fee",
    "entry fee",
    "team size",
    "maximum team size",
    "problem statement",
    "theme",
    "job opportunity",
    "job offer",
    "opportunity",
    "ctc",
    "certificate",
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


def extract_event_name(text: str) -> str:
    value = extract_labelled(
        text,
        [
            "Event Name",
            "Hackathon",
            "Event",
            "Title",
        ],
        max_length=250,
    )

    if value:
        return value

    # Natural language:
    # "Join the XYZ Hackathon"
    patterns = [
        r"\b(?:join|participate in|register for)\s+(?:the\s+)?(.{3,150}?\bhackathon\b)",
        r"\b(.{3,150}?\bhackathon\b)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = clean_value(match.group(1))

            if len(value) <= 250:
                return value

    return ""


def extract_organizer(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Organized By",
            "Organizer",
            "Hosted By",
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


def extract_mode(text: str) -> str:
    # First check an explicit mode field.
    value = extract_labelled(
        text,
        [
            "Event Mode",
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

    lower = text.lower()

    # Only detect mode when connected to the hackathon/event.
    if re.search(
        r"\b(?:online|virtual)\s+hackathon\b",
        lower,
    ):
        return "Virtual" if "virtual hackathon" in lower else "Online"

    if re.search(
        r"\boffline\s+hackathon\b",
        lower,
    ):
        return "Offline"

    if re.search(
        r"\bhackathon\b.{0,80}\b(?:online|virtual)\b",
        lower,
    ):
        return "Virtual" if "virtual" in lower else "Online"

    if re.search(
        r"\bhackathon\b.{0,80}\boffline\b",
        lower,
    ):
        return "Offline"

    if re.search(
        r"\bhybrid\s+hackathon\b",
        lower,
    ):
        return "Hybrid"

    return ""


def extract_finale_date(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Finale Date",
            "Finale",
            "Event Date",
        ],
        max_length=150,
    )


def extract_prize_pool(text: str) -> str:
    value = extract_labelled(
        text,
        [
            "Prize Pool",
            "Prize",
        ],
        max_length=150,
    )

    return value


def extract_registration_fee(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Registration Fee",
            "Entry Fee",
        ],
        max_length=100,
    )


def extract_team_size(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Maximum Team Size",
            "Team Size",
        ],
        max_length=100,
    )


def extract_problem_statement(text: str) -> str:
    return extract_labelled(
        text,
        [
            "Problem Statement",
            "Theme",
        ],
        max_length=400,
    )


def extract_job_opportunity(text: str) -> str:
    value = extract_labelled(
        text,
        [
            "Job Opportunity",
            "Job Offer",
            "Opportunity",
        ],
        max_length=250,
    )

    return value


def extract_certificate(text: str) -> str:
    lower = text.lower()

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


def extract_hackathon_details(text: str) -> dict:
    """
    Extract hackathon-specific details safely.
    """

    if not text:
        return {
            "event_name": "",
            "organizer": "",
            "venue": "",
            "mode": "",
            "registration_deadline": "",
            "finale_date": "",
            "prize_pool": "",
            "registration_fee": "",
            "team_size": "",
            "problem_statement": "",
            "job_opportunity": "",
            "certificate": "",
            "registration_link": "",
        }

    text = clean(text)

    return {
        "event_name": extract_event_name(text),

        "organizer": extract_organizer(text),

        "venue": extract_venue(text),

        "mode": extract_mode(text),

        "registration_deadline": extract_deadline(text),

        "finale_date": extract_finale_date(text),

        "prize_pool": extract_prize_pool(text),

        "registration_fee": extract_registration_fee(text),

        "team_size": extract_team_size(text),

        "problem_statement": extract_problem_statement(text),

        "job_opportunity": extract_job_opportunity(text),

        "certificate": extract_certificate(text),

        "registration_link": extract_registration_link(text),
    }