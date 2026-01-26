from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True, nullable=False)  # e.g., "MA_RSI", "KELTNER", etc
    description = Column(Text, nullable=True)
    strategy_type = Column(String, nullable=False)  # Tipo de estrategia
    
    # Configuración de la estrategia (JSON para flexibilidad)
    config = Column(JSON, nullable=False)  # {fast_window, slow_window, ...}
    
    # Parámetros de backtesting
    initial_capital = Column(Integer, default=10000)
    stop_loss_pct = Column(Integer, default=2)
    take_profit_rr = Column(Integer, default=2)
    
    # Estado y metadatos
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_backtest_at = Column(DateTime, nullable=True)

    # Relaciones
    owner = relationship("User", back_populates="strategies")
    backtest_runs = relationship("BacktestRun", back_populates="strategy", cascade="all, delete-orphan")
    paper_trading_sessions = relationship("PaperTradingSession", back_populates="strategy")
