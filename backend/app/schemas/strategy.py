from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_type: str
    config: Dict[str, Any]
    initial_capital: Optional[float] = 10000.0
    stop_loss_pct: Optional[float] = 2.0
    take_profit_rr: Optional[float] = 2.0


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Strategy(StrategyBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_backtest_at: Optional[datetime] = None

    class Config:
        from_attributes = True


from .backtest import BacktestRun


class StrategyWithBacktests(Strategy):
    backtest_runs: List[BacktestRun] = []

    class Config:
        from_attributes = True
