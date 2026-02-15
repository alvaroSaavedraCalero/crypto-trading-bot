from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Index,
    UniqueConstraint,
    func,
)
from .base import Base


class MarketDataCache(Base):
    __tablename__ = "market_data_cache"
    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_market_data_point"),
        Index("ix_market_data_symbol", "symbol"),
        Index("ix_market_data_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
