from app.core.database import SessionLocal
from app.models.task import Task


# ============================================================
# Duplicate groups confirmed as safe
# ============================================================

DUPLICATE_GROUPS = {
    # Keep 29
    29: [37, 77],

    # Keep 60
    60: [41, 43, 44, 46, 59],

    # Keep 65
    65: [45, 49],

    # Keep 19
    19: [75],
}


# ============================================================
# Merge useful data before deleting duplicates
# ============================================================

def merge_missing_fields(keep, duplicate):

    fields = [
        "company",
        "role",
        "description",
        "eligibility",
        "branches",
        "batch",
        "ctc",
        "stipend",
        "registration_link",
        "venue",
        "location",
        "mode",
        "process",
        "contact",
        "action",
        "deadline",
    ]

    for field in fields:

        current = getattr(keep, field)
        incoming = getattr(duplicate, field)

        if not current and incoming:
            setattr(keep, field, incoming)

    # Preserve calendar event if duplicate has one
    if not keep.calendar_event_id and duplicate.calendar_event_id:
        keep.calendar_event_id = duplicate.calendar_event_id

    # Preserve completed status
    if duplicate.completed:
        keep.completed = True


# ============================================================
# Main cleanup
# ============================================================

def cleanup():

    db = SessionLocal()

    try:

        print("\nStarting duplicate cleanup...\n")

        for keep_id, duplicate_ids in DUPLICATE_GROUPS.items():

            keep = (
                db.query(Task)
                .filter(Task.id == keep_id)
                .first()
            )

            if not keep:
                print(
                    f"KEEP task {keep_id} not found."
                )
                continue

            print(
                f"\nKEEP: {keep.id} | "
                f"{keep.task_type} | "
                f"{keep.title}"
            )

            for duplicate_id in duplicate_ids:

                duplicate = (
                    db.query(Task)
                    .filter(Task.id == duplicate_id)
                    .first()
                )

                if not duplicate:
                    print(
                        f"  SKIP {duplicate_id} "
                        f"(already missing)"
                    )
                    continue

                print(
                    f"  MERGE + DELETE: "
                    f"{duplicate.id} | "
                    f"{duplicate.title}"
                )

                merge_missing_fields(
                    keep,
                    duplicate,
                )

                db.delete(duplicate)

        db.commit()

        print("\nDuplicate cleanup completed.")
        print("Database committed successfully.\n")

    except Exception as e:

        db.rollback()

        print(
            "\nERROR:"
        )

        print(e)

        print(
            "\nNo changes were committed."
        )

    finally:

        db.close()


if __name__ == "__main__":
    cleanup()