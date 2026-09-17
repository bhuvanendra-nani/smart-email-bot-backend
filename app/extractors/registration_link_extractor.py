import re
from urllib.parse import urlparse


PREFERRED_DOMAINS = [
    "superset",
    "unstop",
    "hackerrank",
    "hirepro",
    "mettl",
    "forms.gle",
    "docs.google.com/forms",
    "google.com/forms",
    "odoo",
    "idfcfirstbank",
    "bosch",
    "tekion",
    "zomato",
]


REGISTRATION_KEYWORDS = [
    "register",
    "registration",
    "apply",
    "application",
    "applynow",
    "apply-now",
    "signup",
    "sign-up",
    "enroll",
    "assessment",
    "test",
    "drive",
]


IGNORE_PATTERNS = [
    "unsubscribe",
    "privacy",
    "terms",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "youtube.com",
    "mailto:",
]


def clean_url(url: str) -> str:
    if not url:
        return ""

    url = url.strip()

    # Remove common punctuation attached to URLs
    url = url.rstrip(".,;:!?)]}>\"'")

    return url


def is_valid_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.netloc:
            return False

        return True

    except Exception:
        return False


def is_ignored_url(url: str) -> bool:
    lower = url.lower()

    for pattern in IGNORE_PATTERNS:
        if pattern in lower:
            return True

    return False


def score_link(url: str) -> int:
    """
    Give registration links a relevance score.

    Higher score = more likely to be the actual
    application/registration link.
    """

    lower = url.lower()

    if is_ignored_url(url):
        return -100

    score = 0

    # Strong portal matches
    for domain in PREFERRED_DOMAINS:
        if domain.lower() in lower:
            score += 50

    # Registration-related URL text
    for keyword in REGISTRATION_KEYWORDS:
        if keyword in lower:
            score += 15

    # Common Google forms
    if "forms.gle" in lower:
        score += 60

    if "docs.google.com/forms" in lower:
        score += 60

    return score


def extract_registration_link(text: str) -> str:
    """
    Extract the most relevant registration/application link.

    Priority:
    1. Known registration portals
    2. Links containing registration/apply keywords
    3. Other valid URLs as a last resort
    """

    if not text:
        return ""

    # Extract URLs
    links = re.findall(
        r'https?://[^\s<>"]+',
        text,
        flags=re.IGNORECASE,
    )

    if not links:
        return ""

    # Clean and validate
    valid_links = []

    for link in links:
        link = clean_url(link)

        if not is_valid_url(link):
            continue

        if is_ignored_url(link):
            continue

        if link not in valid_links:
            valid_links.append(link)

    if not valid_links:
        return ""

    # --------------------------------------------------
    # 1. Score all links
    # --------------------------------------------------

    scored_links = [
        (score_link(link), index, link)
        for index, link in enumerate(valid_links)
    ]

    scored_links.sort(
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )

    best_score, _, best_link = scored_links[0]

    # Only return a strongly relevant link
    if best_score > 0:
        return best_link

    # --------------------------------------------------
    # 2. Conservative fallback
    # --------------------------------------------------
    #
    # Do not blindly return random URLs.
    # If the email contains only unrelated URLs,
    # return nothing.
    # --------------------------------------------------

    return ""