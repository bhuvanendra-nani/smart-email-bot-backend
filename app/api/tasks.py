from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.task_service import get_all_tasks
from app.models.task import Task

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.get("/")
def read_tasks(db: Session = Depends(get_db)):
    return get_all_tasks(db)


@router.patch("/{task_id}/complete")
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task.completed = True
    db.commit()
    db.refresh(task)

    return {
        "message": "Task completed",
        "task": task,
    }