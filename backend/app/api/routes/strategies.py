from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...schemas import Strategy, StrategyCreate, StrategyUpdate, StrategyWithBacktests
from ...models import Strategy as StrategyModel
from ...crud import StrategyCRUD

router = APIRouter()


@router.get("/", response_model=List[Strategy])
async def list_strategies(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    owner_id: int = 1,
):
    """List all strategies."""
    strategies = StrategyCRUD.get_all(db, owner_id, skip, limit)
    return strategies


@router.get("/{strategy_id}", response_model=StrategyWithBacktests)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get strategy by ID with all its backtests."""
    strategy = StrategyCRUD.get(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.post("/", response_model=Strategy)
async def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    owner_id: int = 1,
):
    """Create a new strategy."""
    db_strategy = StrategyCRUD.create(db, strategy, owner_id)
    return db_strategy


@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db),
):
    """Update a strategy."""
    db_strategy = StrategyCRUD.update(db, strategy_id, strategy_update)
    if not db_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return db_strategy


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a strategy."""
    success = StrategyCRUD.delete(db, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"detail": "Strategy deleted"}
