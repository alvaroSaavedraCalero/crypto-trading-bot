from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from .base import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Información del backtest
    pair = Column(String, nullable=False)  # e.g., "EURUSD", "USDJPY"
    timeframe = Column(String, nullable=False)  # e.g., "15m", "1h"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Resultados
    total_return_pct = Column(Float, nullable=False)
    winrate_pct = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    max_drawdown_pct = Column(Float, nullable=False)
    num_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Configuración usada
    backtest_config = Column(JSON, nullable=False)  # {initial_capital, sl_pct, tp_rr, ...}
    strategy_config = Column(JSON, nullable=False)  # Configuración de la estrategia en este backtest
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)

    # Relaciones
    owner = relationship("User", back_populates="backtest_runs")
    strategy = relationship("Strategy", back_populates="backtest_runs")
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")
