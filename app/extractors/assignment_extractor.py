import re


FIELD_LABELS = [
    "course",
    "subject",
    "faculty",
    "faculty name",
    "deadline",
    "last date",
    "submission",
    "submission link",
    "submission type",
    "file type",
    "instructions",
    "late submission",
    "late submissions",
]


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize spaces but preserve useful newlines temporarily
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def clean_value(value: str) -> str:
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value).strip()

    # Remove common trailing punctuation
    return value.strip(" \t\r\n:,-")


def stop_at_next_field(value: str) -> str:
    """
    Stop extraction when another known assignment field starts.
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


def find_labelled(text: str, labels, max_length: int = 300) -> str:
    """
    Extract a short value after labels such as:
    Course:, Subject:, Faculty:
    """

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


def extract_faculty(text: str) -> str:
    patterns = [
        r"\bFaculty\s*(?:Name)?\s*[:\-]\s*(.+)",
        r"\bProfessor\s*[:\-]\s*(.+)",
        r"\bInstructor\s*[:\-]\s*(.+)",
        r"\bSubmitted\s+by\s+Faculty\s*[:\-]\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = stop_at_next_field(match.group(1))

            if 2 <= len(value) <= 120:
                return value

    # Common email header:
    # From: Dr. XYZ
    match = re.search(
        r"^\s*From\s*:\s*([^\n]+)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )

    if match:
        value = clean_value(match.group(1))

        # Don't treat an email address alone as faculty
        if (
            value
            and len(value) <= 120
            and "@" not in value
        ):
            return value

    return ""


def extract_deadline(text: str) -> str:
    patterns = [
        r"\bon\s+or\s+before\s+([^\n.]+)",
        r"\bsubmit\s+(?:it\s+)?before\s+([^\n.]+)",
        r"\bsubmission\s+deadline\s*[:\-]?\s*([^\n.]+)",
        r"\bdeadline\s*[:\-]\s*([^\n.]+)",
        r"\blast\s+date\s*[:\-]\s*([^\n.]+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = clean_value(match.group(1))

            if len(value) <= 100:
                return value

    return ""


def extract_submission_link(text: str) -> str:
    links = re.findall(
        r"https?://[^\s<>\"')]+",
        text,
        re.IGNORECASE,
    )

    if not links:
        return ""

    # Prefer links near submission-related words
    for link in links:
        context_match = re.search(
            rf".{{0,100}}(?:submit|submission|upload|assignment).{{0,100}}"
            rf"{re.escape(link)}",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if context_match:
            return link.rstrip(".,;")

    return links[0].rstrip(".,;")


def extract_submission_type(text: str) -> str:
    # Prefer explicit field
    match = re.search(
        r"\b(?:File\s*Type|Submission\s*Type|Format)\s*[:\-]\s*"
        r"([^\n]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        value = clean_value(match.group(1))

        if len(value) <= 100:
            return value

    # Common formats
    formats = [
        ("pdf", "PDF"),
        ("docx", "DOCX"),
        ("doc", "DOC"),
        ("pptx", "PPTX"),
        ("soft-copy", "Soft Copy"),
        ("soft copy", "Soft Copy"),
        ("hard-copy", "Hard Copy"),
        ("hard copy", "Hard Copy"),
    ]

    lower = text.lower()

    for keyword, label in formats:
        if keyword in lower:
            return label

    return ""


def extract_instructions(text: str) -> str:
    patterns = [
        r"\bInstructions?\s*[:\-]\s*(.+)",
        r"\bPlease\s+(.+?)(?=\b(?:Late\s+Submission|Deadline|Last\s+Date)\b|$)",
        r"\bStudents\s+(?:are\s+required|should|must)\s+(.+?)(?=\b(?:Late\s+Submission|Deadline|Last\s+Date)\b|$)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            value = clean_value(match.group(1))

            if 5 <= len(value) <= 500:
                return value

    return ""


def extract_late_submission(text: str) -> str:
    patterns = [
        r"\bLate\s+Submissions?\s*[:\-]\s*(.+)",
        r"\bLate\s+Submissions?\s+(?:will|are|is)\s+(.+)",
        r"\bNo\s+late\s+submissions?\s+(.+)",
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


def extract_assignment_details(text: str) -> dict:
    """
    Extract assignment details from academic emails.

    Returns:
        faculty
        course
        deadline
        submission_link
        submission_type
        instructions
        late_submission
    """

    if not text:
        return {}

    text = clean(text)

    return {
        "faculty": extract_faculty(text),
        "course": find_labelled(
            text,
            ["course", "subject"],
            max_length=150,
        ),
        "deadline": extract_deadline(text),
        "submission_link": extract_submission_link(text),
        "submission_type": extract_submission_type(text),
        "instructions": extract_instructions(text),
        "late_submission": extract_late_submission(text),
    }