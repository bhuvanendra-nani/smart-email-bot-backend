from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Boolean

from app.models import Base


class Setting(Base):

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)

    telegram_enabled = Column(Boolean)

    calendar_enabled = Column(Boolean)

    default_reminder = Column(Integer)