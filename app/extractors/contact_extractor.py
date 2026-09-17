import re


FIELD_LABELS = [
    "contact",
    "coordinator",
    "faculty coordinator",
    "poc",
    "point of contact",
    "email",
    "phone",
    "mobile",
    "website",
    "registration",
    "deadline",
    "venue",
    "location",
]


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text.strip()


def is_valid_contact(value: str) -> bool:
    if not value:
        return False

    value = value.strip()

    # Avoid capturing huge portions of the email
    if len(value) > 200:
        return False

    if len(value.split()) > 30:
        return False

    # Contact should contain at least one useful indicator
    has_email = bool(
        re.search(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            value,
            re.IGNORECASE,
        )
    )

    has_phone = bool(
        re.search(
            r"(?:\+91[\s-]?)?[6-9]\d{9}\b",
            value,
        )
    )

    has_name = bool(
        re.search(
            r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,3}\b",
            value,
        )
    )

    return has_email or has_phone or has_name


def extract_contact(text: str) -> str:
    if not text:
        return ""

    text = clean(text)

    # ==================================================
    # 1. LABELLED CONTACT INFORMATION
    # ==================================================

    patterns = [
        r"\bContact\s*(?:Person|Details|Information)?\s*[:\-]\s*(.+)",
        r"\bCoordinator\s*[:\-]\s*(.+)",
        r"\bFaculty\s+Coordinator\s*[:\-]\s*(.+)",
        r"\bPOC\s*[:\-]\s*(.+)",
        r"\bPoint\s+of\s+Contact\s*[:\-]\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = match.group(1).strip()

        # Stop at another obvious field label
        value = re.split(
            r"\s+(?="
            r"(?:"
            + "|".join(re.escape(label) for label in FIELD_LABELS)
            + r")\s*[:\-]"
            r")",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if is_valid_contact(value):
            return value

    # ==================================================
    # 2. EMAIL ADDRESS
    # ==================================================

    email_match = re.search(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        text,
        re.IGNORECASE,
    )

    if email_match:
        return email_match.group(0).strip()

    # ==================================================
    # 3. PHONE NUMBER
    # ==================================================

    phone_match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}\b",
        text,
    )

    if phone_match:
        return phone_match.group(0).strip()

    return ""