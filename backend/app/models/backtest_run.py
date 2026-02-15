from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import relationship
from .base import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (
        Index("ix_backtest_runs_owner_id", "owner_id"),
        Index("ix_backtest_runs_strategy_id", "strategy_id"),
        Index("ix_backtest_runs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)

    # Backtest info
    pair = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Results
    total_return_pct = Column(Float, nullable=False)
    winrate_pct = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    max_drawdown_pct = Column(Float, nullable=False)
    num_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # Configuration used
    backtest_config = Column(JSON, nullable=False)
    strategy_config = Column(JSON, nullable=False)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    notes = Column(String, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="backtest_runs")
    strategy = relationship("Strategy", back_populates="backtest_runs")
    trades = relationship(
        "BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan"
    )
