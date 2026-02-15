import enum

from sqlalchemy import (
    Column,
    Enum,
    Float,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from .base import Base


class StrategyType(str, enum.Enum):
    MA_RSI = "MA_RSI"
    MACD_ADX = "MACD_ADX"
    KELTNER = "KELTNER"
    BB_TREND = "BB_TREND"
    SQUEEZE = "SQUEEZE"
    SUPERTREND = "SUPERTREND"
    BOLLINGER_MR = "BOLLINGER_MR"
    SMART_MONEY = "SMART_MONEY"
    ICT = "ICT"
    AI_RF = "AI_RF"


class Strategy(Base):
    __tablename__ = "strategies"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_strategy_owner_name"),
        Index("ix_strategies_owner_id", "owner_id"),
        Index("ix_strategies_strategy_type", "strategy_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(Enum(StrategyType), nullable=False)

    # Strategy configuration (JSON for flexibility)
    config = Column(JSON, nullable=False)

    # Backtesting parameters
    initial_capital = Column(Float, default=10000.0)
    stop_loss_pct = Column(Float, default=2.0)
    take_profit_rr = Column(Float, default=2.0)

    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_backtest_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="strategies")
    backtest_runs = relationship(
        "BacktestRun", back_populates="strategy", cascade="all, delete-orphan"
    )
    paper_trading_sessions = relationship(
        "PaperTradingSession", back_populates="strategy", cascade="all, delete-orphan"
    )
