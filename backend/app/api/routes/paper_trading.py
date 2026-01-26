from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models import PaperTradingSession, PaperTrade
from ...schemas import (
    PaperTradingSession as PaperTradingSessionSchema,
    PaperTradingSessionCreate,
    PaperTrade as PaperTradeSchema,
)
from ...services import PaperTradingService

router = APIRouter()


@router.get("/", response_model=List[PaperTradingSessionSchema])
async def list_paper_trading_sessions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    owner_id: int = 1,
):
    """List all paper trading sessions."""
    sessions = db.query(PaperTradingSession).filter(
        PaperTradingSession.owner_id == owner_id,
    ).offset(skip).limit(limit).all()
    return sessions


@router.post("/")
async def create_paper_trading_session(
    session_create: PaperTradingSessionCreate,
    db: Session = Depends(get_db),
    owner_id: int = 1,
):
    """Create a new paper trading session."""
    result = PaperTradingService.create_session(
        db=db,
        owner_id=owner_id,
        strategy_id=session_create.strategy_id,
        pair=session_create.pair,
        timeframe=session_create.timeframe,
        name=session_create.name,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{session_id}", response_model=PaperTradingSessionSchema)
async def get_paper_trading_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Get paper trading session details."""
    session = db.query(PaperTradingSession).filter(
        PaperTradingSession.id == session_id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    return session


@router.post("/{session_id}/run")
async def run_paper_trading_session(
    session_id: int,
    pair: str,
    timeframe: str = "15m",
    db: Session = Depends(get_db),
):
    """Execute paper trading session backtest."""
    result = PaperTradingService.update_session_with_backtest(
        db=db,
        session_id=session_id,
        pair=pair,
        timeframe=timeframe,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{session_id}/trades", response_model=List[PaperTradeSchema])
async def get_session_trades(
    session_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Get all trades for a paper trading session."""
    trades = db.query(PaperTrade).filter(
        PaperTrade.paper_trading_session_id == session_id,
    ).offset(skip).limit(limit).all()

    return trades


@router.post("/{session_id}/close")
async def close_paper_trading_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Close a paper trading session."""
    result = PaperTradingService.close_session(
        db=db,
        session_id=session_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
