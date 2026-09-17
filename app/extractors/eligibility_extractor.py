
import re


# ============================================================
# FIELD LABELS
# ============================================================

FIELD_LABELS = (
    r"ctc|stipend|salary|last date|deadline|website|"
    r"selection process|selection procedure|registration|"
    r"registration link|job role|role|position|company|"
    r"branches|eligible branches|batch|venue|location|mode|"
    r"process|contact|action|description"
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean(text: str) -> str:

    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(r"https?://\S+", " ", text)

    # Normalize common markdown / email formatting
    text = text.replace("**", " ")
    text = text.replace("__", " ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# VALIDATE ELIGIBILITY
# ============================================================

def valid_eligibility(value: str) -> bool:
    """
    Reject obviously incorrect or oversized captures.
    """

    if not value:
        return False

    value = clean(value)

    if len(value) < 5:
        return False

    # Eligibility should remain reasonably concise.
    if len(value) > 500:
        return False

    if len(value.split()) > 80:
        return False

    value_lower = value.lower()

    # --------------------------------------------------------
    # Reject values that clearly contain unrelated fields.
    # --------------------------------------------------------

    bad_field_patterns = [
        r"\bctc\s*[:\-]",
        r"\bstipend\s*[:\-]",
        r"\bsalary\s*[:\-]",
        r"\blast date\s*[:\-]",
        r"\bdeadline\s*[:\-]",
        r"\bwebsite\s*[:\-]",
        r"\bregistration link\s*[:\-]",
        r"\bselection process\s*[:\-]",
        r"\bvenue\s*[:\-]",
        r"\bcontact\s*[:\-]",
    ]

    for pattern in bad_field_patterns:
        if re.search(pattern, value_lower):
            return False

    return True


# ============================================================
# REMOVE TRAILING FIELD CONTENT
# ============================================================

def stop_at_next_field(value: str) -> str:
    """
    Remove everything beginning with another known field.

    Handles both:

        CTC: 14 LPA

    and:

        CTC
        14 LPA

    because VIT emails often omit ':'.
    """

    if not value:
        return ""

    # --------------------------------------------------------
    # Field followed by colon / hyphen
    # --------------------------------------------------------

    value = re.split(
        rf"\s+(?=(?:{FIELD_LABELS})\s*[:\-])",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # --------------------------------------------------------
    # Field followed directly by another value.
    #
    # Example:
    #
    # Eligibility ... No Standing Arrears CTC 14 LPA
    #
    # We stop at CTC.
    # --------------------------------------------------------

    value = re.split(
        rf"\s+(?=(?:{FIELD_LABELS})\s+(?:"
        r"(?:₹|rs\.?|inr|\$|€|£|\d|"
        r"will|not|to|for|on|by|https?://|"
        r"[A-Za-z]))"
        r")",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return value.strip()


# ============================================================
# EXTRACT LABELLED BLOCK
# ============================================================

def extract_labelled_block(text: str, label: str) -> str:
    """
    Extract text after an eligibility label.

    Supports formats such as:

        Eligibility Criteria: 75% in X and XII

        Eligibility Criteria
        75% in X and XII

        Eligibility Criteria
        *75% in X and XII*
        *No Standing Arrears*

    Stops before CTC / Stipend / Deadline / Website etc.
    """

    if not text:
        return ""

    # --------------------------------------------------------
    # First attempt: explicit label followed by value
    # --------------------------------------------------------

    pattern = rf"""
        \b{re.escape(label)}\b
        \s*[:\-]?\s*
        (.+?)
        (?=
            \s+(?:{FIELD_LABELS})\s*[:\-]
            |
            \s+(?:{FIELD_LABELS})\s+
            (?:
                ₹|rs\.?|inr|\$|€|£|\d|
                will|not|to|for|on|by|https?://
            )
            |
            $
        )
    """

    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.VERBOSE,
    )

    if match:

        value = clean(match.group(1))

        value = stop_at_next_field(value)

        if valid_eligibility(value):
            return value

    return ""


# ============================================================
# EXTRACT ELIGIBILITY FROM COMMON VIT FORMAT
# ============================================================

def extract_vit_style_eligibility(text: str) -> str:
    """
    Handles the common CDC email structure:

        Eligibility Criteria
        *% in X and XII – 75% or 7.5 CGPA*
        *in Pursuing Degree – 75% or 7.5 CGPA*
        *in UG (for PGs) – 75% or 7.5 CGPA*
        *No Standing Arrears*

        CTC
        *14 LPA*

    """

    patterns = [
        r"\beligibility\s+criteria\b\s*(.+?)"
        r"(?=\s+\bctc\b|\s+\bstipend\b|\s+\bsalary\b|"
        r"\s+\blast\s+date\b|\s+\bdeadline\b|\s+\bwebsite\b|$)",

        r"\beligible\s+branches\b.*?"
        r"\beligibility\s+criteria\b\s*(.+?)"
        r"(?=\s+\bctc\b|\s+\bstipend\b|\s+\bsalary\b|"
        r"\s+\blast\s+date\b|\s+\bdeadline\b|\s+\bwebsite\b|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = clean(match.group(1))

        value = stop_at_next_field(value)

        if valid_eligibility(value):
            return value

    return ""


# ============================================================
# NATURAL LANGUAGE ELIGIBILITY
# ============================================================

def extract_natural_eligibility(text: str) -> str:

    patterns = [

        r"\beligible\s+(?:candidates|students|applicants)"
        r"\s+(?:are|must be|should be)\s+(.+?)"
        r"(?=[.!?](?:\s|$)|"
        r"\s+(?:ctc|stipend|salary|deadline|last date|"
        r"registration|website)\b|$)",

        r"\beligibility\s+(?:is|includes)\s+(.+?)"
        r"(?=[.!?](?:\s|$)|"
        r"\s+(?:ctc|stipend|salary|deadline|last date|"
        r"registration|website)\b|$)",

        r"\bcandidates\s+must\s+be\s+(.+?)"
        r"(?=[.!?](?:\s|$)|"
        r"\s+(?:ctc|stipend|salary|deadline|last date|"
        r"registration|website)\b|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        result = clean(match.group(1))

        result = stop_at_next_field(result)

        if valid_eligibility(result):
            return result

    return ""


# ============================================================
# MAIN EXTRACTOR
# ============================================================

def extract_eligibility(text: str) -> str:

    if not text:
        return ""

    text = clean(text)

    # --------------------------------------------------------
    # 1. Explicit labelled eligibility
    # --------------------------------------------------------

    labels = [
        "Eligibility Criteria",
        "Eligible Criteria",
        "Eligibility",
    ]

    for label in labels:

        result = extract_labelled_block(
            text,
            label,
        )

        if result:
            return result

    # --------------------------------------------------------
    # 2. VIT-style eligibility block
    # --------------------------------------------------------

    result = extract_vit_style_eligibility(text)

    if result:
        return result

    # --------------------------------------------------------
    # 3. Natural language eligibility
    # --------------------------------------------------------

    result = extract_natural_eligibility(text)

    if result:
        return result

    return ""

