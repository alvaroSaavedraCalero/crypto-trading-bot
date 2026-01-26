"""CRUD operations for Strategy"""

from sqlalchemy.orm import Session
from ..models import Strategy as StrategyModel
from ..schemas import StrategyCreate, StrategyUpdate


class StrategyCRUD:
    @staticmethod
    def create(db: Session, strategy: StrategyCreate, owner_id: int) -> StrategyModel:
        """Create a new strategy."""
        db_strategy = StrategyModel(
            owner_id=owner_id,
            name=strategy.name,
            description=strategy.description,
            strategy_type=strategy.strategy_type,
            config=strategy.config,
            initial_capital=strategy.initial_capital,
            stop_loss_pct=strategy.stop_loss_pct,
            take_profit_rr=strategy.take_profit_rr,
        )
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        return db_strategy

    @staticmethod
    def get(db: Session, strategy_id: int) -> StrategyModel:
        """Get a strategy by ID."""
        return db.query(StrategyModel).filter(StrategyModel.id == strategy_id).first()

    @staticmethod
    def get_all(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
        """Get all strategies for a user."""
        return db.query(StrategyModel).filter(
            StrategyModel.owner_id == owner_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session,
        strategy_id: int,
        strategy_update: StrategyUpdate,
    ) -> StrategyModel:
        """Update a strategy."""
        db_strategy = db.query(StrategyModel).filter(
            StrategyModel.id == strategy_id
        ).first()
        
        if db_strategy:
            update_data = strategy_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_strategy, field, value)
            db.add(db_strategy)
            db.commit()
            db.refresh(db_strategy)
        
        return db_strategy

    @staticmethod
    def delete(db: Session, strategy_id: int) -> bool:
        """Delete a strategy."""
        db_strategy = db.query(StrategyModel).filter(
            StrategyModel.id == strategy_id
        ).first()
        
        if db_strategy:
            db.delete(db_strategy)
            db.commit()
            return True
        
        return False
