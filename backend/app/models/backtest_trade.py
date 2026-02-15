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


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    __table_args__ = (
        Index("ix_backtest_trades_backtest_run_id", "backtest_run_id"),
        CheckConstraint("side IN ('long', 'short')", name="ck_backtest_trades_side"),
    )

    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False)

    # Trade details
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)

    # Position info
    position_size = Column(Float, nullable=False)
    stop_loss_price = Column(Float, nullable=False)
    take_profit_price = Column(Float, nullable=False)

    # Results
    pnl = Column(Float, nullable=False)
    pnl_pct = Column(Float, nullable=False)
    is_winning = Column(Boolean, default=False)

    # Extra data
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="trades")
