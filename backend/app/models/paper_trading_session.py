from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class PaperTradingSession(Base):
    __tablename__ = "paper_trading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Session info
    name = Column(String, nullable=False)
    pair = Column(String, nullable=False)  # e.g., "EURUSD", "USDJPY"
    timeframe = Column(String, nullable=False)  # e.g., "15m"
    
    # Capital
    initial_capital = Column(Float, nullable=False)
    current_capital = Column(Float, nullable=False)
    
    # Results
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_return_pct = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration used
    strategy_config = Column(JSON, nullable=False)
    backtest_config = Column(JSON, nullable=False)

    # Relaciones
    owner = relationship("User", back_populates="paper_trading_sessions")
    strategy = relationship("Strategy", back_populates="paper_trading_sessions")
    trades = relationship("PaperTrade", back_populates="paper_trading_session", cascade="all, delete-orphan")
