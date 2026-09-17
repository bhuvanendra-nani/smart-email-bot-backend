from app.core.database import SessionLocal
from app.models.task import Task


def set_if_confirmed(task, field, value):
    if value is not None and str(value).strip():
        setattr(task, field, value)


def restore_tasks():
    db = SessionLocal()

    try:
        print("\nStarting task restoration...\n")

        # =========================================================
        # TASK 19 — EXXONMOBIL PPT + GROUP DISCUSSION
        # =========================================================
        task = db.query(Task).filter(Task.id == 19).first()

        if task:
            set_if_confirmed(task, "company", "ExxonMobil")
            set_if_confirmed(task, "deadline", "17-09-2026 08:00 AM")
            set_if_confirmed(task, "venue", "VIT Vellore")
            set_if_confirmed(task, "action", "Attend")
            set_if_confirmed(
                task,
                "description",
                (
                    "ExxonMobil PPT and Group Discussion scheduled on "
                    "17-09-2026 at 08:00 AM at VIT Vellore. "
                    "Students shortlisted through the Group Discussion "
                    "will have their Technical Interview on 18-09-2026 "
                    "at VIT Vellore."
                ),
            )
            set_if_confirmed(
                task,
                "process",
                "PPT + Group Discussion followed by Technical Interview",
            )

            print("Restored Task 19 - ExxonMobil")

        # =========================================================
        # TASK 29 — SANDISK
        # =========================================================
        task = db.query(Task).filter(Task.id == 29).first()

        if task:
            set_if_confirmed(task, "company", "Sandisk")
            set_if_confirmed(task, "stipend", "50,000")
            set_if_confirmed(
                task,
                "eligibility",
                (
                    "B.Tech students who are available from September "
                    "with no pending credits are eligible to register."
                ),
            )

            print("Restored Task 29 - Sandisk")

        # =========================================================
        # TASK 60 — COGNIZANT
        # =========================================================
        task = db.query(Task).filter(Task.id == 60).first()

        if task:
            set_if_confirmed(task, "company", "Cognizant")
            set_if_confirmed(task, "deadline", "11th September 2026")
            set_if_confirmed(task, "venue", "CB305*")
            set_if_confirmed(task, "action", "Take Test")

            print("Restored Task 60 - Cognizant")

        # =========================================================
        # TASK 65 — ELGI
        # =========================================================
        task = db.query(Task).filter(Task.id == 65).first()

        if task:
            set_if_confirmed(task, "company", "Elgi")
            set_if_confirmed(task, "deadline", "10-09-2026 by 5:30 PM")
            set_if_confirmed(task, "venue", "PRP - 717")
            set_if_confirmed(task, "action", "Take Test")

            set_if_confirmed(
                task,
                "description",
                (
                    "Elgi Online Test scheduled on 10-09-2026. "
                    "Candidates must take the test from the designated "
                    "campus labs. Vellore students must report to PRP-717. "
                    "Test starts sharply at 6:00 PM."
                ),
            )

            print("Restored Task 65 - Elgi")

        db.commit()

        print("\n========================================")
        print("TASK RESTORATION COMPLETED")
        print("========================================\n")

    except Exception as e:
        db.rollback()

        print("\n========================================")
        print("RESTORATION FAILED")
        print("========================================")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    restore_tasks()