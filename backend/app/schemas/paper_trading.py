from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class PaperTradeBase(BaseModel):
    entry_time: datetime
    exit_time: Optional[datetime] = None
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    position_size: float
    stop_loss_price: float
    take_profit_price: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    is_winning: Optional[int] = None


class PaperTrade(PaperTradeBase):
    id: int
    paper_trading_session_id: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaperTradingSessionBase(BaseModel):
    name: str
    pair: str
    timeframe: str
    initial_capital: float
    current_capital: float
    strategy_config: Dict[str, Any]
    backtest_config: Dict[str, Any]


class PaperTradingSessionCreate(BaseModel):
    name: str
    strategy_id: int
    pair: str
    timeframe: str


class PaperTradingSessionUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class PaperTradingSession(PaperTradingSessionBase):
    id: int
    owner_id: int
    strategy_id: int
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    is_active: bool
    start_date: datetime
    end_date: Optional[datetime] = None
    last_update: datetime

    class Config:
        from_attributes = True


class PaperTradingSessionWithTrades(PaperTradingSession):
    trades: List[PaperTrade] = []

    class Config:
        from_attributes = True
