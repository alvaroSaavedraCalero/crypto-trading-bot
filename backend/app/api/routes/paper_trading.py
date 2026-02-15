import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models import PaperTradingSession, PaperTrade, User
from ...schemas import (
    PaperTradingSession as PaperTradingSessionSchema,
    PaperTradingSessionCreate,
    PaperTrade as PaperTradeSchema,
)
from ...services import PaperTradingService
from ..auth import get_current_user

router = APIRouter()

MAX_LIMIT = 1000


@router.get("", response_model=List[PaperTradingSessionSchema])
async def list_paper_trading_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all paper trading sessions for the authenticated user."""
    limit = min(limit, MAX_LIMIT)
    sessions = (
        db.query(PaperTradingSession)
        .filter(PaperTradingSession.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return sessions


@router.post("")
async def create_paper_trading_session(
    session_create: PaperTradingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new paper trading session."""
    result = PaperTradingService.create_session(
        db=db,
        owner_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
):
    """Get paper trading session details."""
    session = (
        db.query(PaperTradingSession)
        .filter(
            PaperTradingSession.id == session_id,
            PaperTradingSession.owner_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post("/{session_id}/run")
async def run_paper_trading_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute paper trading session backtest using the pair/timeframe stored in the session."""
    # Verify ownership first
    session = (
        db.query(PaperTradingSession)
        .filter(
            PaperTradingSession.id == session_id,
            PaperTradingSession.owner_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await asyncio.to_thread(
        PaperTradingService.update_session_with_backtest,
        db=db,
        session_id=session_id,
        pair=session.pair,
        timeframe=session.timeframe,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{session_id}/trades", response_model=List[PaperTradeSchema])
async def get_session_trades(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """Get all trades for a paper trading session."""
    # Verify ownership
    session = (
        db.query(PaperTradingSession)
        .filter(
            PaperTradingSession.id == session_id,
            PaperTradingSession.owner_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    limit = min(limit, MAX_LIMIT)
    trades = (
        db.query(PaperTrade)
        .filter(PaperTrade.paper_trading_session_id == session_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return trades


@router.post("/{session_id}/close")
async def close_paper_trading_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close a paper trading session."""
    # Verify ownership
    session = (
        db.query(PaperTradingSession)
        .filter(
            PaperTradingSession.id == session_id,
            PaperTradingSession.owner_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = PaperTradingService.close_session(
        db=db,
        session_id=session_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
