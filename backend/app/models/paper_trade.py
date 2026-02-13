from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from .base import Base


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    paper_trading_session_id = Column(Integer, ForeignKey("paper_trading_sessions.id"), nullable=False)
    
    # Trade details
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)  # Null si está abierto
    side = Column(String, nullable=False)  # "long" or "short"
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)  # Null si está abierto
    
    # Position info
    position_size = Column(Float, nullable=False)
    stop_loss_price = Column(Float, nullable=False)
    take_profit_price = Column(Float, nullable=False)
    
    # Results (actualizado en real-time)
    pnl = Column(Float, default=0.0)  # P&L en dinero
    pnl_pct = Column(Float, default=0.0)  # P&L en porcentaje
    is_winning = Column(Integer, nullable=True)  # 1 si ganador, 0 si perdedor, None si abierto
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Relaciones
    paper_trading_session = relationship("PaperTradingSession", back_populates="trades")
