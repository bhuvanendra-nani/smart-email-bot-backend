from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Task(Base):

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    task_type: Mapped[str] = mapped_column(
        String(100)
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        default="Medium"
    )

    deadline: Mapped[str] = mapped_column(
        String(100)
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    calendar_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    message_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    # ==========================
    # COMPANY DETAILS
    # ==========================

    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    role: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ==========================
    # ELIGIBILITY DETAILS
    # ==========================

    eligibility: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    branches: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    batch: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # ==========================
    # SALARY DETAILS
    # ==========================

    ctc: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    stipend: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # ==========================
    # REGISTRATION DETAILS
    # ==========================

    registration_link: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ==========================
    # EVENT DETAILS
    # ==========================

    venue: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    mode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # ==========================
    # PROCESS DETAILS
    # ==========================

    process: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    contact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    action: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )


class BotState(Base):

    __tablename__ = "bot_state"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    message_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True
    )

    task_key: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    calendar_key: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    batch: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    process: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    contact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    action: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )