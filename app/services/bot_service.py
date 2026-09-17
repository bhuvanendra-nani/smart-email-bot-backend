from sqlalchemy.orm import Session

from app.services.gmail_service import (
    fetch_tasks,
    make_task_key,
)

# from app.services.telegram_service import (
#     build_telegram_message,
#     send_telegram,
# )

from app.services.calendar_service import add_calendar_events

from app.services.state_service import (
    get_sent_message_ids,
    get_sent_task_keys,
    save_task_state,
)

from app.schemas.task_schema import TaskCreate
from app.services.task_service import create_task


def run_bot(
    db: Session,
    reprocess: bool = False,
):

    print("=" * 60)
    print("SMART EMAIL BOT")
    print("Reprocess mode:", reprocess)
    print("=" * 60)

    # ===================================================
    # Existing State
    # ===================================================

    sent_message_ids = get_sent_message_ids(db)
    sent_task_keys = get_sent_task_keys(db)

    # ===================================================
    # Fetch + Extract + Classify
    # ===================================================

    tasks = fetch_tasks(
        sent_message_ids=sent_message_ids,
        sent_task_keys=sent_task_keys,
        reprocess=reprocess,
    )

    print(
        "Extracted tasks:",
        len(tasks),
    )

    if not tasks:

        print("No tasks found.")

        return []

    # ===================================================
    # Calendar
    # ===================================================

    # During reprocessing, DO NOT create calendar events
    # again for old emails.

    if not reprocess:

        add_calendar_events(tasks)

    # ===================================================
    # Telegram
    # ===================================================

    # message = build_telegram_message(tasks)
    # send_telegram(message)

    # ===================================================
    # Save / Update Tasks
    # ===================================================

    for task in tasks:

        task_data = TaskCreate(

            title=task["label"],

            # Task type
            task_type=task["type"],

            # Basic fields
            priority="Medium",

            deadline=task["date"],

            message_id=task["message_id"],

            # Company / Role
            company=task.get("company"),

            role=task.get("role"),

            # Description
            description=task.get("description"),

            # Eligibility
            eligibility=task.get("eligibility"),

            branches=task.get("branches"),

            batch=task.get("batch"),

            # Package Details
            ctc=task.get("ctc"),

            stipend=task.get("stipend"),

            # Registration
            registration_link=task.get(
                "registration_link"
            ),

            # Event Details
            venue=task.get("venue"),

            location=task.get("location"),

            mode=task.get("mode"),

            # Process Details
            process=task.get("process"),

            contact=task.get("contact"),

            # Action
            action=task.get("action"),
        )

        # =================================================
        # Create or Update
        # =================================================

        create_task(
            db=db,
            task=task_data,
            update_existing=reprocess,
        )

        # =================================================
        # Save State
        # =================================================

        if not reprocess:

            task_key = make_task_key(
                task_type=task["type"],
                label=task["label"],
                date_text=task["date"],
            )

            save_task_state(
                db=db,
                message_id=task["message_id"],
                task_key=task_key,
            )

    print("=" * 60)

    print(
        "Bot completed.",
        "Tasks:",
        len(tasks),
    )

    print("=" * 60)

    return tasks