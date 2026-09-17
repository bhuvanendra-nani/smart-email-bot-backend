import os
import html
import time
import requests
import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()
CAREER_TYPES = {
    "Placement",
    "Internship",
    "Coding Test",
    "Assessment",
}

ACADEMIC_TYPES = {
    "Assignment",
    "Quiz",
    "Exam",
    "Lab",
    "Project",
    "Notes",
}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def group_tasks(tasks):
    career, academic, misc = [], [], []
    for task in tasks:
        if task["type"] in CAREER_TYPES:
            career.append(task)
        elif task["type"] in ACADEMIC_TYPES:
            academic.append(task)
        else:
            misc.append(task)
    return career, academic, misc

def make_pre_table(title, tasks, second_col_title):
    if not tasks:
        return f"<b>{html.escape(title)}</b>\n<pre>No items</pre>"

    type_w = min(max(len("Type"), max(len(t["type"]) for t in tasks)), 14)
    col2_w = min(max(len(second_col_title), max(len(t["label"]) for t in tasks)), 34)
    date_w = min(max(len("Date"), max(len(t["date"]) for t in tasks)), 17)

    border = f"+-{'-' * type_w}-+-{'-' * col2_w}-+-{'-' * date_w}-+"
    header = f"| {'Type':<{type_w}} | {second_col_title:<{col2_w}} | {'Date':<{date_w}} |"

    rows = [border, header, border]
    for t in tasks:
        rows.append(
            f"| {t['type'][:type_w]:<{type_w}} | "
            f"{t['label'][:col2_w]:<{col2_w}} | "
            f"{t['date'][:date_w]:<{date_w}} |"
        )
    rows.append(border)

    return f"<b>{html.escape(title)}</b>\n<pre>{html.escape(chr(10).join(rows))}</pre>"


def build_telegram_message(tasks):
    career, academic, misc = group_tasks(tasks)
    parts = [
        "<b>VIT Task Summary</b>",
        f"Total new tasks: <b>{len(tasks)}</b>",
        "",
        make_pre_table("💼 Career", career, "Company/Test"),
        "",
        make_pre_table("📚 Academic", academic, "Subject/Task"),
        "",
        make_pre_table("🗂 Miscellaneous", misc, "Details"),
    ]
    return "\n".join(parts)

def split_html_message(text, limit=3500):
    parts = []
    while len(text) > limit:
        split_at = text.rfind("\n\n", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        parts.append(text)
    return parts

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing in .env")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    parts = split_html_message(message)
    last_response = None

    for idx, part in enumerate(parts, start=1):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": part,
            "parse_mode": "HTML",
        }
        response = requests.post(url, data=payload, timeout=20)
        try:
            data = response.json()
        except Exception:
            logger.error("Telegram returned invalid JSON.")
            return None

        last_response = data
        logger.info("Telegram response part %s: %s", idx, data)

        if not data.get("ok"):
            break

        time.sleep(1)

    return last_response
