import re


FIELD_LABELS = (
    r"ctc|package|compensation|eligibility|branches|batch|"
    r"deadline|last date|registration|registration link|"
    r"company|role|position|location|venue|mode|process|"
    r"contact|action"
)


def clean(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_stipend(value: str) -> str:
    if not value:
        return ""

    value = clean(value)

    # Stop at the next known field
    value = re.split(
        rf"\s+(?=(?:{FIELD_LABELS})\s*[:\-])",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    value = value.strip(" :-|,.;")

    if len(value) > 100:
        return ""

    if len(value.split()) > 15:
        return ""

    return value


def extract_money_stipend(text: str) -> str:
    """
    Extract a concise stipend amount.
    """

    if not text:
        return ""

    patterns = [
        # Rs. 40,000 per month
        r"\bRs\.?\s*\d[\d,]*(?:\.\d+)?"
        r"(?:\s*/\s*month|\s+per\s+month)?",

        # ₹50,000/month
        r"₹\s*\d[\d,]*(?:\.\d+)?"
        r"(?:\s*/\s*month|\s+per\s+month)?",

        # 40000/month
        r"\b\d[\d,]*(?:\.\d+)?\s*/\s*month\b",

        # 40000 per month
        r"\b\d[\d,]*(?:\.\d+)?\s+per\s+month\b",

        # 40000/monthly
        r"\b\d[\d,]*(?:\.\d+)?\s*/\s*monthly\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = clean(match.group(0))

        if len(value) <= 60:
            return value

    return ""


def extract_stipend(text: str) -> str:
    """
    Extract internship stipend.

    Examples:
        Stipend: 40000
        Monthly Stipend: 35000
        Rs. 40,000 per month
        ₹50,000/month
        40000/month
    """

    if not text:
        return ""

    text = clean(text)

    # --------------------------------------------------
    # 1. Explicit Stipend field
    # --------------------------------------------------

    labelled_patterns = [
        rf"\bmonthly\s+stipend\s*[:\-]\s*(.+?)(?=\s+(?:{FIELD_LABELS})\s*[:\-]|$)",

        rf"\bstipend\s*[:\-]\s*(.+?)(?=\s+(?:{FIELD_LABELS})\s*[:\-]|$)",
    ]

    for pattern in labelled_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = normalize_stipend(match.group(1))

        if not value:
            continue

        # Prefer a clean monetary value
        money = extract_money_stipend(value)

        if money:
            return money

        # Numeric stipend field such as "40000"
        if re.fullmatch(
            r"(?:₹|Rs\.?\s*)?\d[\d,]*(?:\.\d+)?",
            value,
            re.IGNORECASE,
        ):
            return value

        # Accept short useful values such as
        # "40,000 per month"
        if len(value) <= 80:
            return value

    # --------------------------------------------------
    # 2. Direct stipend expressions
    # --------------------------------------------------

    return extract_money_stipend(text)