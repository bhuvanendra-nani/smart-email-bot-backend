
import re


# ============================================================
# KNOWN COMPANIES
# ============================================================

KNOWN_COMPANIES = [
    "Urban Company",
    "Unthinkable",
    "Smart Data Solutions",
    "Myntra",
    "Apple",
    "Tekion",
    "Sabre",
    "Bosch",
    "Zomato",
    "Odoo",
    "KLA",
    "IDFC FIRST Bank",
    "IDFC First Bank",
    "Mondelez International",
    "WorkIndia",
    "Foodbuddies",
    "SATVEN",
    "UNIQCORE CONSTRUCTION",
    "Pixel Compute",
    "Google",
    "Microsoft",
    "Amazon",
    "Flipkart",
    "Adobe",
    "Oracle",
    "Intel",
    "NVIDIA",
    "Qualcomm",
    "Cisco",
    "Accenture",
    "Deloitte",
    "Infosys",
    "TCS",
    "Wipro",
    "Cognizant",
    "Capgemini",
    "IBM",
    "HCL",
]


# ============================================================
# GENERIC WORDS THAT MUST NEVER BE A COMPANY NAME
# ============================================================

INVALID_COMPANY_NAMES = {
    "company",
    "organization",
    "employer",
    "client",
    "team",
    "hr",
    "recruitment team",
    "placement team",
    "talent acquisition",
    "human resources",
    "congratulations",
    "dream",
    "super dream",
}


# ============================================================
# SUBJECT / EMAIL NOISE
# ============================================================

SUBJECT_NOISE = [
    r"^re\s*:\s*",
    r"^fw\s*:\s*",
    r"^fwd\s*:\s*",
    r"^forwarded\s*:\s*",
    r"^reminder\s*:\s*",
    r"^urgent\s*:\s*",
    r"^important\s*:\s*",
    r"^congratulations\s*!*\s*",
    r"^congratulation\s*!*\s*",
]


# ============================================================
# TEXT CLEANING
# ============================================================

def clean(text: str) -> str:

    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"https?://\S+", " ", text)

    replacements = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": "...",
        "Ã©": "é",
        "Ã‰": "É",
        "Ã¡": "á",
        "Ã³": "ó",
        "Ãº": "ú",
        "Â": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# REMOVE SUBJECT DECORATION
# ============================================================

def clean_subject_prefix(subject: str) -> str:

    subject = clean(subject)

    previous = None

    while subject != previous:
        previous = subject

        for pattern in SUBJECT_NOISE:
            subject = re.sub(
                pattern,
                "",
                subject,
                flags=re.IGNORECASE,
            )

    return subject.strip()


# ============================================================
# VALIDATE COMPANY
# ============================================================

def is_valid_company(company: str) -> bool:

    if not company:
        return False

    company = clean(company).strip(" :-|.,;!*")

    if not company:
        return False

    if len(company) < 2 or len(company) > 80:
        return False

    if company.lower() in INVALID_COMPANY_NAMES:
        return False

    if len(company.split()) > 8:
        return False

    invalid_words = [
        "role:",
        "position:",
        "eligibility:",
        "deadline:",
        "location:",
        "branches:",
        "batch:",
        "ctc:",
        "stipend:",
        "salary:",
        "registration:",
        "description:",
        "process:",
        "venue:",
        "mode:",
        "contact:",
        "action:",
    ]

    company_lower = company.lower()

    if any(word in company_lower for word in invalid_words):
        return False

    if company.endswith((".", "!", "?")):
        return False

    return True


# ============================================================
# NORMALIZE COMPANY
# ============================================================

def normalize_company(company: str) -> str:

    if not company:
        return ""

    company = clean(company)

    # --------------------------------------------------------
    # Remove common labels
    # --------------------------------------------------------

    company = re.sub(
        r"^(company|organization|employer|client|company name|"
        r"name of the company)\s*[:\-]\s*",
        "",
        company,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Remove subject decoration
    # --------------------------------------------------------

    company = re.sub(
        r"^congratulations\s*!*\s*",
        "",
        company,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Remove common recruitment suffixes
    #
    # IMPORTANT:
    # "Super Dream" / "Dream" are not company names.
    # --------------------------------------------------------

    company = re.sub(
        r"\s+(super\s+dream|dream)\s*$",
        "",
        company,
        flags=re.IGNORECASE,
    )

    company = re.sub(
        r"\s+(internship|placement|recruitment|hiring|"
        r"drive|opportunity|opening|selection|"
        r"registration|assessment|test|interview)\s*$",
        "",
        company,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Remove common punctuation
    # --------------------------------------------------------

    company = company.strip(" :-|.,;!*")

    # --------------------------------------------------------
    # Stop at another field
    # --------------------------------------------------------

    company = re.split(
        r"\s+(?="
        r"role|position|profile|location|eligibility|deadline|"
        r"branches|batch|ctc|stipend|salary|registration|"
        r"process|venue|mode|contact|action|description"
        r"\s*[:\-])",
        company,
        flags=re.IGNORECASE,
    )[0]

    company = company.strip(" :-|.,;!*")

    if not is_valid_company(company):
        return ""

    return company


# ============================================================
# FIND KNOWN COMPANY
# ============================================================

def find_known_company(text: str) -> str:

    if not text:
        return ""

    text = clean(text)

    companies = sorted(
        KNOWN_COMPANIES,
        key=len,
        reverse=True,
    )

    for company in companies:

        pattern = (
            rf"(?<![A-Za-z0-9])"
            rf"{re.escape(company)}"
            rf"(?![A-Za-z0-9])"
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return company

    return ""


# ============================================================
# EXPLICIT COMPANY FIELD
# ============================================================

def extract_explicit_company(text: str) -> str:

    if not text:
        return ""

    text = clean(text)

    patterns = [

        r"\bname\s+of\s+the\s+company\s*[:\-]\s*([^|\n]{2,100})",

        r"\bcompany\s+name\s*[:\-]\s*([^|\n]{2,100})",

        r"\bcompany\s*[:\-]\s*([^|\n]{2,100})",

        r"\bemployer\s*[:\-]\s*([^|\n]{2,100})",

        r"\borganization\s*[:\-]\s*([^|\n]{2,100})",

        r"\bclient\s*[:\-]\s*([^|\n]{2,100})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        candidate = match.group(1)

        candidate = re.split(
            r"\s+(?="
            r"role|position|profile|location|eligibility|deadline|"
            r"branches|batch|ctc|stipend|salary|registration|"
            r"process|venue|mode|contact|action|description"
            r"\s*[:\-])",
            candidate,
            flags=re.IGNORECASE,
        )[0]

        candidate = normalize_company(candidate)

        if not candidate:
            continue

        known = find_known_company(candidate)

        if known:
            return known

        return candidate

    return ""


# ============================================================
# COMPANY FROM SUBJECT
# ============================================================

def extract_company_from_subject(subject: str) -> str:

    subject = clean_subject_prefix(subject)

    if not subject:
        return ""

    # --------------------------------------------------------
    # Explicit company field
    # --------------------------------------------------------

    company = extract_explicit_company(subject)

    if company:
        return company

    # --------------------------------------------------------
    # Known company in subject
    # --------------------------------------------------------

    company = find_known_company(subject)

    if company:
        return company

    # --------------------------------------------------------
    # Remove common subject prefixes
    # --------------------------------------------------------

    working = subject

    # --------------------------------------------------------
    # IMPORTANT:
    # Remove "Super Dream", "Dream", and "2027 batch"
    # before generic extraction.
    # --------------------------------------------------------

    working = re.sub(
        r"\b(super\s+dream|dream)\b",
        " ",
        working,
        flags=re.IGNORECASE,
    )

    working = re.sub(
        r"\b20(?:20|21|22|23|24|25|26|27|28|29|30|31|32|33|34|35)\b",
        " ",
        working,
    )

    working = re.sub(
        r"\bbatch\b",
        " ",
        working,
        flags=re.IGNORECASE,
    )

    working = re.sub(
        r"\s+",
        " ",
        working,
    ).strip()

    # --------------------------------------------------------
    # Generic subject patterns
    # --------------------------------------------------------

    patterns = [

        r"^(.{2,60}?)\s*\|\s*"
        r"(?:internship|placement|assessment|test|hiring|"
        r"recruitment|drive|selection|interview|registration)\b",

        r"^(.{2,60}?)\s*[-:]\s*"
        r"(?:internship|placement|assessment|test|hiring|"
        r"recruitment|drive|selection|interview|registration)\b",

        r"^(.{2,60}?)\s+"
        r"(?:internship|placement|recruitment|hiring|drive|"
        r"assessment|selection|interview|registration)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            working,
            re.IGNORECASE,
        )

        if not match:
            continue

        candidate = normalize_company(
            match.group(1)
        )

        if not candidate:
            continue

        known = find_known_company(candidate)

        if known:
            return known

        return candidate

    return ""


# ============================================================
# COMPANY FROM BODY
# ============================================================

def extract_company_from_body(body: str) -> str:

    body = clean(body)

    if not body:
        return ""

    # --------------------------------------------------------
    # 1. Explicit company field
    # --------------------------------------------------------

    company = extract_explicit_company(body)

    if company:
        return company

    # --------------------------------------------------------
    # 2. Strong sentence patterns
    # --------------------------------------------------------

    patterns = [

        r"\b(?:we are|we're|welcome to|join)\s+"
        r"([A-Z][A-Za-z0-9&.,'()\- ]{2,60}?)"
        r"\s+(?:for|as|at)\b",

        r"\b([A-Z][A-Za-z0-9&.,'()\- ]{2,60}?)"
        r"\s+is\s+(?:hiring|recruiting)\b",

        r"\b([A-Z][A-Za-z0-9&.,'()\- ]{2,60}?)"
        r"\s+(?:internship|placement|recruitment|"
        r"hiring)\s+(?:opportunity|drive|program)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            body,
            re.IGNORECASE,
        )

        if not match:
            continue

        candidate = normalize_company(
            match.group(1)
        )

        if not candidate:
            continue

        known = find_known_company(candidate)

        if known:
            return known

        if len(candidate.split()) <= 6:
            return candidate

    return ""


# ============================================================
# MAIN COMPANY EXTRACTOR
# ============================================================

def extract_company(subject, body):

    subject = subject or ""
    body = body or ""

    if not clean(subject) and not clean(body):
        return ""

    # --------------------------------------------------------
    # 1. Subject
    # --------------------------------------------------------

    company = extract_company_from_subject(subject)

    if company:
        return company

    # --------------------------------------------------------
    # 2. Body
    # --------------------------------------------------------

    company = extract_company_from_body(body)

    if company:
        return company

    # --------------------------------------------------------
    # Nothing reliable found
    # --------------------------------------------------------

    return ""

