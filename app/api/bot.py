from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.bot_service import run_bot

router = APIRouter(
    prefix="/bot",
    tags=["Bot"],
)


@router.post("/run")
def run_email_bot(
    reprocess: bool = False,
    db: Session = Depends(get_db),
):
    tasks = run_bot(db, reprocess=reprocess)

    grouped = {
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
        task_type = task["type"]

        if task_type in internship_types:
            group = "Internship"

        elif task_type in placement_types:
            group = "Placement"

        elif task_type == "Online Test":
            group = "Online Test"

        elif task_type in academic_types:
            group = "Academics"

        else:
            group = "Other"

        grouped[group].append(task)

    return {
        "status": "success",
        "reprocess": reprocess,
        "tasks_found": len(tasks),
        "groups": grouped,
    }