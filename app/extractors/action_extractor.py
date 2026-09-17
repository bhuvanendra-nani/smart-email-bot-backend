
import re


VALID_ACTIONS = {
    "Register",
    "Apply",
    "Attend",
    "Submit",
    "Take Test",
    "Complete",
    "Join",
    "View",
    "Check Result",
    "Participate",
}


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def exact_phrase(text: str, phrase: str) -> bool:
    return bool(
        re.search(
            rf"\b{re.escape(phrase.lower())}\b",
            text.lower(),
        )
    )


def extract_action(subject: str = "", body: str = "") -> str | None:

    subject = clean_text(subject)
    body = clean_text(body)

    subject_lower = subject.lower()
    body_lower = body.lower()

    # --------------------------------------------------------
    # 1. Explicit result / selection messages
    # --------------------------------------------------------

    result_phrases = [
        "selection list",
        "selected candidates",
        "selected candidate",
        "shortlisted candidates",
        "shortlisted candidate",
        "test shortlisted",
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
        "final selection",
        "final selected",
        "you have been selected",
        "you are selected",
        "selected for",
        "shortlisted for",
    ]

    for phrase in result_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Check Result"

    # --------------------------------------------------------
    # 2. Explicit attendance / reporting
    # --------------------------------------------------------

    attend_phrases = [
        "report to",
        "report at",
        "report by",
        "report immediately",
        "all shortlisted candidates must attend",
        "must attend",
        "should attend",
        "need to attend",
        "please attend",
        "attend the test",
        "attend the interview",
        "attend the session",
        "carry your laptop",
        "bring your laptop",
    ]

    for phrase in attend_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Attend"

    for phrase in attend_phrases:
        if exact_phrase(body_lower, phrase):
            return "Attend"

    # --------------------------------------------------------
    # 3. Test / assessment / exam
    # --------------------------------------------------------

    test_phrases = [
        "online test",
        "offline test",
        "coding assessment",
        "technical assessment",
        "aptitude test",
        "written test",
        "assessment test",
        "online assessment",
        "coding test",
        "technical test",
        "quiz",
        "exam",
    ]

    for phrase in test_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Take Test"

    # --------------------------------------------------------
    # 4. Interview
    # --------------------------------------------------------

    interview_phrases = [
        "interview",
        "interviews",
        "interview scheduled",
        "interview process",
        "technical interview",
        "hr interview",
        "personal interview",
        "virtual interview",
        "offline interview",
    ]

    for phrase in interview_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Attend"

    # --------------------------------------------------------
    # 5. Registration
    # --------------------------------------------------------

    registration_phrases = [
        "registration",
        "register",
        "register for",
        "registration link",
        "last date for registration",
        "registration deadline",
        "register now",
    ]

    for phrase in registration_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Register"

    # --------------------------------------------------------
    # 6. Application
    # --------------------------------------------------------

    application_phrases = [
        "apply",
        "apply for",
        "application",
        "application link",
        "apply now",
        "last date to apply",
        "application deadline",
    ]

    for phrase in application_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Apply"

    # --------------------------------------------------------
    # 7. Submission
    # --------------------------------------------------------

    submission_phrases = [
        "submit",
        "submission",
        "submit your",
        "submission deadline",
        "last date for submission",
        "upload",
        "upload your",
    ]

    for phrase in submission_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Submit"

    # --------------------------------------------------------
    # 8. Competition / hackathon participation
    # --------------------------------------------------------

    participation_phrases = [
        "hackathon",
        "competition",
        "contest",
        "challenge",
        "participate",
        "participation",
    ]

    for phrase in participation_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Participate"

    # --------------------------------------------------------
    # 9. Workshop / session / PPT
    # --------------------------------------------------------

    event_phrases = [
        "workshop",
        "webinar",
        "seminar",
        "session",
        "pre placement talk",
        "pre-placement talk",
        "company presentation",
        "presentation session",
        "ppt session",
    ]

    for phrase in event_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Attend"

    # --------------------------------------------------------
    # 10. Strong body-level action phrases
    # --------------------------------------------------------

    body_patterns = [
        (r"\bplease register\b", "Register"),
        (r"\bregister now\b", "Register"),
        (r"\bplease apply\b", "Apply"),
        (r"\bapply now\b", "Apply"),
        (r"\bplease submit\b", "Submit"),
        (r"\bsubmit your\b", "Submit"),
        (r"\bmust attend\b", "Attend"),
        (r"\bplease attend\b", "Attend"),
        (r"\bneed to attend\b", "Attend"),
        (r"\bmust report\b", "Attend"),
        (r"\bplease report\b", "Attend"),
        (r"\breport immediately\b", "Attend"),
        (r"\bcomplete the test\b", "Take Test"),
        (r"\btake the test\b", "Take Test"),
        (r"\bcomplete the assessment\b", "Complete"),
        (r"\bjoin the session\b", "Join"),
        (r"\bjoin the meeting\b", "Join"),
    ]

    for pattern, action in body_patterns:
        if re.search(pattern, body_lower):
            return action

    # --------------------------------------------------------
    # 11. Explicit view / result phrases in subject
    # --------------------------------------------------------

    view_phrases = [
        "result",
        "results",
        "result update",
        "result announced",
        "result declaration",
        "selection update",
    ]

    for phrase in view_phrases:
        if exact_phrase(subject_lower, phrase):
            return "Check Result"

    # --------------------------------------------------------
    # 12. Generic fallback
    # --------------------------------------------------------

    return None

