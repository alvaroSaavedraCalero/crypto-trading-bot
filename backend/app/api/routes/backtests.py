import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from typing import List

from ...database import get_db
from ...models import BacktestRun, User
from ...schemas import BacktestRun as BacktestRunSchema
from ...services import BacktestService
from ..auth import get_current_user

router = APIRouter()

MAX_LIMIT = 1000


class BacktestRunRequest(BaseModel):
    strategy_id: int
    pair: str
    timeframe: str = "15m"
    period: str = "60d"
    limit: int = 2000


@router.get("", response_model=List[BacktestRunSchema])
async def list_backtests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all backtest runs for the authenticated user."""
    limit = min(limit, MAX_LIMIT)
    backtests = (
        db.query(BacktestRun)
        .options(joinedload(BacktestRun.strategy))
        .filter(BacktestRun.owner_id == current_user.id)
        .order_by(BacktestRun.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    # Inject strategy_type from related strategy
    results = []
    for bt in backtests:
        bt_dict = {
            "id": bt.id,
            "owner_id": bt.owner_id,
            "strategy_id": bt.strategy_id,
            "pair": bt.pair,
            "timeframe": bt.timeframe,
            "start_date": bt.start_date,
            "end_date": bt.end_date,
            "total_return_pct": bt.total_return_pct,
            "winrate_pct": bt.winrate_pct,
            "profit_factor": bt.profit_factor,
            "max_drawdown_pct": bt.max_drawdown_pct,
            "num_trades": bt.num_trades,
            "winning_trades": bt.winning_trades,
            "losing_trades": bt.losing_trades,
            "backtest_config": bt.backtest_config,
            "strategy_config": bt.strategy_config,
            "created_at": bt.created_at,
            "notes": bt.notes,
            "strategy_type": bt.strategy.strategy_type.value if bt.strategy else None,
        }
        results.append(bt_dict)
    return results


@router.post("")
async def run_backtest(
    body: BacktestRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a backtest for a strategy (async)."""
    result = await asyncio.to_thread(
        BacktestService.run_backtest,
        db=db,
        strategy_id=body.strategy_id,
        pair=body.pair,
        timeframe=body.timeframe,
        period=body.period,
        limit=body.limit,
        owner_id=current_user.id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{backtest_id}")
async def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get backtest results with all trades."""
    result = BacktestService.get_backtest_results(db, backtest_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Verify ownership
    backtest = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == backtest_id, BacktestRun.owner_id == current_user.id)
        .first()
    )
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return result


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a backtest run and its trades (owner-checked)."""
    backtest = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == backtest_id, BacktestRun.owner_id == current_user.id)
        .first()
    )
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    db.delete(backtest)
    db.commit()
    return {"detail": "Backtest deleted"}
