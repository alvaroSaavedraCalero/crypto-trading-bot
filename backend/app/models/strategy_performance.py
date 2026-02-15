from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Index,
    func,
)
from .base import Base


class StrategyPerformance(Base):
    __tablename__ = "strategy_performances"
    __table_args__ = (
        Index("ix_strategy_performances_strategy_id", "strategy_id"),
        Index("ix_strategy_performances_recorded_at", "recorded_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    pair = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)

    # Performance metrics
    total_return_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)
    winrate_pct = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    avg_trade_pnl = Column(Float, nullable=True)
    num_trades = Column(Integer, default=0)

    recorded_at = Column(DateTime, server_default=func.now())
