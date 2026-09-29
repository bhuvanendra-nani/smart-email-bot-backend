import re

from datetime import datetime


MONTHS = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)


def clean_date(date: str) -> str:
    if not date:
        return ""

    return re.sub(
        r"\s+",
        " ",
        date,
    ).strip(" \t\r\n:,-.")


def normalize_ordinal_date(date_text: str) -> str:
    """
    Remove ordinal suffixes:

    29th September 2026
    1st October 2026
    2nd November 2026
    3rd December 2026

    becomes:

    29 September 2026
    1 October 2026
    2 November 2026
    3 December 2026
    """

    return re.sub(
        r"(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        date_text,
        flags=re.IGNORECASE,
    )


def is_valid_date(date_text: str) -> bool:
    """
    Validate a date so impossible dates are rejected.

    Examples:
        45/19/2026 -> False
        31/02/2026 -> False
        29th September 2026 -> True
    """

    if not date_text:
        return False

    date_text = clean_date(date_text)
    normalized = normalize_ordinal_date(date_text)

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d.%m.%y",
        "%d %B %Y",
        "%d %B, %Y",
        "%B %d, %Y",
        "%B %d %Y",
    ]

    for fmt in formats:
        try:
            datetime.strptime(normalized, fmt)
            return True
        except ValueError:
            continue

    return False


def extract_date(text: str) -> str:
    """
    Extract the first valid complete date from text.

    Supported examples:
        25-07-2026
        25/07/2026
        25.07.2026
        16th September 2026
        16 September 2026
        September 16th, 2026
        September 16, 2026
    """

    if not text:
        return ""

    patterns = [
        # 25-07-2026
        # 25/07/2026
        # 25.07.2026
        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",

        # 16th September 2026
        # 16 September 2026
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+"
        rf"(?:{MONTHS})\s+\d{{4}}\b",

        # September 16th, 2026
        # September 16, 2026
        rf"\b(?:{MONTHS})\s+"
        rf"\d{{1,2}}(?:st|nd|rd|th)?"
        rf"(?:,\s*|\s+)\d{{4}}\b",
    ]

    for pattern in patterns:
        matches = re.finditer(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            value = clean_date(match.group(0))

            if is_valid_date(value):
                return value

    return ""


def extract_deadline(text: str) -> str:
    """
    Extract the most useful date from a college/career email.

    Priority:

    1. Registration deadline
    2. Application deadline
    3. Submission deadline
    4. Explicit deadline
    5. Last date
    6. Apply before/by
    7. Due by/on
    8. Register/apply/submit on or before
    9. Event/test/interview scheduled date

    The final event-date fallback is useful because college
    emails frequently describe the important date as:

        Online test is scheduled on 29th September 2026

        Interview is scheduled for 05-10-2026

        PPT is scheduled on 28th September 2026
    """

    if not text:
        return "Not mentioned"

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    # --------------------------------------------------
    # 1. HIGH-CONFIDENCE DEADLINE PHRASES
    # --------------------------------------------------

    priority_patterns = [
        r"\bregistration\s+deadline\b",
        r"\blast\s+date\s+for\s+registration\b",
        r"\bregistration\s+closes?\b",
        r"\bregistration\s+ends?\b",
        r"\bapplication\s+deadline\b",
        r"\blast\s+date\s+to\s+apply\b",
        r"\bapplication\s+closes?\b",
        r"\bapplication\s+ends?\b",
        r"\bsubmission\s+deadline\b",
        r"\bsubmission\s+date\b",
        r"\bsubmit\s+before\b",
        r"\blast\s+date\b",
        r"\bdeadline\b",
        r"\bclosing\s+date\b",
        r"\bclosing\s+on\b",
        r"\bapply\s+before\b",
        r"\bapply\s+by\b",
    ]

    for keyword_pattern in priority_patterns:
        matches = re.finditer(
            keyword_pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            window = text[
                match.end():match.end() + 150
            ]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 2. "ON OR BEFORE" DATE
    # --------------------------------------------------
    #
    # Very common college/placement wording:
    #
    #   Register on or before 29-09-2026
    #
    #   Submit on or before 30th September 2026
    #
    #   Apply on or before 1st October 2026
    #
    # Also handles:
    #
    #   on/before 29-09-2026
    #
    # This must be checked before the more generic
    # register/apply patterns.
    # --------------------------------------------------

    on_or_before_patterns = [
        r"\bon\s+or\s+before\b",
        r"\bon\s*/\s*before\b",
    ]

    for keyword_pattern in on_or_before_patterns:
        matches = re.finditer(
            keyword_pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            window = text[
                match.end():match.end() + 100
            ]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 3. DUE / SUBMIT / REGISTER / APPLY BY DATE
    # --------------------------------------------------

    relative_patterns = [
        r"\bdue\s+(?:by|on)\b",
        r"\bsubmit\s+(?:by|before|on)\b",
        r"\bregister\s+(?:by|before|on)\b",
        r"\bapply\s+(?:by|before|on)\b",
    ]

    for keyword_pattern in relative_patterns:
        matches = re.finditer(
            keyword_pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            window = text[
                match.end():match.end() + 100
            ]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 4. EXPLICIT "LABEL: DATE" PATTERNS
    # --------------------------------------------------

    label_patterns = [
        r"\blast\s+date\s*[:\-]\s*",
        r"\bdeadline\s*[:\-]\s*",
        r"\bregistration\s+deadline\s*[:\-]\s*",
        r"\bapplication\s+deadline\s*[:\-]\s*",
        r"\bsubmission\s+deadline\s*[:\-]\s*",
        r"\bclosing\s+date\s*[:\-]\s*",
    ]

    for pattern in label_patterns:
        matches = re.finditer(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            window = text[
                match.end():match.end() + 100
            ]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 5. EVENT / TEST / INTERVIEW SCHEDULED DATE
    # --------------------------------------------------

    scheduled_patterns = [
        r"\bscheduled\s+on\b",
        r"\bscheduled\s+for\b",
        r"\btest\s+(?:is\s+)?on\b",
        r"\btest\s+(?:is\s+)?scheduled\s+on\b",
        r"\btest\s+(?:is\s+)?scheduled\s+for\b",
        r"\bassessment\s+(?:is\s+)?on\b",
        r"\bassessment\s+(?:is\s+)?scheduled\s+on\b",
        r"\binterview\s+(?:is\s+)?on\b",
        r"\binterview\s+(?:is\s+)?scheduled\s+on\b",
        r"\binterview\s+(?:is\s+)?scheduled\s+for\b",
        r"\bexam\s+(?:is\s+)?on\b",
        r"\bexam\s+(?:is\s+)?scheduled\s+on\b",
        r"\bppt\s+(?:is\s+)?on\b",
        r"\bppt\s+(?:is\s+)?scheduled\s+on\b",
    ]

    for keyword_pattern in scheduled_patterns:
        matches = re.finditer(
            keyword_pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            window = text[
                match.end():match.end() + 100
            ]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 6. EVENT DATE PHRASES
    # --------------------------------------------------

    event_date_patterns = [
        r"\btest\s+date\s*[:\-]\s*",
        r"\binterview\s+date\s*[:\-]\s*",
        r"\bassessment\s+date\s*[:\-]\s*",
        r"\bexam\s+date\s*[:\-]\s*",
        r"\bppt\s+date\s*[:\-]\s*",
        r"\bdate\s+of\s+(?:test|interview|assessment|exam)\s*[:\-]?\s*",
    ]

    for pattern in event_date_patterns:
        matches = re.finditer(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            window = text[
                match.end():match.end() + 100
            ]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 7. NO SAFE DATE FOUND
    # --------------------------------------------------

    return "Not mentioned"

