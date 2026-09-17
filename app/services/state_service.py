
from sqlalchemy.orm import Session

from app.models.task import BotState


# ============================================================
# Get Processed Message IDs
# ============================================================

def get_sent_message_ids(db: Session):

    rows = db.query(BotState).all()

    return {
        row.message_id
        for row in rows
        if row.message_id
    }


# ============================================================
# Get Processed Task Keys
# ============================================================

def get_sent_task_keys(db: Session):

    rows = db.query(BotState).all()

    return {
        row.task_key
        for row in rows
        if row.task_key
    }


# ============================================================
# Get Calendar Keys
# ============================================================

def get_calendar_keys(db: Session):

    rows = db.query(BotState).all()

    return {
        row.calendar_key
        for row in rows
        if row.calendar_key
    }


# ============================================================
# Save / Update Task State
# ============================================================

def save_task_state(
    db: Session,
    message_id: str,
    task_key: str,
    calendar_key: str | None = None,
):

    # --------------------------------------------------------
    # 1. Check whether this exact Gmail message already exists
    # --------------------------------------------------------

    existing_message = (
        db.query(BotState)
        .filter(
            BotState.message_id == message_id
        )
        .first()
    )

    if existing_message:

        # If the same message is being processed again,
        # update its task information safely.

        existing_message.task_key = task_key

        if calendar_key:
            existing_message.calendar_key = calendar_key

        db.commit()

        return existing_message

    # --------------------------------------------------------
    # 2. Check whether this task_key already exists
    # --------------------------------------------------------

    existing_task = (
        db.query(BotState)
        .filter(
            BotState.task_key == task_key
        )
        .first()
    )

    if existing_task:

        # The task already has a state entry.
        #
        # Do NOT create another row because task_key is UNIQUE.
        #
        # The Task table already handles event-level matching,
        # so we only need one BotState entry for the same task.

        if calendar_key and not existing_task.calendar_key:
            existing_task.calendar_key = calendar_key
            db.commit()

        return existing_task

    # --------------------------------------------------------
    # 3. Create completely new state
    # --------------------------------------------------------

    state = BotState(
        message_id=message_id,
        task_key=task_key,
        calendar_key=calendar_key,
    )

    db.add(state)
    db.commit()

    return state

