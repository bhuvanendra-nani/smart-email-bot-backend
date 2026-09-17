import re


# ============================================================
# COMMON ROLES
# ============================================================

COMMON_ROLES = [
    "Software Development Engineer in Test",
    "Software Development Engineer",
    "Associate Software Engineer",
    "Graduate Engineer Trainee",
    "Graduate Trainee Engineer",
    "Software Engineer Intern",
    "Software Engineer",
    "Software Developer",
    "Developer Intern",
    "Product Management Intern",
    "Product Manager Intern",
    "Product Management",
    "SDET Intern",
    "SDET",
    "SDE Intern",
    "SDE",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "Python Developer",
    "Java Developer",
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "AI Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "QA Engineer",
    "Test Engineer",
    "Business Analyst",
    "Cyber Security Engineer",
    "Embedded Engineer",
    "System Engineer",
]


# ============================================================
# FIELD LABELS
# ============================================================

FIELD_LABELS = (
    r"company|organization|employer|location|eligibility|"
    r"eligible branches|branches|departments|batch|ctc|stipend|"
    r"salary|deadline|last date|registration|registration link|"
    r"venue|mode|process|contact|action|description|"
    r"additional details|selection|selection process|"
    r"selection procedure|website"
)


ROLE_LABELS = [
    "job role",
    "role",
    "position",
    "profile",
    "designation",
    "job title",
    "opening",
]


# ============================================================
# CLEAN
# ============================================================

def clean(text: str) -> str:

    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(r"https?://\S+", " ", text)

    # Fix common encoding corruption
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "Â": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove markdown emphasis
    text = text.replace("**", " ")
    text = text.replace("__", " ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# NORMALIZE ROLE
# ============================================================

def normalize_role(role: str) -> str:

    if not role:
        return ""

    role = clean(role)

    # Remove leading markdown characters
    role = role.strip(" *:-|,.;")

    # Remove labels from beginning
    role = re.sub(
        r"^(?:job\s+role|role|position|profile|designation|"
        r"job\s+title|opening)\s*[:\-]?\s*",
        "",
        role,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Stop at another field
    # --------------------------------------------------------

    role = re.split(
        rf"\s+(?=(?:{FIELD_LABELS})\s*[:\-])",
        role,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Stop at markdown-style field
    role = re.split(
        rf"\s+(?=\*?\s*(?:{FIELD_LABELS})\s*\*?\s*[:\-])",
        role,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Stop at common Myntra-style additional information
    role = re.split(
        r"\s+\*?\s*(?:Additional Details|Selection|"
        r"Eligibility|CTC|Stipend|Location|Branches)\b",
        role,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Remove trailing markdown
    role = role.strip(" *:-|,.;")

    # Reject obviously huge garbage
    if len(role) > 100:
        return ""

    if len(role.split()) > 12:
        return ""

    return role


# ============================================================
# FIND KNOWN ROLE
# ============================================================

def find_known_role(text: str) -> str:
    """
    Find a known role in a limited text block.

    Longer/more specific roles are checked first.
    """

    if not text:
        return ""

    text = clean(text)

    roles = sorted(
        COMMON_ROLES,
        key=len,
        reverse=True,
    )

    for role in roles:

        pattern = (
            rf"(?<![A-Za-z0-9])"
            rf"{re.escape(role)}"
            rf"(?![A-Za-z0-9])"
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return role

    return ""


# ============================================================
# EXPLICIT ROLE
# ============================================================

def extract_explicit_role(text: str) -> str:
    """
    Extract roles from explicit labels.

    Examples:
        Role: SDET
        Position: Software Engineer
        Job Role: Backend Developer
        Profile: Data Analyst
    """

    if not text:
        return ""

    text = clean(text)

    for label in ROLE_LABELS:

        pattern = rf"""
            \b{re.escape(label)}\b
            \s*[:\-]?\s*
            (.+?)
            (?=
                \s+(?:{FIELD_LABELS})\s*[:\-]
                |
                \s+\*?\s*(?:{FIELD_LABELS})\s*\*?\s*
                |
                $
            )
        """

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.VERBOSE,
        )

        if not match:
            continue

        value = normalize_role(
            match.group(1)
        )

        if not value:
            continue

        # Prefer canonical role
        known = find_known_role(value)

        if known:
            return known

        # Accept short explicit role
        if (
            len(value) <= 80
            and len(value.split()) <= 10
        ):
            return value

    return ""


# ============================================================
# HIRING PHRASE
# ============================================================

def extract_hiring_phrase(text: str) -> str:
    """
    Extract roles from phrases such as:

        Hiring for Software Engineer
        Opening for Backend Developer
        Looking for a Software Engineer
    """

    if not text:
        return ""

    text = clean(text)

    patterns = [
        rf"\bhiring\s+for\s+(?:a|an)?\s*(.+?)"
        rf"(?=\s+(?:{FIELD_LABELS})\s*[:\-]|[.!?]|$)",

        rf"\bopening\s+for\s+(?:a|an)?\s*(.+?)"
        rf"(?=\s+(?:{FIELD_LABELS})\s*[:\-]|[.!?]|$)",

        rf"\blooking\s+for\s+(?:a|an)?\s*(.+?)"
        rf"(?=\s+(?:{FIELD_LABELS})\s*[:\-]|[.!?]|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = normalize_role(
            match.group(1)
        )

        if not value:
            continue

        known = find_known_role(value)

        if known:
            return known

        if (
            len(value) <= 80
            and len(value.split()) <= 10
        ):
            return value

    return ""


# ============================================================
# ROLE OF ...
# ============================================================

def extract_role_of(text: str) -> str:

    if not text:
        return ""

    text = clean(text)

    patterns = [
        r"\brole\s+of\s+(.+?)(?=[.!?,]|$)",
        r"\bposition\s+of\s+(.+?)(?=[.!?,]|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = normalize_role(
            match.group(1)
        )

        if not value:
            continue

        known = find_known_role(value)

        if known:
            return known

        if (
            len(value) <= 80
            and len(value.split()) <= 10
        ):
            return value

    return ""


# ============================================================
# MAIN EXTRACTOR
# ============================================================

def extract_role(subject: str, body: str) -> str:
    """
    Extract the primary hiring role.

    Priority:

    1. Explicit role in subject
    2. Known role in subject
    3. Hiring/opening phrase in subject
    4. Explicit role in body
    5. Hiring/opening phrase in body
    6. Known role in carefully selected body lines
    7. role of / position of

    Never blindly scans the complete body for arbitrary text.
    """

    subject = clean(subject or "")
    body = clean(body or "")

    if not subject and not body:
        return ""

    # --------------------------------------------------------
    # 1. Explicit role in SUBJECT
    # --------------------------------------------------------

    role = extract_explicit_role(subject)

    if role:
        return role

    # --------------------------------------------------------
    # 2. Known role in SUBJECT
    # --------------------------------------------------------

    role = find_known_role(subject)

    if role:
        return role

    # --------------------------------------------------------
    # 3. Hiring/opening phrase in SUBJECT
    # --------------------------------------------------------

    role = extract_hiring_phrase(subject)

    if role:
        return role

    # --------------------------------------------------------
    # 4. Explicit role in BODY
    # --------------------------------------------------------

    role = extract_explicit_role(body)

    if role:
        return role

    # --------------------------------------------------------
    # 5. Hiring/opening phrase in BODY
    # --------------------------------------------------------

    role = extract_hiring_phrase(body)

    if role:
        return role

    # --------------------------------------------------------
    # 6. Carefully inspect relevant body lines
    # --------------------------------------------------------

    lines = body.splitlines()

    for line in lines:

        line = clean(line)

        if not line:
            continue

        lower = line.lower()

        if not any(
            keyword in lower
            for keyword in [
                "role",
                "position",
                "designation",
                "job title",
                "profile",
                "opening",
                "hiring",
                "vacancy",
            ]
        ):
            continue

        role = find_known_role(line)

        if role:
            return role

    # --------------------------------------------------------
    # 7. Role of / Position of
    # --------------------------------------------------------

    role = extract_role_of(subject)

    if role:
        return role

    role = extract_role_of(body)

    if role:
        return role

    return ""