from sqlalchemy import Column, Integer, String

from app.models import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String,
        nullable=True
    )

    google_id = Column(
        String,
        unique=True,
        nullable=True,
        index=True
    )

    picture = Column(
        String,
        nullable=True
    )

    access_token = Column(
        String,
        nullable=True
    )

    refresh_token = Column(
        String,
        nullable=True
    )

    token_expiry = Column(
        String,
        nullable=True
    )

    created_at = Column(
        String,
        nullable=True
    )