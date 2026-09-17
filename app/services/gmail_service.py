import base64
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.services.classifier_service import rule_based_classify


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():
    creds = Credentials.from_authorized_user_file(
        "credentials/token.json",
        GMAIL_SCOPES,
    )

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )


# ============================================================
# HEADER HELPERS
# ============================================================

def get_header(headers, name):
    """
    Get a Gmail header value safely.
    """

    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


# ============================================================
# BASE64 DECODER
# ============================================================

def decode_base64(data):
    """
    Decode Gmail URL-safe base64 content.
    """

    if not data:
        return ""

    try:
        # Gmail sometimes removes padding.
        data += "=" * (-len(data) % 4)

        return base64.urlsafe_b64decode(
            data.encode("utf-8")
        ).decode(
            "utf-8",
            errors="ignore",
        )

    except Exception:
        return ""


# ============================================================
# TEXT CLEANING
# ============================================================

def normalize_newlines(text):
    """
    Normalize different newline formats.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    return text


def clean_text(text):
    """
    Basic whitespace cleanup.
    """

    if not text:
        return ""

    text = normalize_newlines(text)

    # Remove null characters.
    text = text.replace("\x00", "")

    # Remove excessive spaces.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# REMOVE HTML
# ============================================================

def remove_html(text):
    """
    Basic HTML-to-text cleanup.
    Used only as a fallback when plain text isn't available.
    """

    if not text:
        return ""

    # Remove script/style blocks.
    text = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert common block tags to newlines.
    text = re.sub(
        r"<(br|/p|/div|/tr|/li|/h[1-6])[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # Remove remaining HTML tags.
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Decode a few common HTML entities.
    replacements = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return clean_text(text)


# ============================================================
# FIND BODY PARTS
# ============================================================

def collect_body_parts(payload):
    """
    Recursively collect email body parts.

    Returns:
        {
            "plain": [...],
            "html": [...]
        }
    """

    result = {
        "plain": [],
        "html": [],
    }

    if not payload:
        return result

    mime_type = payload.get("mimeType", "").lower()

    body = payload.get("body", {})
    data = body.get("data", "")

    if data:
        decoded = decode_base64(data)

        if decoded:
            if mime_type == "text/plain":
                result["plain"].append(decoded)

            elif mime_type == "text/html":
                result["html"].append(decoded)

    for part in payload.get("parts", []):
        child_result = collect_body_parts(part)

        result["plain"].extend(
            child_result["plain"]
        )

        result["html"].extend(
            child_result["html"]
        )

    return result


# ============================================================
# REMOVE QUOTED / REPLIED CONTENT
# ============================================================

def remove_quoted_content(text):
    """
    Remove old replies, forwarded messages and quoted email chains.

    This is extremely important because placement emails often
    contain previous unrelated content after the current message.
    """

    if not text:
        return ""

    text = normalize_newlines(text)

    lines = text.split("\n")

    cleaned_lines = []

    # Patterns that usually indicate the beginning of
    # an old/replied/forwarded email.
    reply_start_patterns = [
        r"^\s*On .+wrote:\s*$",
        r"^\s*On .+ at .+wrote:\s*$",
        r"^\s*From:\s*.+$",
        r"^\s*Sent:\s*.+$",
        r"^\s*To:\s*.+$",
        r"^\s*Cc:\s*.+$",
        r"^\s*Subject:\s*.+$",
        r"^\s*-----Original Message-----\s*$",
        r"^\s*Begin forwarded message:\s*$",
        r"^\s*Forwarded message\s*$",
        r"^\s*---------- Forwarded message ----------\s*$",
    ]

    for line in lines:

        stripped = line.strip()

        # Stop completely when an old email starts.
        should_stop = False

        for pattern in reply_start_patterns:
            if re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            ):
                should_stop = True
                break

        if should_stop:
            break

        # Gmail quoted lines usually start with ">"
        if stripped.startswith(">"):
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    return clean_text(text)


# ============================================================
# REMOVE SIGNATURE / EMAIL FOOTER
# ============================================================

def remove_signature(text):
    """
    Remove common email signatures and footer content.

    We intentionally keep this conservative so important
    placement/academic information isn't accidentally removed.
    """

    if not text:
        return ""

    lines = text.split("\n")

    signature_markers = [
        r"^\s*--\s*$",
        r"^\s*thanks\s*&\s*regards\s*$",
        r"^\s*thanks and regards\s*$",
        r"^\s*kind regards\s*$",
        r"^\s*best regards\s*$",
        r"^\s*warm regards\s*$",
        r"^\s*regards\s*$",
        r"^\s*thank you\s*$",
    ]

    for index, line in enumerate(lines):

        stripped = line.strip()

        for pattern in signature_markers:

            if re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            ):

                # Keep the marker itself only if it appears
                # very early. Otherwise assume it starts signature.
                if index >= 2:
                    lines = lines[:index]
                    return clean_text(
                        "\n".join(lines)
                    )

    return clean_text(text)


# ============================================================
# REMOVE GMAIL / SYSTEM NOISE
# ============================================================

def remove_email_noise(text):
    """
    Remove obvious email UI/system noise.
    """

    if not text:
        return ""

    lines = text.split("\n")

    noise_patterns = [
        r"^\s*unsubscribe\s*$",
        r"^\s*view this email in your browser\s*$",
        r"^\s*click here to unsubscribe\s*$",
        r"^\s*you are receiving this email because.*$",
        r"^\s*this email was sent to.*$",
    ]

    cleaned = []

    for line in lines:

        stripped = line.strip()

        is_noise = False

        for pattern in noise_patterns:

            if re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            ):
                is_noise = True
                break

        if not is_noise:
            cleaned.append(line)

    return clean_text(
        "\n".join(cleaned)
    )


# ============================================================
# EXTRACT CLEAN EMAIL BODY
# ============================================================

def extract_text_from_payload(payload):
    """
    Extract the best available email body.

    Priority:
        1. text/plain
        2. text/html converted to text
        3. empty string

    We DO NOT combine plain text + HTML because they can contain
    duplicate copies of the same email.
    """

    parts = collect_body_parts(payload)

    plain_parts = [
        clean_text(part)
        for part in parts["plain"]
        if clean_text(part)
    ]

    html_parts = [
        remove_html(part)
        for part in parts["html"]
        if remove_html(part)
    ]

    # Prefer plain text.
    if plain_parts:

        # Usually the first plain part is the actual message.
        # If multiple parts exist, choose the longest useful one.
        body = max(
            plain_parts,
            key=len,
        )

    elif html_parts:

        body = max(
            html_parts,
            key=len,
        )

    else:
        body = ""

    # Clean in stages.
    body = clean_text(body)

    body = remove_quoted_content(body)

    body = remove_signature(body)

    body = remove_email_noise(body)

    body = clean_text(body)

    return body


# ============================================================
# SHORTEN DISPLAY TEXT
# ============================================================

def shorten_text(text, max_len=40):
    """
    Shorten text only for the task label.
    """

    text = clean_text(text)

    if len(text) <= max_len:
        return text

    return text[: max_len - 3] + "..."


# ============================================================
# SAFE TASK KEY
# ============================================================

def normalize_subject_for_key(subject):
    """
    Normalize subject only for duplicate/event comparison.

    Examples:
        Re: Sandisk Online Test
        Reminder: Sandisk Online Test
        Sandisk Online Test

    all become the same normalized subject.
    """

    subject = clean_text(subject)

    previous = None

    while subject != previous:
        previous = subject

        subject = re.sub(
            r"^(re|fw|fwd|forwarded|reminder)\s*:\s*",
            "",
            subject,
            flags=re.IGNORECASE,
        )

    # Normalize common punctuation differences.
    subject = subject.lower()

    subject = re.sub(
        r"[^a-z0-9\s]",
        " ",
        subject,
    )

    subject = re.sub(
        r"\s+",
        " ",
        subject,
    ).strip()

    return subject


def make_task_key(task_type, label, date_text):
    """
    Stable key for the actual task.

    Prefixes such as Re/Fwd/Reminder are ignored.
    """

    task_type = clean_text(task_type)

    label = normalize_subject_for_key(
        label
    )

    date_text = clean_text(
        date_text
    )

    return (
        f"{task_type}|"
        f"{label}|"
        f"{date_text}"
    )

# ============================================================
# FETCH EMAIL TASKS
# ============================================================

def fetch_tasks(
    max_results=50,
    sent_message_ids=None,
    sent_task_keys=None,
    reprocess=False,
):
    """
    Fetch relevant Gmail messages and convert them into tasks.
    """

    if sent_message_ids is None:
        sent_message_ids = set()

    if sent_task_keys is None:
        sent_task_keys = set()

    print("Fetching emails...")

    service = get_gmail_service()

    # --------------------------------------------------------
    # Gmail search
    # --------------------------------------------------------

    query = (
        "("
        "subject:quiz OR "
        "subject:assignment OR "
        "subject:notes OR "
        "subject:test OR "
        "subject:assessment OR "
        "subject:internship OR "
        "subject:placement OR "
        '"quiz" OR '
        '"assignment" OR '
        '"notes" OR '
        '"online test" OR '
        '"offline test" OR '
        '"coding assessment" OR '
        '"aptitude test" OR '
        '"written test" OR '
        '"assessment link" OR '
        '"placement drive" OR '
        '"internship" OR '
        '"ppt" OR '
        '"slides" OR '
        '"marks"'
        ") "
        "-category:promotions "
        "-in:chats "
        "newer_than:6m"
    )

    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results,
        )
        .execute()
    )

    messages = results.get(
        "messages",
        [],
    )

    print(
        "Messages from Gmail:",
        len(messages),
    )

    print(
        "Reprocess mode:",
        reprocess,
    )

    tasks = []

    seen_message_ids = set()

    # ========================================================
    # PROCESS EACH EMAIL
    # ========================================================

    for msg in messages:

        message_id = msg.get("id")

        if not message_id:
            continue

        # ----------------------------------------------------
        # Skip already processed messages
        # ----------------------------------------------------

        if (
            not reprocess
            and message_id in sent_message_ids
        ):
            continue

        # ----------------------------------------------------
        # Avoid duplicate Gmail IDs
        # ----------------------------------------------------

        if message_id in seen_message_ids:
            continue

        seen_message_ids.add(message_id)

        # ----------------------------------------------------
        # Get full email
        # ----------------------------------------------------

        try:

            full_msg = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="full",
                )
                .execute()
            )

        except Exception as error:

            print(
                "Failed to read message:",
                message_id,
                error,
            )

            continue

        payload = full_msg.get(
            "payload",
            {},
        )

        headers = payload.get(
            "headers",
            [],
        )

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        subject = clean_text(
            get_header(
                headers,
                "Subject",
            )
        )

        sender = clean_text(
            get_header(
                headers,
                "From",
            )
        )

        # ----------------------------------------------------
        # CLEAN BODY
        #
        # IMPORTANT:
        # Do NOT use Gmail snippet here.
        #
        # Snippet can contain text from quoted/previous content
        # and can contaminate extraction.
        # ----------------------------------------------------

        body_text = extract_text_from_payload(
            payload
        )

        # Gmail snippet is intentionally NOT passed
        # to the classifier.
        snippet = ""

        internal_date = int(
            full_msg.get(
                "internalDate",
                "0",
            )
        )

        # ----------------------------------------------------
        # Debug
        # ----------------------------------------------------

        print("=" * 60)

        print(
            "Subject:",
            subject,
        )

        print(
            "From:",
            sender,
        )

        print(
            "Body length:",
            len(body_text),
        )

        # Print only a safe preview.
        preview = shorten_text(
            body_text,
            180,
        )

        print(
            "Body preview:",
            preview,
        )

        # ----------------------------------------------------
        # Empty email
        # ----------------------------------------------------

        if not subject and not body_text:
            print(
                "Skipped empty email."
            )
            continue

        # ====================================================
        # CLASSIFICATION
        # ====================================================

        try:

            data = rule_based_classify(
                subject,
                sender,
                body_text,
                snippet,
            )

        except Exception as error:

            print(
                "Classifier error:",
                error,
            )

            continue

        # ----------------------------------------------------
        # Classifier returned nothing
        # ----------------------------------------------------

        if not data:

            print(
                "Classifier returned None"
            )

            continue

        # ----------------------------------------------------
        # Validate classifier output
        # ----------------------------------------------------

        if not isinstance(data, dict):

            print(
                "Classifier returned invalid data:",
                type(data),
            )

            continue

        task_type = clean_text(
            str(
                data.get(
                    "type",
                    "",
                )
                or ""
            )
        )

        # ----------------------------------------------------
        # Skip Other
        # ----------------------------------------------------

        if task_type == "Other":

            print(
                "Skipped because classified as Other"
            )

            continue

        if not task_type:

            print(
                "Skipped because task type is empty."
            )

            continue

        # ----------------------------------------------------
        # Task label
        # ----------------------------------------------------

        label = clean_text(
            str(
                data.get(
                    "label",
                    "",
                )
                or ""
            )
        )

        if not label:
            label = subject or "Untitled Task"

        label = shorten_text(
            label,
            80,
        )

        # ----------------------------------------------------
        # Deadline
        # ----------------------------------------------------

        date_text = clean_text(
            str(
                data.get(
                    "date",
                    "Not mentioned",
                )
                or "Not mentioned"
            )
        )

        if not date_text:
            date_text = "Not mentioned"

        # ----------------------------------------------------
        # Task key
        # ----------------------------------------------------

        task_key = make_task_key(
            task_type,
            label,
            date_text,
        )

        # ----------------------------------------------------
        # Existing task check
        # ----------------------------------------------------

        if (
            not reprocess
            and task_key in sent_task_keys
        ):

            print(
                "Skipped existing task key:",
                task_key,
            )

            continue

        # ----------------------------------------------------
        # Accepted
        # ----------------------------------------------------

        print(
            "Accepted task:",
            task_key,
        )

        # ====================================================
        # BUILD TASK
        # ====================================================

        tasks.append(
            {
                "type": task_type,
                "label": label,
                "date": date_text,
                "internalDate": internal_date,
                "message_id": message_id,

                "company": data.get(
                    "company",
                    "",
                ),

                "role": data.get(
                    "role",
                    "",
                ),

                "eligibility": data.get(
                    "eligibility",
                    "",
                ),

                "ctc": data.get(
                    "ctc",
                    "",
                ),

                "stipend": data.get(
                    "stipend",
                    "",
                ),

                "registration_link": data.get(
                    "registration_link",
                    "",
                ),

                "venue": data.get(
                    "venue",
                    "",
                ),

                "location": data.get(
                    "location",
                    "",
                ),

                "deadline": data.get(
                    "deadline",
                    "",
                ),

                "batch": data.get(
                    "batch",
                    "",
                ),

                "branches": data.get(
                    "branches",
                    "",
                ),

                "process": data.get(
                    "process",
                    "",
                ),

                "contact": data.get(
                    "contact",
                    "",
                ),

                "action": data.get(
                    "action",
                    "",
                ),

                "description": data.get(
                    "description",
                    "",
                ),
            }
        )

    # ========================================================
    # SORT NEWEST FIRST
    # ========================================================

    tasks.sort(
        key=lambda x: x.get(
            "internalDate",
            0,
        ),
        reverse=True,
    )

    print(
        "Final extracted tasks:",
        len(tasks),
    )

    return tasks