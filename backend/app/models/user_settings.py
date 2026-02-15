from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    func,
)
from .base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        Index("ix_user_settings_owner_id", "owner_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    default_pair = Column(String, default="BTC-USD")
    default_timeframe = Column(String, default="1h")
    default_capital = Column(String, default="10000")
    theme = Column(String, default="dark")
    notifications_enabled = Column(String, default="true")
    extra_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
