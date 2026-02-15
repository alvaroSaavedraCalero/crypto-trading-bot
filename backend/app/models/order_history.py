import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Enum,
    JSON,
    Index,
    func,
)
from .base import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderHistory(Base):
    __tablename__ = "order_history"
    __table_args__ = (
        Index("ix_order_history_owner_id", "owner_id"),
        Index("ix_order_history_symbol", "symbol"),
        Index("ix_order_history_status", "status"),
        Index("ix_order_history_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    filled_quantity = Column(Float, default=0.0)
    filled_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
