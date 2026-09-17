from fastapi import APIRouter
from app.services.gmail_service import get_latest_tasks

router = APIRouter()


@router.get("/sync")
def sync_gmail():
    """
    Read Gmail and return newly detected tasks.
    """

    tasks = get_latest_tasks()

    return {
        "count": len(tasks),
        "tasks": tasks
    }