import re


# ============================================================
# KNOWN BRANCHES
# ============================================================

KNOWN_BRANCHES = [
    "Computer Science & Engineering",
    "Computer Science and Engineering",
    "Computer Science",
    "Information Technology",
    "Electronics and Communication Engineering",
    "Electronics and Communication",
    "Electrical and Electronics Engineering",
    "Electrical and Electronics",
    "Artificial Intelligence and Machine Learning",
    "Artificial Intelligence",
    "Data Science",
    "Mechanical Engineering",
    "Mechanical",
    "Civil Engineering",
    "Civil",
    "Biotechnology",
    "Chemical Engineering",
    "Chemical",
    "Computer Engineering",
    "CSE",
    "IT",
    "ECE",
    "EEE",
    "AI & ML",
    "AI/ML",
    "AI ML",
    "AI",
    "ML",
    "MCA",
    "All Branches",
    "All Branch",
    "All Engineering Branches",
]


# ============================================================
# INVALID / STOP LABELS
# ============================================================

STOP_LABELS = [
    "eligibility criteria",
    "eligibility",
    "ctc",
    "salary",
    "stipend",
    "package",
    "job location",
    "location",
    "venue",
    "registration",
    "registration link",
    "apply link",
    "application link",
    "website",
    "last date",
    "deadline",
    "date",
    "batch",
    "role",
    "designation",
    "position",
    "job description",
    "description",
    "process",
    "selection process",
    "contact",
    "email",
    "phone",
    "remarks",
]


# ============================================================
# CLEAN
# ============================================================

def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML if any.
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# NORMALIZE BRANCH NAME
# ============================================================

def normalize_branch(branch: str) -> str:
    if not branch:
        return ""

    branch = clean(branch)

    # Normalize common variations.
    normalized = branch.lower()

    aliases = {
        "computer science and engineering": "CSE",
        "computer science & engineering": "CSE",
        "computer science": "CSE",
        "cse": "CSE",

        "information technology": "IT",
        "it": "IT",

        "electronics and communication engineering": "ECE",
        "electronics and communication": "ECE",
        "ece": "ECE",

        "electrical and electronics engineering": "EEE",
        "electrical and electronics": "EEE",
        "eee": "EEE",

        "mechanical engineering": "Mechanical",
        "mechanical": "Mechanical",

        "civil engineering": "Civil",
        "civil": "Civil",

        "artificial intelligence and machine learning": "AI & ML",
        "artificial intelligence": "AI",
        "ai & ml": "AI & ML",
        "ai/ml": "AI & ML",
        "ai ml": "AI & ML",
        "ai": "AI",

        "machine learning": "ML",
        "ml": "ML",

        "data science": "Data Science",

        "biotechnology": "Biotechnology",

        "chemical engineering": "Chemical",
        "chemical": "Chemical",

        "computer engineering": "Computer Engineering",

        "mca": "MCA",

        "all branches": "All Branches",
        "all branch": "All Branches",
        "all engineering branches": "All Engineering Branches",
    }

    return aliases.get(
        normalized,
        branch,
    )


# ============================================================
# VALIDATE BRANCH BLOCK
# ============================================================

def valid_branch_block(block: str) -> bool:
    """
    Prevent the extractor from returning an entire email body.

    A valid branch result should be short and should contain
    at least one recognizable branch.
    """

    if not block:
        return False

    block = clean(block)

    # Hard length limit.
    if len(block) > 250:
        return False

    # Too many words usually means we captured email content.
    if len(block.split()) > 30:
        return False

    # Must contain at least one known branch.
    lower = block.lower()

    if not any(
        branch.lower() in lower
        for branch in KNOWN_BRANCHES
    ):
        return False

    return True


# ============================================================
# EXTRACT LABELLED BRANCH BLOCK
# ============================================================

def extract_labelled_block(text: str) -> str:
    """
    Extract branches from explicit labels such as:

        Eligible Branches: CSE, ECE
        Branches: CSE
        Eligible Departments: CSE, IT
        Eligible Branch: All Branches
    """

    if not text:
        return ""

    # Work line-by-line first.
    # This prevents one missing stop label from swallowing
    # the entire email.
    lines = text.splitlines()

    labels = [
        r"eligible\s+branches?",
        r"eligible\s+departments?",
        r"eligible\s+streams?",
        r"eligible\s+courses?",
        r"branches?",
        r"departments?",
        r"streams?",
    ]

    label_pattern = "|".join(labels)

    for index, line in enumerate(lines):

        line = line.strip()

        if not line:
            continue

        match = re.search(
            rf"^(?:{label_pattern})\s*[:\-]\s*(.+)$",
            line,
            re.IGNORECASE,
        )

        if not match:
            continue

        block = match.group(1).strip()

        # If the value is on the next line, include it.
        if not block and index + 1 < len(lines):
            block = lines[index + 1].strip()

        # Stop at another field label.
        block = re.split(
            r"\b(?:"
            + "|".join(
                re.escape(label)
                for label in STOP_LABELS
            )
            + r")\b\s*[:\-]?",
            block,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        block = clean(block)

        if valid_branch_block(block):
            return block

    return ""


# ============================================================
# EXTRACT BRANCHES FROM INLINE SENTENCES
# ============================================================

def extract_sentence_branches(text: str) -> str:
    """
    Detect common natural-language forms:

        Eligible for CSE and ECE students
        Open to CSE students
        Applicable to all branches
        Students from CSE, IT and ECE can apply
    """

    if not text:
        return ""

    patterns = [

        r"(?:eligible|eligibility)\s+(?:for|to)\s+"
        r"(.{2,150}?)"
        r"(?:students?|candidates?|graduates?)\b",

        r"(?:open|available)\s+to\s+"
        r"(.{2,150}?)"
        r"(?:students?|candidates?)\b",

        r"(?:applicable|restricted)\s+to\s+"
        r"(.{2,150}?)"
        r"(?:students?|candidates?)\b",

        r"(?:students?|candidates?)\s+from\s+"
        r"(.{2,150}?)"
        r"(?:can|may|are)\s+(?:apply|register|participate)",

    ]

    for pattern in patterns:

        matches = re.finditer(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:

            block = clean(
                match.group(1)
            )

            if not block:
                continue

            # Remove unnecessary connecting words.
            block = re.sub(
                r"\b(?:the|following|all)\b",
                " ",
                block,
                flags=re.IGNORECASE,
            )

            block = clean(block)

            # Find only recognized branches in this small block.
            found = find_known_branches(block)

            if found:
                return found

    return ""


# ============================================================
# FIND KNOWN BRANCHES
# ============================================================

def find_known_branches(text: str) -> str:
    """
    Find recognizable branch names.

    Unlike the old extractor, this returns only canonical branch
    names rather than the complete surrounding sentence.
    """

    if not text:
        return ""

    text = clean(text)

    found = []

    # Longest names first.
    branches = sorted(
        KNOWN_BRANCHES,
        key=len,
        reverse=True,
    )

    for branch in branches:

        pattern = (
            rf"(?<![A-Za-z0-9])"
            rf"{re.escape(branch)}"
            rf"(?![A-Za-z0-9])"
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):

            canonical = normalize_branch(branch)

            if canonical not in found:
                found.append(canonical)

    # If "All Branches" is present, it is sufficient.
    if "All Branches" in found:
        return "All Branches"

    if "All Engineering Branches" in found:
        return "All Engineering Branches"

    return ", ".join(found)


# ============================================================
# MAIN EXTRACTOR
# ============================================================

def extract_branches(text: str) -> str:
    """
    Extract eligible academic branches safely.

    Priority:

    1. Explicit labelled branch field
    2. Natural-language eligibility sentence
    3. Very conservative branch detection

    The final fallback is intentionally restricted to avoid
    detecting CSE/ECE/etc. from unrelated parts of the email.
    """

    if not text:
        return ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # --------------------------------------------------------
    # 1. Explicit branch field
    # --------------------------------------------------------

    result = extract_labelled_block(text)

    if result:
        return result

    # --------------------------------------------------------
    # 2. Natural-language eligibility
    # --------------------------------------------------------

    result = extract_sentence_branches(text)

    if result:
        return result

    # --------------------------------------------------------
    # 3. Conservative fallback
    #
    # Only inspect short windows around eligibility-related
    # words. Do NOT scan the entire email blindly.
    # --------------------------------------------------------

    lines = text.splitlines()

    for index, line in enumerate(lines):

        lower = line.lower()

        if not any(
            word in lower
            for word in [
                "eligib",
                "branch",
                "department",
                "stream",
            ]
        ):
            continue

        window_lines = lines[
            max(0, index - 1):
            min(len(lines), index + 3)
        ]

        window = " ".join(window_lines)

        result = find_known_branches(window)

        if result:
            return result

    return ""