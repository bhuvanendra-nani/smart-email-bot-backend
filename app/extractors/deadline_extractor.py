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


def is_valid_date(date_text: str) -> bool:
    """
    Basic validation to prevent impossible dates such as:
    45/19/2026
    31/02/2026
    """

    if not date_text:
        return False

    date_text = clean_date(date_text)

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

    # Remove ordinal suffixes
    normalized = re.sub(
        r"(\d{1,2})(st|nd|rd|th)",
        r"\1",
        date_text,
        flags=re.IGNORECASE,
    )

    for fmt in formats:
        try:
            datetime.strptime(normalized, fmt)
            return True
        except ValueError:
            continue

    return False


def extract_date(text: str) -> str:
    """
    Extract the first valid complete date from a small text window.
    """

    if not text:
        return ""

    patterns = [
        # 25-07-2026 / 25/07/2026 / 25.07.2026
        r"\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}\b",

        # 16th September 2026
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+"
        rf"(?:{MONTHS})\s+\d{{4}}\b",

        # September 16th, 2026
        rf"\b(?:{MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?"
        rf"(?:,)?\s+\d{{4}}\b",

        # September 16, 2026
        rf"\b(?:{MONTHS})\s+\d{{1,2}}(?:,)?\s+\d{{4}}\b",
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
    Extract the most relevant deadline from a placement/internship email.

    Priority:
    1. Registration deadline
    2. Application deadline
    3. Submission deadline
    4. Explicit deadline
    5. Last date
    6. Apply before
    7. Due by
    8. Only then use a conservative fallback
    """

    if not text:
        return "Not mentioned"

    text = re.sub(r"\s+", " ", text).strip()

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

            start = match.end()

            # Only inspect nearby text
            window = text[start:start + 150]

            date = extract_date(window)

            if date:
                return date

    # --------------------------------------------------
    # 2. "Due by/on DATE"
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
    # 3. "Last date: DATE"
    # --------------------------------------------------

    last_date_patterns = [
        r"\blast\s+date\s*[:\-]\s*",
        r"\bdeadline\s*[:\-]\s*",
        r"\bregistration\s+deadline\s*[:\-]\s*",
        r"\bapplication\s+deadline\s*[:\-]\s*",
    ]

    for pattern in last_date_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        window = text[
            match.end():match.end() + 100
        ]

        date = extract_date(window)

        if date:
            return date

    # --------------------------------------------------
    # 4. DO NOT blindly use the first date anymore
    # --------------------------------------------------
    #
    # An email may contain:
    #
    # Test Date: 15 Sep 2026
    # Interview Date: 17 Sep 2026
    # Registration Deadline: 12 Sep 2026
    #
    # The first date is NOT necessarily the deadline.
    #
    # Therefore, return Not mentioned instead of guessing.
    # --------------------------------------------------

    return "Not mentioned"