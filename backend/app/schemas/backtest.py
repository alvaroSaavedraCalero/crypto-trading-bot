from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class BacktestTradeBase(BaseModel):
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: float
    exit_price: float
    position_size: float
    stop_loss_price: float
    take_profit_price: float
    pnl: float
    pnl_pct: float
    is_winning: int


class BacktestTrade(BacktestTradeBase):
    id: int
    backtest_run_id: int
    extra_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestRunBase(BaseModel):
    pair: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_return_pct: float
    winrate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    backtest_config: Dict[str, Any]
    strategy_config: Dict[str, Any]


class BacktestRunCreate(BaseModel):
    pair: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    strategy_id: int


class BacktestRun(BacktestRunBase):
    id: int
    owner_id: int
    strategy_id: int
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BacktestRunWithTrades(BacktestRun):
    trades: List[BacktestTrade] = []

    class Config:
        from_attributes = True
