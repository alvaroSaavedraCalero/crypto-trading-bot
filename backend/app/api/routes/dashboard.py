from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from ...database import get_db
from ...models import Strategy, BacktestRun, PaperTradingSession, User
from ..auth import get_current_user

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics."""
    owner_id = current_user.id

    total_strategies = (
        db.query(func.count(Strategy.id))
        .filter(Strategy.owner_id == owner_id)
        .scalar()
        or 0
    )

    active_backtests = (
        db.query(func.count(BacktestRun.id))
        .filter(BacktestRun.owner_id == owner_id)
        .scalar()
        or 0
    )

    paper_trading_sessions = (
        db.query(func.count(PaperTradingSession.id))
        .filter(
            PaperTradingSession.owner_id == owner_id,
            PaperTradingSession.is_active == True,
        )
        .scalar()
        or 0
    )

    total_trades = (
        db.query(func.sum(PaperTradingSession.total_trades))
        .filter(PaperTradingSession.owner_id == owner_id)
        .scalar()
        or 0
    )

    portfolio_session = (
        db.query(PaperTradingSession)
        .filter(
            PaperTradingSession.owner_id == owner_id,
            PaperTradingSession.is_active == True,
        )
        .first()
    )

    portfolio_value = portfolio_session.current_capital if portfolio_session else 10000.0
    daily_return = portfolio_session.total_return_pct if portfolio_session else 0.0

    return {
        "total_strategies": total_strategies,
        "active_backtests": active_backtests,
        "paper_trading_sessions": paper_trading_sessions,
        "total_trades": int(total_trades),
        "portfolio_value": portfolio_value,
        "daily_return": daily_return,
    }


@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary data for dashboard."""
    owner_id = current_user.id

    recent_backtests = (
        db.query(BacktestRun)
        .options(joinedload(BacktestRun.strategy))
        .filter(BacktestRun.owner_id == owner_id)
        .order_by(BacktestRun.created_at.desc())
        .limit(5)
        .all()
    )

    active_sessions = (
        db.query(PaperTradingSession)
        .filter(
            PaperTradingSession.owner_id == owner_id,
            PaperTradingSession.is_active == True,
        )
        .all()
    )

    best_strategies = (
        db.query(
            Strategy.name,
            func.avg(BacktestRun.winrate_pct).label("avg_winrate"),
            func.count(BacktestRun.id).label("backtest_count"),
        )
        .join(BacktestRun)
        .filter(Strategy.owner_id == owner_id)
        .group_by(Strategy.name)
        .order_by(func.avg(BacktestRun.winrate_pct).desc())
        .limit(5)
        .all()
    )

    return {
        "recent_backtests": [
            {
                "id": b.id,
                "strategy": b.strategy.name if b.strategy else "Unknown",
                "pair": b.pair,
                "return": b.total_return_pct,
                "winrate": b.winrate_pct,
                "trades": b.num_trades,
                "date": b.created_at.isoformat(),
            }
            for b in recent_backtests
        ],
        "active_sessions": [
            {
                "id": s.id,
                "name": s.name,
                "pair": s.pair,
                "capital": s.current_capital,
                "trades": s.total_trades,
                "return": s.total_return_pct,
            }
            for s in active_sessions
        ],
        "best_strategies": [
            {
                "name": name,
                "avg_winrate": avg_winrate or 0,
                "backtests": count,
            }
            for name, avg_winrate, count in best_strategies
        ],
    }
