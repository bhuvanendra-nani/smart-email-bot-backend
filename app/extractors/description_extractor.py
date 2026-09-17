import re


FIELD_LABELS = [
    "company",
    "role",
    "eligibility",
    "branches",
    "batch",
    "ctc",
    "stipend",
    "deadline",
    "last date",
    "registration",
    "registration link",
    "venue",
    "location",
    "mode",
    "process",
    "contact",
    "action",
]


def clean(text: str) -> str:
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(r"https?://\S+", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def remove_email_noise(text: str) -> str:
    """
    Remove common email noise from the beginning/end.
    """

    # Remove common greetings
    text = re.sub(
        r"^(dear\s+(students|all|candidate|candidates|sir|madam)[,:\-]?\s*)",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove common sign-offs
    text = re.split(
        r"\b(?:regards|best regards|thanks|thank you|sincerely)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return text.strip()


def remove_field_blocks(text: str) -> str:
    """
    Remove long structured metadata sections so that the
    description contains useful natural-language information.
    """

    pattern = (
        r"\b(?:"
        + "|".join(re.escape(label) for label in FIELD_LABELS)
        + r")\s*[:\-]\s*[^.]{0,150}"
    )

    text = re.sub(
        pattern,
        " ",
        text,
        flags=re.IGNORECASE,
    )

    return re.sub(r"\s+", " ", text).strip()


def extract_description(text: str, max_length: int = 250) -> str:
    if not text:
        return ""

    text = clean(text)

    if not text:
        return ""

    # Remove common email noise
    text = remove_email_noise(text)

    # Split into sentences
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    useful_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        # Skip very short fragments
        if len(sentence) < 20:
            continue

        # Skip obvious metadata-only lines
        lowered = sentence.lower()

        if any(
            re.match(
                rf"^{re.escape(label)}\s*[:\-]",
                lowered,
            )
            for label in FIELD_LABELS
        ):
            continue

        useful_sentences.append(sentence)

    # Prefer the first useful natural-language sentences
    if useful_sentences:
        description = " ".join(useful_sentences[:3])
    else:
        description = text

    # Remove remaining obvious field blocks
    description = remove_field_blocks(description)

    description = re.sub(r"\s+", " ", description).strip()

    if not description:
        return ""

    if len(description) <= max_length:
        return description

    # Cut at the nearest word boundary
    description = description[:max_length]

    if " " in description:
        description = description.rsplit(" ", 1)[0]

    return description.rstrip(".,;:- ") + "..."