from sqlalchemy import Column, Integer, String, Text

from app.models import Base


class Email(Base):

    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)

    gmail_id = Column(String, unique=True)

    subject = Column(String)

    sender = Column(String)

    body = Column(Text)

    received_time = Column(String)

    processed = Column(String)