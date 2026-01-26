from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models import BacktestRun
from ...schemas import BacktestRun as BacktestRunSchema
from ...services import BacktestService

router = APIRouter()


@router.get("/", response_model=List[BacktestRunSchema])
async def list_backtests(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """List all backtest runs."""
    backtests = db.query(BacktestRun).offset(skip).limit(limit).all()
    return backtests


@router.post("/")
async def run_backtest(
    strategy_id: int,
    pair: str,
    timeframe: str = "15m",
    period: str = "60d",
    limit: int = 2000,
    db: Session = Depends(get_db),
    owner_id: int = 1,
):
    """Run a backtest for a strategy."""
    result = BacktestService.run_backtest(
        db=db,
        strategy_id=strategy_id,
        pair=pair,
        timeframe=timeframe,
        period=period,
        limit=limit,
        owner_id=owner_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{backtest_id}")
async def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """Get backtest results with all trades."""
    result = BacktestService.get_backtest_results(db, backtest_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
