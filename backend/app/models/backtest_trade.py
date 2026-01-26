from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from .base import Base


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False)
    
    # Trade details
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    side = Column(String, nullable=False)  # "long" or "short"
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    
    # Position info
    position_size = Column(Float, nullable=False)
    stop_loss_price = Column(Float, nullable=False)
    take_profit_price = Column(Float, nullable=False)
    
    # Results
    pnl = Column(Float, nullable=False)  # P&L en dinero
    pnl_pct = Column(Float, nullable=False)  # P&L en porcentaje
    is_winning = Column(Integer, default=0)  # 1 si ganador, 0 si perdedor
    
    # Extra data
    metadata = Column(JSON, nullable=True)  # Información adicional del trade
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    backtest_run = relationship("BacktestRun", back_populates="trades")
