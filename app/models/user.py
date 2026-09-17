from sqlalchemy import Column, Integer, String

from app.models import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True)

    name = Column(String)

    google_id = Column(String)

    created_at = Column(String)