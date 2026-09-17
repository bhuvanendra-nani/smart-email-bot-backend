import re


def clean(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_ctc(value: str) -> str:
    if not value:
        return ""

    value = clean(value)

    # Stop at another common field
    value = re.split(
        r"\s+(?=(?:stipend|eligibility|branches|batch|"
        r"deadline|last date|location|venue|mode|process|"
        r"registration|role|position)\s*[:\-])",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    value = value.strip(" :-|,.;")

    # CTC should be reasonably short
    if len(value) > 120:
        return ""

    if len(value.split()) > 20:
        return ""

    return value


def extract_ctc(text: str) -> str:
    """
    Extract CTC / salary package from placement emails.

    Examples:
        CTC: Rs. 14 LPA
        Package: 18 LPA
        Compensation: 12 LPA
        ₹18 LPA
        14 LPA + variable
        25 Lakhs
    """

    if not text:
        return ""

    text = clean(text)

    # --------------------------------------------------
    # 1. Explicit CTC / Package / Compensation field
    # --------------------------------------------------

    labelled_patterns = [
        r"\bCTC\s*[:\-]\s*(.+?)(?=\s+(?:stipend|eligibility|branches|batch|"
        r"deadline|last date|location|venue|mode|process|registration|"
        r"role|position)\s*[:\-]|$)",

        r"\bPackage\s*[:\-]\s*(.+?)(?=\s+(?:stipend|eligibility|branches|batch|"
        r"deadline|last date|location|venue|mode|process|registration|"
        r"role|position)\s*[:\-]|$)",

        r"\bCompensation\s*[:\-]\s*(.+?)(?=\s+(?:stipend|eligibility|branches|batch|"
        r"deadline|last date|location|venue|mode|process|registration|"
        r"role|position)\s*[:\-]|$)",
    ]

    for pattern in labelled_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = normalize_ctc(match.group(1))

        if value:
            # Prefer a clean salary expression inside the field
            salary = extract_salary_expression(value)

            if salary:
                return salary

            return value

    # --------------------------------------------------
    # 2. Direct salary expressions
    # --------------------------------------------------

    return extract_salary_expression(text)


def extract_salary_expression(text: str) -> str:
    """
    Extract a concise salary/package expression.
    """

    if not text:
        return ""

    patterns = [

        # Rs. 14 LPA / Rs 14 LPA
        r"\bRs\.?\s*\d+(?:\.\d+)?\s*LPA"
        r"(?:\s*\+\s*[^,.;]{0,40})?",

        # ₹14 LPA
        r"₹\s*\d+(?:\.\d+)?\s*LPA"
        r"(?:\s*\+\s*[^,.;]{0,40})?",

        # 14 LPA
        r"\b\d+(?:\.\d+)?\s*LPA"
        r"(?:\s*\+\s*[^,.;]{0,40})?",

        # 25 Lakhs / 25 Lakh
        r"\b\d+(?:\.\d+)?\s*Lakhs?"
        r"(?:\s*\+\s*[^,.;]{0,40})?",
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

        # Prevent accidental huge captures
        if len(value) <= 100:
            return value

    return ""