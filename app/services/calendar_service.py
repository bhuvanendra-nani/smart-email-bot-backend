import os
import re
import time

from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

AUTO_ADD_CALENDAR = (
    os.getenv("AUTO_ADD_CALENDAR", "false").lower() == "true"
)

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def get_calendar_service():
    creds = Credentials.from_authorized_user_file(
    "credentials/calendar_token.json",
    CALENDAR_SCOPES,
)
    return build(
        "calendar",
        "v3",
        credentials=creds,
        cache_discovery=False
    )


def parse_date_for_calendar(date_str):
    if not date_str or date_str == "Not mentioned":
        return None

    cleaned = re.sub(r"(\d)(st|nd|rd|th)", r"\1", date_str, flags=re.IGNORECASE)

    formats = [
        "%d/%m/%y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d-%m-%y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass

    return None


def add_calendar_events(tasks):
    if not AUTO_ADD_CALENDAR:
        return []

    service = get_calendar_service()
    created = []

    for task in tasks:

        dt = parse_date_for_calendar(task["date"])

        if not dt:
            continue

        start = dt.replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0
        )

        end = start + timedelta(hours=1)

        event = {
            "summary": f"{task['type']}: {task['label']}",
            "description": f"Category: {task['type']}",
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": TIMEZONE,
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": TIMEZONE,
            },
        }

        try:
            result = service.events().insert(
                calendarId="primary",
                body=event
            ).execute()

            created.append(result)

            time.sleep(0.5)

        except Exception as e:
            print("Calendar Error:", e)

    return created
