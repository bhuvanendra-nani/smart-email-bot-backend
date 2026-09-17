import os
import json
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =======================================================
# AI EXTRACTION PROMPT
# =======================================================

PROMPT = """
You are a strict email information extraction system.

Your job is to extract ONLY information that is actually
supported by the email.

Do NOT guess.
Do NOT infer missing information.
Do NOT use examples or unrelated company names.
Do NOT copy information from email signatures unless it
clearly belongs to the event/job/internship being described.

If a field is not clearly available, return "".

Return ONLY valid JSON.
Do not return Markdown.
Do not return explanations.

JSON format:

{
  "type": "",
  "company": "",
  "role": "",
  "eligibility": "",
  "branches": "",
  "batch": "",
  "ctc": "",
  "stipend": "",
  "deadline": "",
  "registration_link": "",
  "venue": "",
  "location": "",
  "mode": "",
  "process": "",
  "contact": "",
  "action": "",
  "description": ""
}


=======================================================
FIELD RULES
=======================================================

company:
- Extract the actual company/organization conducting
  the opportunity.
- Prefer the company explicitly associated with the
  internship, placement, job, interview, test, or event.
- Do NOT select a company merely because its name appears
  in a footer, forwarded email, signature, disclaimer,
  previous email, or unrelated text.

role:
- Extract the actual job/internship role.
- Examples: Software Engineer, Technical Support Associate,
  Data Analyst Intern.
- Do not return long sentences.

eligibility:
- Extract eligibility requirements only.
- Include relevant qualification, CGPA, percentage,
  branch, experience, or other stated requirements.
- Do not invent requirements.

branches:
- Extract eligible branches/departments only.
- Keep the answer short.
- Example: CSE, IT, ECE.
- Do not copy entire paragraphs.

batch:
- Extract the eligible graduation batch/year.
- Example: 2027.
- If multiple years are explicitly eligible, preserve them.

ctc:
- Extract salary/package/CTC only.
- Example: 8 LPA.
- Do not confuse stipend with CTC.

stipend:
- Extract internship stipend only.
- Example: ₹25,000/month.
- Do not confuse CTC/package with stipend.

deadline:
- Extract the relevant registration/application/
  submission/test/interview deadline.
- Do not select an unrelated date from the email.
- If several dates exist, select the date associated
  with the required action.

registration_link:
- Return the actual application/registration/test link.
- Do not return unsubscribe links, privacy links,
  social media links, tracking links, or unrelated URLs.

venue:
- Extract the physical venue when explicitly mentioned.
- Do not use a generic city as venue.
- Do not return "online", "virtual", or "remote" as venue.

location:
- Extract the actual work/event/interview location
  when explicitly stated.
- Example: Bengaluru, Hyderabad, Chennai.
- Do not confuse company address or email footer with
  opportunity location.

mode:
- Return only when clearly stated.
- Examples: Online, Offline, Hybrid, Virtual.
- Do not infer Online merely because registration is online.

process:
- Extract the selection/recruitment process.
- Keep it concise.
- Do not copy the complete email.

contact:
- Extract the relevant coordinator/contact person,
  email, or phone number.
- Do not copy unrelated signatures.

action:
- Extract the primary action required from the recipient.
- Allowed values:
  Register
  Attend
  Submit
  Participate
  Complete
  Check Result
  Join
  Apply
  View

description:
- Give a short summary of the actual opportunity/email.
- Maximum approximately 250 characters.
- Do not copy the entire email.

type:
- Identify the main type if clearly stated.
- Examples:
  Internship Registration
  Internship Selection
  Placement Registration
  Placement Selection
  Interview
  Workshop
  Hackathon
  Online Test
  Assignment
  Quiz
  Notes
  Marks Update
- If unclear, return "".
"""


# =======================================================
# JSON CLEANING
# =======================================================

def clean_json_response(text):
    """
    Clean common Gemini JSON formatting issues.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove Markdown code fences.
    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

    text = text.strip()

    # Sometimes Gemini returns extra text around JSON.
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text.strip()


# =======================================================
# VALUE CLEANING
# =======================================================

VALID_ACTIONS = {
    "Register",
    "Attend",
    "Submit",
    "Participate",
    "Complete",
    "Check Result",
    "Join",
    "Apply",
    "View",
}


VALID_MODES = {
    "online": "Online",
    "offline": "Offline",
    "hybrid": "Hybrid",
    "virtual": "Virtual",
}


def clean_value(value):
    """
    Normalize Gemini values without changing meaning.
    """

    if value is None:
        return ""

    if isinstance(value, list):

        value = ", ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    elif isinstance(value, dict):

        value = json.dumps(
            value,
            ensure_ascii=False,
        )

    else:

        value = str(value)

    value = value.strip()

    invalid_values = {
        "not mentioned",
        "not available",
        "not specified",
        "unknown",
        "n/a",
        "na",
        "none",
        "null",
        "-",
    }

    if value.lower() in invalid_values:
        return ""

    return value


def normalize_result(data):
    """
    Ensure Gemini returns only the expected schema.
    """

    if not isinstance(data, dict):
        return {}

    fields = [
        "type",
        "company",
        "role",
        "eligibility",
        "branches",
        "batch",
        "ctc",
        "stipend",
        "deadline",
        "registration_link",
        "venue",
        "location",
        "mode",
        "process",
        "contact",
        "action",
        "description",
    ]

    result = {}

    for field in fields:

        result[field] = clean_value(
            data.get(field, "")
        )

    # ---------------------------------------------------
    # Normalize action
    # ---------------------------------------------------

    if result["action"]:

        action_lower = result["action"].lower()

        matching_action = next(
            (
                action
                for action in VALID_ACTIONS
                if action.lower() == action_lower
            ),
            None,
        )

        if matching_action:
            result["action"] = matching_action
        else:
            # Classifier has a safer rule-based action.
            result["action"] = ""

    # ---------------------------------------------------
    # Normalize mode
    # ---------------------------------------------------

    if result["mode"]:

        mode_lower = result["mode"].lower()

        if mode_lower in VALID_MODES:
            result["mode"] = VALID_MODES[mode_lower]

        else:
            result["mode"] = ""

    # ---------------------------------------------------
    # Keep description short
    # ---------------------------------------------------

    if len(result["description"]) > 300:

        result["description"] = (
            result["description"][:297] + "..."
        )

    # ---------------------------------------------------
    # Prevent huge semantic values
    # ---------------------------------------------------

    max_lengths = {
        "company": 150,
        "role": 150,
        "eligibility": 500,
        "branches": 200,
        "batch": 100,
        "ctc": 100,
        "stipend": 100,
        "deadline": 150,
        "registration_link": 500,
        "venue": 200,
        "location": 150,
        "mode": 50,
        "process": 500,
        "contact": 200,
        "action": 50,
        "description": 300,
    }

    for field, max_length in max_lengths.items():

        if len(result[field]) > max_length:
            result[field] = ""

    return result


# =======================================================
# AI EXTRACTION
# =======================================================

def ai_extract(subject, body):

    try:

        subject = subject or ""
        body = body or ""

        response = client.models.generate_content(
            model="gemini-2.5-flash",

            contents=f"""
{PROMPT}

=======================================================
EMAIL TO ANALYZE
=======================================================

SUBJECT:
{subject}

BODY:
{body}

=======================================================
END EMAIL
=======================================================
""",
        )

        text = response.text or ""

        text = clean_json_response(text)

        if not text:
            return {}

        data = json.loads(text)

        return normalize_result(data)

    except Exception:
        return {}