import re


def clean_text(text: str) -> str:
    """
    Remove extra spaces, tabs and newlines.
    """
    return re.sub(r"\s+", " ", text or "").strip()


def shorten_text(text: str, max_len: int = 40) -> str:
    """
    Shorten long text for display.
    """
    text = clean_text(text)

    if len(text) <= max_len:
        return text

    return text[: max_len - 3] + "..."


def extract_date(text: str) -> str:
    """
    Extract date from email text using regex.
    Returns 'Not mentioned' if no date is found.
    """

    if not text:
        return "Not mentioned"

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        r"\b\d{1,2}(st|nd|rd|th)?\s+"
        r"(Jan|January|Feb|February|Mar|March|Apr|April|May|June|Jun|"
        r"July|Jul|August|Aug|September|Sep|October|Oct|November|Nov|"
        r"December|Dec)\s+\d{2,4}\b",

        r"\b(Jan|January|Feb|February|Mar|March|Apr|April|May|June|Jun|"
        r"July|Jul|August|Aug|September|Sep|October|Oct|November|Nov|"
        r"December|Dec)\s+\d{1,2},?\s+\d{2,4}\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0)

    return "Not mentioned"


def normalize_type(task_type: str) -> str:
    """
    Normalize task names into standard categories.
    """

    task = clean_text(task_type).lower()

    mapping = {
        "ppt": "PPT",
        "slides": "PPT",
        "slide": "PPT",
        "presentation": "PPT",

        "lab": "Lab",
        "laboratory": "Lab",
        "practical": "Lab",

        "lab assignment": "Lab Assignment",
        "record work": "Lab Assignment",
        "lab record": "Lab Assignment",

        "marks": "Marks Update",
        "mark": "Marks Update",
        "marks update": "Marks Update",
        "result update": "Marks Update",
        "grade": "Marks Update",
        "grades": "Marks Update",
        "score updated": "Marks Update",

        "quiz": "Quiz",
        "assignment": "Assignment",
        "notes": "Notes",
        "internship": "Internship",
        "placement": "Placement",
        "online test": "Online Test",
        "test": "Test",
        "other": "Other",
    }

    return mapping.get(task, task_type)