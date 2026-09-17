import re

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task_schema import TaskCreate


# ============================================================
# Helpers
# ============================================================

GENERIC_TITLE_WORDS = {
    "reminder",
    "update",
    "updated",
    "important",
    "notice",
    "notification",
    "congratulations",
    "congrats",
    "regarding",
    "information",
    "announcement",
    "urgent",
    "attention",
}


def normalize_text(value):
    """
    Normalize text only for comparison.

    Examples:
        "Reminder: Sandisk Online Test"
        "Re: Sandisk Online Test"

    become comparable.
    """

    if not value:
        return ""

    value = str(value).strip().lower()

    previous = None

    while value != previous:
        previous = value

        value = re.sub(
            r"^(re|fw|fwd|forwarded|reminder)\s*:\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


def values_match(value1, value2):
    value1 = normalize_text(value1)
    value2 = normalize_text(value2)

    if not value1 or not value2:
        return False

    return value1 == value2


def is_meaningful(value):
    """
    True only when the value contains useful information.
    """

    if value is None:
        return False

    value = str(value).strip()

    if not value:
        return False

    if value.lower() in {
        "not mentioned",
        "not available",
        "n/a",
        "na",
        "none",
        "null",
    }:
        return False

    return True


def title_is_generic(title):
    """
    Detect titles that are too generic to identify an event.
    """

    normalized = normalize_text(title)

    if not normalized:
        return True

    words = set(normalized.split())

    # If title consists almost entirely of generic words,
    # it must never be used for event-level merging.
    meaningful_words = words - GENERIC_TITLE_WORDS

    return len(meaningful_words) == 0


def title_words(title):
    normalized = normalize_text(title)

    if not normalized:
        return set()

    return {
        word
        for word in normalized.split()
        if len(word) >= 3
    }


def title_similarity(title1, title2):
    """
    Simple word-overlap similarity.

    Returns a value between 0 and 1.
    """

    words1 = title_words(title1)
    words2 = title_words(title2)

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)

    return len(intersection) / min(
        len(words1),
        len(words2),
    )


# ============================================================
# Event Matching
# ============================================================

def find_event_match(
    db: Session,
    task: TaskCreate,
):
    """
    Find an existing task representing the SAME real-world event.

    Important:
    This function must be conservative.

    A false positive is much worse than creating a duplicate,
    because a false positive can corrupt an existing task with
    information from an unrelated email.
    """

    if not task.task_type:
        return None

    normalized_title = normalize_text(task.title)
    normalized_company = normalize_text(task.company)

    if not normalized_title:
        return None

    # --------------------------------------------------------
    # Generic titles are never enough for event matching.
    # --------------------------------------------------------

    if title_is_generic(task.title):
        return None

    candidates = (
        db.query(Task)
        .filter(
            Task.task_type == task.task_type
        )
        .all()
    )

    best_match = None
    best_score = 0

    for existing in candidates:

        existing_title = normalize_text(existing.title)
        existing_company = normalize_text(existing.company)

        if not existing_title:
            continue

        # ----------------------------------------------------
        # COMPANY SAFETY
        # ----------------------------------------------------
        # If BOTH sides have a company and they differ,
        # this can NEVER be the same event.
        #
        # This is the most important protection against
        # cross-company contamination.
        # ----------------------------------------------------

        if normalized_company and existing_company:

            if normalized_company != existing_company:
                continue

        # ----------------------------------------------------
        # Never match a generic existing title.
        # ----------------------------------------------------

        if title_is_generic(existing.title):
            continue

        # ----------------------------------------------------
        # Exact title match
        # ----------------------------------------------------

        if normalized_title == existing_title:

            # Exact title + same company is very strong.
            if normalized_company and existing_company:

                return existing

            # Both have no company.
            if not normalized_company and not existing_company:

                return existing

            # One side has company.
            # Do NOT merge automatically.
            continue

        # ----------------------------------------------------
        # If both companies are missing, be conservative.
        # ----------------------------------------------------

        if not normalized_company and not existing_company:
            continue

        # ----------------------------------------------------
        # Company must exist on both sides for fuzzy matching.
        # ----------------------------------------------------

        if not normalized_company or not existing_company:
            continue

        # At this point companies are already equal.

        # ----------------------------------------------------
        # Strong title similarity
        # ----------------------------------------------------

        similarity = title_similarity(
            task.title,
            existing.title,
        )

        # Require substantial overlap.
        if similarity < 0.75:
            continue

        # ----------------------------------------------------
        # Additional protection:
        #
        # One title should not merely be a tiny prefix of another.
        # Require at least 2 meaningful common words.
        # ----------------------------------------------------

        common_words = (
            title_words(task.title)
            .intersection(
                title_words(existing.title)
            )
        )

        if len(common_words) < 2:
            continue

        score = similarity

        if score > best_score:
            best_score = score
            best_match = existing

    return best_match


# ============================================================
# Create / Update Task
# ============================================================

def create_task(
    db: Session,
    task: TaskCreate,
    update_existing: bool = False,
):

    print(
        "Inside create_task:",
        task.title,
    )

    # ========================================================
    # 1. Exact Gmail message match
    # ========================================================

    existing_task = (
        db.query(Task)
        .filter(
            Task.message_id == task.message_id
        )
        .first()
    )

    # ========================================================
    # 2. Existing exact message
    # ========================================================

    if existing_task:

        if not update_existing:

            print(
                "Task already exists:",
                existing_task.id,
            )

            return existing_task

        print(
            "Updating existing task:",
            existing_task.id,
        )

        update_task_fields(
            existing_task,
            task,
        )

        db.commit()
        db.refresh(existing_task)

        return existing_task

    # ========================================================
    # 3. Event-level duplicate detection
    # ========================================================

    event_match = find_event_match(
        db=db,
        task=task,
    )

    if event_match:

        print(
            "Same event already exists:",
            event_match.id,
        )

        print(
            "Existing message:",
            event_match.message_id,
        )

        print(
            "New message:",
            task.message_id,
        )

        if update_existing:

            update_task_fields(
                event_match,
                task,
            )

            db.commit()
            db.refresh(event_match)

        return event_match

    # ========================================================
    # 4. Create completely new task
    # ========================================================

    new_task = Task(

        title=task.title,

        task_type=task.task_type,

        company=task.company,
        role=task.role,

        action=task.action,
        description=task.description,

        eligibility=task.eligibility,
        branches=task.branches,
        batch=task.batch,

        ctc=task.ctc,
        stipend=task.stipend,

        registration_link=task.registration_link,

        venue=task.venue,
        location=task.location,
        mode=task.mode,

        process=task.process,
        contact=task.contact,

        priority=task.priority,
        deadline=task.deadline,

        message_id=task.message_id,
    )

    db.add(new_task)

    db.commit()
    db.refresh(new_task)

    print(
        "Created new task:",
        new_task.id,
    )

    return new_task


# ============================================================
# Safe Update Helpers
# ============================================================

def update_if_missing(
    existing_task: Task,
    field: str,
    new_value,
):
    """
    Fill a field only when the existing value is missing.

    This prevents later emails from replacing correct data.
    """

    if not is_meaningful(new_value):
        return

    current_value = getattr(
        existing_task,
        field,
        None,
    )

    if not is_meaningful(current_value):

        setattr(
            existing_task,
            field,
            new_value,
        )


def update_if_better(
    existing_task: Task,
    field: str,
    new_value,
):
    """
    Used only for fields where a later email may legitimately
    provide a more useful value.

    Never replace a useful value with 'Not mentioned'.
    """

    if not is_meaningful(new_value):
        return

    current_value = getattr(
        existing_task,
        field,
        None,
    )

    if not is_meaningful(current_value):

        setattr(
            existing_task,
            field,
            new_value,
        )


# ============================================================
# Update Existing Task
# ============================================================

def update_task_fields(
    existing_task: Task,
    task: TaskCreate,
):
    """
    Safely merge information from another email belonging
    to the SAME event.

    IMPORTANT:

    - Do NOT blindly overwrite existing information.
    - Missing fields can be filled.
    - Real deadlines are protected.
    - Company / role / salary / eligibility are protected.
    """

    # --------------------------------------------------------
    # Core
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "task_type",
        task.task_type,
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------
    # Keep the original useful title.

    update_if_missing(
        existing_task,
        "title",
        task.title,
    )

    # --------------------------------------------------------
    # Company
    # --------------------------------------------------------
    # Company should almost never change after creation.

    update_if_missing(
        existing_task,
        "company",
        task.company,
    )

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "role",
        task.role,
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "description",
        task.description,
    )

    # --------------------------------------------------------
    # Eligibility
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "eligibility",
        task.eligibility,
    )

    # --------------------------------------------------------
    # Branches
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "branches",
        task.branches,
    )

    # --------------------------------------------------------
    # Batch
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "batch",
        task.batch,
    )

    # --------------------------------------------------------
    # Salary
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "ctc",
        task.ctc,
    )

    update_if_missing(
        existing_task,
        "stipend",
        task.stipend,
    )

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "registration_link",
        task.registration_link,
    )

    # --------------------------------------------------------
    # Event
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "venue",
        task.venue,
    )

    update_if_missing(
        existing_task,
        "location",
        task.location,
    )

    update_if_missing(
        existing_task,
        "mode",
        task.mode,
    )

    # --------------------------------------------------------
    # Hiring
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "process",
        task.process,
    )

    update_if_missing(
        existing_task,
        "contact",
        task.contact,
    )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    update_if_missing(
        existing_task,
        "priority",
        task.priority,
    )

    # --------------------------------------------------------
    # Deadline
    # --------------------------------------------------------
    # A later email can provide a deadline when the old task
    # did not have one.
    #
    # But "Not mentioned" can NEVER replace a real deadline.

    update_if_missing(
        existing_task,
        "deadline",
        task.deadline,
    )

    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------
    # Only fill action when missing.
    #
    # This prevents:
    #   Take Test
    # becoming
    #   Attend
    #
    # merely because a reminder email was processed later.

    update_if_missing(
        existing_task,
        "action",
        task.action,
    )

    # --------------------------------------------------------
    # Gmail message
    # --------------------------------------------------------
    # Keep the newest message as representative message.

    if is_meaningful(task.message_id):

        existing_task.message_id = task.message_id


# ============================================================
# Get All Tasks
# ============================================================

def get_all_tasks(db: Session):

    tasks = (
        db.query(Task)
        .order_by(Task.id.desc())
        .all()
    )

    groups = {
        "Internship": [],
        "Placement": [],
        "Online Test": [],
        "Academics": [],
        "Other": [],
    }

    internship_types = {
        "Internship Registration",
        "Internship Selection",
    }

    placement_types = {
        "Placement Registration",
        "Placement Selection",
    }

    academic_types = {
        "Quiz",
        "Assignment",
        "Lab",
        "Lab Assignment",
        "PPT",
        "Notes",
        "Test",
        "Marks Update",
    }

    for task in tasks:

        if task.task_type in internship_types:

            group = "Internship"

        elif task.task_type in placement_types:

            group = "Placement"

        elif task.task_type == "Online Test":

            group = "Online Test"

        elif task.task_type in academic_types:

            group = "Academics"

        else:

            group = "Other"

        groups[group].append({

            "id": task.id,

            "title": task.title,

            "task_type": task.task_type,

            "company": task.company,
            "role": task.role,

            "action": task.action,
            "description": task.description,

            "eligibility": task.eligibility,
            "branches": task.branches,
            "batch": task.batch,

            "ctc": task.ctc,
            "stipend": task.stipend,

            "registration_link": (
                task.registration_link
            ),

            "venue": task.venue,
            "location": task.location,
            "mode": task.mode,

            "process": task.process,
            "contact": task.contact,

            "priority": task.priority,
            "deadline": task.deadline,
            "completed": task.completed,

            "message_id": task.message_id,
        })

    return groups