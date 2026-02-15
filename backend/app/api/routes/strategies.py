import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...schemas import Strategy, StrategyCreate, StrategyUpdate, StrategyWithBacktests
from ...models import Strategy as StrategyModel
from ...crud import StrategyCRUD
from ..auth import get_current_user
from ...models import User

# Import strategy registry for type validation
project_root = str(Path(__file__).parent.parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from strategies.registry import STRATEGY_REGISTRY

router = APIRouter()

MAX_LIMIT = 1000


@router.get("/types")
async def list_strategy_types():
    """Return list of available strategy types from the registry."""
    return {"types": list(STRATEGY_REGISTRY.keys())}


@router.get("", response_model=List[Strategy])
async def list_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all strategies for the authenticated user."""
    limit = min(limit, MAX_LIMIT)
    strategies = StrategyCRUD.get_all(db, current_user.id, skip, limit)
    return strategies


@router.get("/{strategy_id}", response_model=StrategyWithBacktests)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get strategy by ID with all its backtests."""
    strategy = StrategyCRUD.get(db, strategy_id)
    if not strategy or strategy.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.post("", response_model=Strategy)
async def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new strategy."""
    if strategy.strategy_type not in STRATEGY_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy_type '{strategy.strategy_type}'. "
            f"Must be one of: {', '.join(sorted(STRATEGY_REGISTRY.keys()))}",
        )
    db_strategy = StrategyCRUD.create(db, strategy, current_user.id)
    return db_strategy


@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a strategy."""
    existing = StrategyCRUD.get(db, strategy_id)
    if not existing or existing.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db_strategy = StrategyCRUD.update(db, strategy_id, strategy_update)
    return db_strategy


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a strategy."""
    existing = StrategyCRUD.get(db, strategy_id)
    if not existing or existing.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Strategy not found")
    StrategyCRUD.delete(db, strategy_id)
    return {"detail": "Strategy deleted"}


@router.post("/{strategy_id}/clone", response_model=Strategy)
async def clone_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clone an existing strategy."""
    original = StrategyCRUD.get(db, strategy_id)
    if not original or original.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Strategy not found")

    clone = StrategyModel(
        owner_id=current_user.id,
        name=f"{original.name} (copy)",
        description=original.description,
        strategy_type=original.strategy_type,
        config=original.config,
        initial_capital=original.initial_capital,
        stop_loss_pct=original.stop_loss_pct,
        take_profit_rr=original.take_profit_rr,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone
