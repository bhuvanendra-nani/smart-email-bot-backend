import re
from collections import defaultdict

from app.extractors.company_extractor import extract_company
from app.extractors.role_extractor import extract_role
from app.extractors.deadline_extractor import extract_deadline
from app.extractors.ctc_extractor import extract_ctc
from app.extractors.stipend_extractor import extract_stipend
from app.extractors.branches_extractor import extract_branches
from app.extractors.batch_extractor import extract_batch
from app.extractors.eligibility_extractor import extract_eligibility
from app.extractors.registration_link_extractor import extract_registration_link

from app.extractors.venue_extractor import extract_venue
from app.extractors.location_extractor import extract_location
from app.extractors.mode_extractor import extract_mode
from app.extractors.process_extractor import extract_process
from app.extractors.contact_extractor import extract_contact
from app.extractors.description_extractor import extract_description
from app.extractors.action_extractor import extract_action

from app.extractors.assignment_extractor import extract_assignment_details
from app.extractors.quiz_extractor import extract_quiz_details
from app.extractors.interview_extractor import extract_interview_details
from app.extractors.workshop_extractor import extract_workshop_details
from app.extractors.hackathon_extractor import extract_hackathon_details

from app.services.ai_classifier import ai_extract


# =======================================================
# Helper Functions
# =======================================================

def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def shorten_text(text, max_len=40):
    text = clean_text(text)

    if len(text) <= max_len:
        return text

    return text[: max_len - 3] + "..."


def valid_value(value):
    if value is None:
        return False

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return False

        invalid_values = {
            "not mentioned",
            "unknown",
            "n/a",
            "na",
            "none",
            "null",
            "not available",
            "not specified",
            "nil",
            "-",
        }

        return value.lower() not in invalid_values

    if isinstance(value, (list, dict)):
        return len(value) > 0

    return True


def clean_ai_value(value):

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip()
        value = value.strip("\"'")

        if not value:
            return None

        invalid_values = {
            "not mentioned",
            "unknown",
            "n/a",
            "na",
            "none",
            "null",
            "not available",
            "not specified",
        }

        if value.lower() in invalid_values:
            return None

        return value

    return value


def suspicious_value(value, field=None):

    if not valid_value(value):
        return True

    if not isinstance(value, str):
        return False

    value = value.strip()

    if len(value) > 700:
        return True

    if len(value.split()) > 100:
        return True

    if field in {
        "company",
        "role",
        "batch",
        "ctc",
        "stipend",
        "location",
        "venue",
        "mode",
        "contact",
    }:

        if "\n" in value:
            return True

    return False


def merge(rule_value, ai_value, field=None):

    rule_value = (
        None
        if suspicious_value(rule_value, field)
        else rule_value
    )

    ai_value = clean_ai_value(ai_value)

    if not valid_value(rule_value):
        return ai_value

    if not valid_value(ai_value):
        return rule_value

    if field in {
        "deadline",
        "registration_link",
    }:
        return rule_value

    semantic_fields = {
        "company",
        "role",
        "eligibility",
        "branches",
        "batch",
        "ctc",
        "stipend",
        "venue",
        "location",
        "mode",
        "process",
        "contact",
        "description",
    }

    if field in semantic_fields:
        return ai_value

    return rule_value


# =======================================================
# Metadata Extraction
# =======================================================

def extract_metadata(
    subject,
    sender,
    body,
    snippet,
    task_type,
):

    subject = subject or ""
    sender = sender or ""
    body = body or ""
    snippet = snippet or ""

    company = extract_company(
        subject,
        body,
    )

    role = extract_role(
        subject,
        body,
    )

    eligibility = extract_eligibility(
        body,
    )

    branches = extract_branches(
        body,
    )

    batch = extract_batch(
        body,
    )

    ctc = extract_ctc(
        body,
    )

    stipend = extract_stipend(
        body,
    )

    deadline_text = f"{subject}\n{body}"

    deadline = extract_deadline(
        deadline_text,
    )

    registration_link = extract_registration_link(
        body,
    )

    venue = extract_venue(
        body,
    )

    location = extract_location(
        body,
    )

    mode = extract_mode(
        body,
    )

    process = extract_process(
        body,
    )

    contact = extract_contact(
        body,
    )

    action = extract_action(
        subject,
        body,
    )

    description = extract_description(
        body,
    )

    # ---------------------------------------------------
    # Gemini
    # ---------------------------------------------------

    ai_data = {}

    important_task_types = [
        "Internship Registration",
        "Internship Selection",
        "Placement Registration",
        "Placement Selection",
        "Interview",
        "Workshop",
        "Hackathon",
    ]

    if task_type in important_task_types:

        try:

            ai_data = ai_extract(
                subject,
                body,
            )

            if not isinstance(ai_data, dict):
                ai_data = {}

        except Exception:
            ai_data = {}

    # ---------------------------------------------------
    # Task-specific extraction
    # ---------------------------------------------------

    assignment_details = None
    quiz_details = None
    interview_details = None
    workshop_details = None
    hackathon_details = None

    if task_type == "Assignment":

        assignment_details = extract_assignment_details(body)

    elif task_type == "Quiz":

        quiz_details = extract_quiz_details(body)

    elif task_type == "Interview":

        interview_details = extract_interview_details(body)

    elif task_type == "Workshop":

        workshop_details = extract_workshop_details(body)

    elif task_type == "Hackathon":

        hackathon_details = extract_hackathon_details(body)

    # ---------------------------------------------------
    # Merge
    # ---------------------------------------------------

    return {

        "company": merge(
            company,
            ai_data.get("company"),
            "company",
        ),

        "role": merge(
            role,
            ai_data.get("role"),
            "role",
        ),

        "eligibility": merge(
            eligibility,
            ai_data.get("eligibility"),
            "eligibility",
        ),

        "branches": merge(
            branches,
            ai_data.get("branches"),
            "branches",
        ),

        "batch": merge(
            batch,
            ai_data.get("batch"),
            "batch",
        ),

        "ctc": merge(
            ctc,
            ai_data.get("ctc"),
            "ctc",
        ),

        "stipend": merge(
            stipend,
            ai_data.get("stipend"),
            "stipend",
        ),

        "deadline": merge(
            deadline,
            ai_data.get("deadline"),
            "deadline",
        ),

        "registration_link": merge(
            registration_link,
            ai_data.get("registration_link"),
            "registration_link",
        ),

        "venue": merge(
            venue,
            ai_data.get("venue"),
            "venue",
        ),

        "location": merge(
            location,
            ai_data.get("location"),
            "location",
        ),

        "mode": merge(
            mode,
            ai_data.get("mode"),
            "mode",
        ),

        "process": merge(
            process,
            ai_data.get("process"),
            "process",
        ),

        "contact": merge(
            contact,
            ai_data.get("contact"),
            "contact",
        ),

        "action": action,

        "description": merge(
            shorten_text(
                description,
                250,
            ),
            ai_data.get("description"),
            "description",
        ),

        "assignment_details": assignment_details,

        "quiz_details": quiz_details,

        "interview_details": interview_details,

        "workshop_details": workshop_details,

        "hackathon_details": hackathon_details,
    }


# =======================================================
# Classification Helpers
# =======================================================

def normalize_subject(subject):

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

    return subject.strip()


def contains_any(text, keywords):
    return any(
        keyword in text
        for keyword in keywords
    )


def classify_result(
    task_type,
    original_subject,
    sender,
    body,
    snippet,
    confidence,
):

    metadata = extract_metadata(
        original_subject,
        sender,
        body,
        snippet,
        task_type,
    )

    return {
        "type": task_type,
        "label": shorten_text(original_subject),
        "date": metadata["deadline"] or "Not mentioned",
        "confidence": confidence,
        **metadata,
    }


# =======================================================
# Rule-Based Classification
# =======================================================

def rule_based_classify(
    subject,
    sender,
    body,
    snippet,
):

    original_subject = clean_text(subject)

    normalized_subject = normalize_subject(
        original_subject
    )

    subject_text = normalized_subject.lower()

    body_text = clean_text(
        f"{sender}\n{snippet}\n{body}"
    ).lower()

    # ===================================================
    # 1. SELECTION / RESULT / OFFER
    # ===================================================

    # IMPORTANT:
    # Do NOT treat "selection process" alone as a result.
    # It can appear in PPT/interview/instruction emails.

    selection_result_phrases = [
        "selection list",
        "selected candidates",
        "selected candidate",
        "shortlisted candidates",
        "shortlisted candidate",
        "selection result",
        "selection results",
        "offer selection",
        "offer selection list",
        "offer list",
        "offer letter",
        "ppo selection",
        "ppo list",
        "ppo offer",
        "placement offer",
        "placement offer selection",
        "final selection",
        "final selected",
        "you have been selected",
        "you are selected",
    ]

    selection_subject_match = contains_any(
        subject_text,
        selection_result_phrases,
    )

    # "selected for" / "shortlisted for" are only strong
    # when they are actually announcing a candidate result.
    selected_for_match = (
        "selected for" in subject_text
        or "shortlisted for" in subject_text
    )

    if selection_subject_match or selected_for_match:

        # Placement / PPO
        if contains_any(
            subject_text,
            [
                "placement",
                "ppo",
                "placement offer",
                "placement selection",
            ],
        ):

            return classify_result(
                "Placement Selection",
                original_subject,
                sender,
                body,
                snippet,
                "Very High",
            )

        # Internship
        if contains_any(
            subject_text,
            [
                "internship",
                "summer internship",
                "internship offer",
                "intern",
            ],
        ):

            return classify_result(
                "Internship Selection",
                original_subject,
                sender,
                body,
                snippet,
                "Very High",
            )

        # Body fallback
        if (
            "placement" in body_text
            or "ppo" in body_text
        ):

            return classify_result(
                "Placement Selection",
                original_subject,
                sender,
                body,
                snippet,
                "High",
            )

        if "internship" in body_text:

            return classify_result(
                "Internship Selection",
                original_subject,
                sender,
                body,
                snippet,
                "High",
            )

        return classify_result(
            "Placement Selection",
            original_subject,
            sender,
            body,
            snippet,
            "Medium",
        )

    # ===================================================
    # 2. ACTUAL INTERVIEW
    # ===================================================

    interview_phrases = [
        "interview scheduled",
        "interview is scheduled",
        "interview schedule",
        "interview invitation",
        "interview invite",
        "interview call",
        "technical interview",
        "hr interview",
        "managerial interview",
        "panel interview",
        "final interview",
        "interview round",
        "interview slot",
        "interview details",
        "interview venue",
        "interview link",
        "attend interview",
        "interview process",
    ]

    if contains_any(
        subject_text,
        interview_phrases,
    ):

        return classify_result(
            "Interview",
            original_subject,
            sender,
            body,
            snippet,
            "Very High",
        )

    # ===================================================
    # 3. PPT / PRE-PLACEMENT TALK
    # ===================================================

    ppt_phrases = [
        "pre placement talk",
        "pre-placement talk",
        "pre placement presentation",
        "pre-placement presentation",
        "ppt",
        "ppt session",
        "ppt presentation",
        "company presentation",
        "company ppt",
        "company presentation session",
        "presentation session",
        "presentation by",
        "group discussion",
    ]

    if contains_any(
        subject_text,
        ppt_phrases,
    ):

        return classify_result(
            "PPT",
            original_subject,
            sender,
            body,
            snippet,
            "Very High",
        )

    # ===================================================
    # 4. ONLINE TEST / ASSESSMENT
    # ===================================================

    test_phrases = [
        "online test",
        "online assessment",
        "coding test",
        "coding assessment",
        "technical assessment",
        "aptitude test",
        "assessment test",
        "assessment link",
        "coding round",
        "online exam",
        "test scheduled",
        "test is scheduled",
        "assessment scheduled",
        "assessment is scheduled",
        "hackerrank",
        "hirepro",
        "amcat",
        "cocubes",
    ]

    if contains_any(
        subject_text,
        test_phrases,
    ):

        return classify_result(
            "Online Test",
            original_subject,
            sender,
            body,
            snippet,
            "Very High",
        )

    # ===================================================
    # 5. ASSIGNMENT
    # ===================================================

    assignment_phrases = [
        "assignment submission",
        "submit assignment",
        "submit the assignment",
        "assignment deadline",
        "submission of assignment",
        "lab assignment",
    ]

    if contains_any(
        subject_text,
        assignment_phrases,
    ):

        return classify_result(
            "Assignment",
            original_subject,
            sender,
            body,
            snippet,
            "Very High",
        )

    # ===================================================
    # 6. INTERNSHIP REGISTRATION
    # ===================================================

    internship_registration_phrases = [
        "internship registration",
        "register for internship",
        "registration for internship",
        "internship application",
        "internship drive",
        "summer internship",
        "summer internship registration",
        "internship hiring",
        "apply internship",
        "apply for internship",
        "internship opportunity",
        "internship opening",
        "internship recruitment",
        "internship hiring drive",
        "internship position",
        "internship program",
        "internship 2027",
        "super dream internship",
        "internship - registration",
        "internship & placement",
        "internship/placement",
    ]

    if contains_any(
        subject_text,
        internship_registration_phrases,
    ):

        return classify_result(
            "Internship Registration",
            original_subject,
            sender,
            body,
            snippet,
            "Very High",
        )

    # ===================================================
    # 7. PLACEMENT REGISTRATION
    # ===================================================

    placement_registration_phrases = [
        "placement registration",
        "register for placement",
        "registration for placement",
        "campus hiring registration",
        "placement drive",
        "campus recruitment",
        "campus hiring",
        "hiring drive",
        "placement opportunity",
        "placement opening",
        "placement recruitment",
        "placement hiring",
        "placement 2027",
        "super dream placement",
    ]

    if contains_any(
        subject_text,
        placement_registration_phrases,
    ):

        return classify_result(
            "Placement Registration",
            original_subject,
            sender,
            body,
            snippet,
            "Very High",
        )

    # ===================================================
    # 8. HACKATHON
    # ===================================================

    hackathon_phrases = [
        "hackathon",
        "coding contest",
        "coding competition",
        "innovation challenge",
        "innovation competition",
        "ideathon",
    ]

    if contains_any(
        subject_text,
        hackathon_phrases,
    ):

        return classify_result(
            "Hackathon",
            original_subject,
            sender,
            body,
            snippet,
            "High",
        )

    # ===================================================
    # 9. WORKSHOP
    # ===================================================

    workshop_phrases = [
        "workshop",
        "bootcamp",
        "training session",
        "technical training",
        "hands-on training",
    ]

    if contains_any(
        subject_text,
        workshop_phrases,
    ):

        return classify_result(
            "Workshop",
            original_subject,
            sender,
            body,
            snippet,
            "High",
        )

    # ===================================================
    # 10. QUIZ
    # ===================================================

    quiz_phrases = [
        "online quiz",
        "quiz scheduled",
        "quiz submission",
        "mcq quiz",
        "quiz test",
        "quiz",
    ]

    if contains_any(
        subject_text,
        quiz_phrases,
    ):

        return classify_result(
            "Quiz",
            original_subject,
            sender,
            body,
            snippet,
            "High",
        )

    # ===================================================
    # 11. NOTES
    # ===================================================

    notes_phrases = [
        "study material",
        "lecture notes",
        "class notes",
        "course notes",
        "notes shared",
        "study notes",
    ]

    if contains_any(
        subject_text,
        notes_phrases,
    ):

        return classify_result(
            "Notes",
            original_subject,
            sender,
            body,
            snippet,
            "High",
        )

    # ===================================================
    # 12. MARKS UPDATE
    # ===================================================

    marks_phrases = [
        "marks update",
        "marks updated",
        "marks released",
        "marks published",
        "internal marks",
        "grade update",
        "grades updated",
        "cgpa update",
        "score updated",
        "evaluation marks",
    ]

    if contains_any(
        subject_text,
        marks_phrases,
    ):

        return classify_result(
            "Marks Update",
            original_subject,
            sender,
            body,
            snippet,
            "High",
        )

    # ===================================================
    # 13. BODY-BASED FALLBACK
    # ===================================================

    rules = {

        "Internship Registration": [
            "internship registration",
            "register for internship",
            "registration for internship",
            "internship application",
            "internship opportunity",
            "internship opening",
            "super dream internship",
        ],

        "Internship Selection": [
            "internship selection",
            "selected candidates for internship",
            "internship shortlist",
            "internship shortlisted",
            "internship offer",
        ],

        "Placement Registration": [
            "placement registration",
            "register for placement",
            "placement drive",
            "campus recruitment",
            "campus hiring",
            "hiring drive",
        ],

        "Placement Selection": [
            "placement selection",
            "selected candidates for placement",
            "placement shortlist",
            "placement offer",
            "ppo selection",
        ],

        "Online Test": [
            "online test",
            "online assessment",
            "coding assessment",
            "technical assessment",
            "aptitude test",
        ],

        "Interview": [
            "technical interview",
            "hr interview",
            "interview scheduled",
            "interview invitation",
        ],

        "PPT": [
            "pre placement talk",
            "pre-placement talk",
            "ppt scheduled",
            "company presentation",
            "presentation session",
            "group discussion",
        ],

        "Workshop": [
            "workshop",
            "bootcamp",
            "training session",
        ],

        "Hackathon": [
            "hackathon",
            "coding contest",
            "coding competition",
            "ideathon",
        ],

        "Assignment": [
            "assignment submission",
            "submit assignment",
            "assignment deadline",
        ],

        "Quiz": [
            "quiz scheduled",
            "online quiz",
            "quiz submission",
        ],

        "Notes": [
            "study material",
            "lecture notes",
            "class notes",
        ],

        "Marks Update": [
            "marks updated",
            "marks published",
            "internal marks",
            "grades updated",
        ],
    }

    scores = defaultdict(int)

    for task_type, keywords in rules.items():

        for keyword in keywords:

            if keyword in body_text:
                scores[task_type] += 1

    # ===================================================
    # 14. NO MATCH
    # ===================================================

    if not scores:

        metadata = extract_metadata(
            subject,
            sender,
            body,
            snippet,
            "Other",
        )

        return {
            "type": "Other",
            "label": shorten_text(original_subject),
            "date": metadata["deadline"] or "Not mentioned",
            "confidence": "Low",
            **metadata,
        }

    # ===================================================
    # 15. BEST FALLBACK
    # ===================================================

    task_type = max(
        scores,
        key=scores.get,
    )

    score = scores[task_type]

    confidence = (
        "High"
        if score >= 3
        else "Medium"
        if score >= 2
        else "Low"
    )

    return classify_result(
        task_type,
        original_subject,
        sender,
        body,
        snippet,
        confidence,
    )