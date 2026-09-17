from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    title: str

    task_type: str

    priority: str = "Medium"

    deadline: str

    message_id: Optional[str] = None

    company: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None

    eligibility: Optional[str] = None
    branches: Optional[str] = None
    batch: Optional[str] = None

    ctc: Optional[str] = None
    stipend: Optional[str] = None

    registration_link: Optional[str] = None

    venue: Optional[str] = None
    location: Optional[str] = None
    mode: Optional[str] = None

    process: Optional[str] = None
    contact: Optional[str] = None

    action: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None

    task_type: Optional[str] = None

    priority: Optional[str] = None
    deadline: Optional[str] = None
    completed: Optional[bool] = None

    company: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None

    eligibility: Optional[str] = None
    branches: Optional[str] = None
    batch: Optional[str] = None

    ctc: Optional[str] = None
    stipend: Optional[str] = None

    registration_link: Optional[str] = None

    venue: Optional[str] = None
    location: Optional[str] = None
    mode: Optional[str] = None

    process: Optional[str] = None
    contact: Optional[str] = None

    action: Optional[str] = None


class TaskResponse(BaseModel):
    id: int

    title: str
    task_type: str
    priority: str
    deadline: str
    completed: bool

    calendar_event_id: Optional[str]
    message_id: Optional[str]

    company: Optional[str]
    role: Optional[str]
    description: Optional[str]

    eligibility: Optional[str]
    branches: Optional[str]
    batch: Optional[str]

    ctc: Optional[str]
    stipend: Optional[str]

    registration_link: Optional[str]

    venue: Optional[str]
    location: Optional[str]
    mode: Optional[str]

    process: Optional[str]
    contact: Optional[str]

    action: Optional[str]

    model_config = {
        "from_attributes": True
    }