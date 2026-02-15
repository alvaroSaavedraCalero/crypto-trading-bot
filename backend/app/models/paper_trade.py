import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    JSON,
    Boolean,
    Enum,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship
from .base import Base


class TradeSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class PaperTrade(Base):
    __tablename__ = "paper_trades"
    __table_args__ = (
        Index("ix_paper_trades_session_id", "paper_trading_session_id"),
        CheckConstraint("side IN ('long', 'short')", name="ck_paper_trades_side"),
    )

    id = Column(Integer, primary_key=True, index=True)
    paper_trading_session_id = Column(
        Integer, ForeignKey("paper_trading_sessions.id"), nullable=False
    )

    # Trade details
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    side = Column(Enum(TradeSide), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)

    # Position info
    position_size = Column(Float, nullable=False)
    stop_loss_price = Column(Float, nullable=False)
    take_profit_price = Column(Float, nullable=False)

    # Results (updated in real-time)
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    is_winning = Column(Boolean, nullable=True)

    # Extra data
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    paper_trading_session = relationship("PaperTradingSession", back_populates="trades")
