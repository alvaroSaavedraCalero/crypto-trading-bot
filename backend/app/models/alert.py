import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
    Enum,
    Index,
    func,
)
from .base import Base


class AlertType(str, enum.Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PCT_CHANGE = "pct_change"
    VOLUME_SPIKE = "volume_spike"


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_owner_id", "owner_id"),
        Index("ix_alerts_symbol", "symbol"),
        Index("ix_alerts_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    threshold = Column(Float, nullable=False)
    message = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
