"""Paper Trading Service - integrates paper trading with API."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any

import pandas as pd
from sqlalchemy.orm import Session, joinedload

# Add project root to path for imports (only if not already present)
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from strategies.registry import STRATEGY_REGISTRY
from backtesting.engine import Backtester, BacktestConfig
from utils.risk import RiskManagementConfig
from data.yfinance_downloader import get_yfinance_data
from utils.logger import get_logger

from ..config import settings
from ..models import (
    Strategy as StrategyModel,
    PaperTradingSession,
    PaperTrade,
)

logger = get_logger(__name__)


class PaperTradingService:
    """Service for managing paper trading."""

    @staticmethod
    def create_session(
        db: Session,
        owner_id: int,
        strategy_id: int,
        pair: str,
        timeframe: str = "15m",
        name: Optional[str] = None,
        initial_capital: float = 10000.0,
    ) -> Dict[str, Any]:
        """Create a new paper trading session."""
        try:
            strategy = (
                db.query(StrategyModel)
                .filter(
                    StrategyModel.id == strategy_id,
                    StrategyModel.owner_id == owner_id,
                )
                .first()
            )

            if not strategy:
                return {"error": "Strategy not found"}

            session_name = name or f"{strategy.name} - {pair}"

            session = PaperTradingSession(
                owner_id=owner_id,
                strategy_id=strategy_id,
                name=session_name,
                pair=pair,
                timeframe=timeframe,
                initial_capital=initial_capital,
                current_capital=initial_capital,
                strategy_config=strategy.config,
                backtest_config={
                    "initial_capital": strategy.initial_capital,
                    "sl_pct": strategy.stop_loss_pct,
                    "tp_rr": strategy.take_profit_rr,
                },
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            return {
                "status": "success",
                "session_id": session.id,
                "name": session_name,
                "pair": pair,
                "timeframe": timeframe,
                "initial_capital": initial_capital,
            }

        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            db.rollback()
            if settings.DEBUG:
                return {"error": str(e)[:200]}
            return {"error": "Failed to create session"}

    @staticmethod
    def update_session_with_backtest(
        db: Session,
        session_id: int,
        pair: str,
        timeframe: str = "15m",
        period: str = "60d",
        limit: int = 2500,
    ) -> Dict[str, Any]:
        """Update a paper trading session by running a backtest and saving generated trades."""
        try:
            session = (
                db.query(PaperTradingSession)
                .filter(PaperTradingSession.id == session_id)
                .first()
            )

            if not session:
                return {"error": "Session not found"}

            strategy = (
                db.query(StrategyModel)
                .filter(StrategyModel.id == session.strategy_id)
                .first()
            )

            if not strategy:
                return {"error": "Strategy not found"}

            df = get_yfinance_data(
                symbol=pair,
                timeframe=timeframe,
                limit=limit,
                period=period,
            )

            if df is None or df.empty:
                return {"error": f"Could not fetch data for {pair}"}

            if strategy.strategy_type not in STRATEGY_REGISTRY:
                return {"error": f"Strategy type {strategy.strategy_type} not registered"}

            strategy_class, config_class = STRATEGY_REGISTRY[strategy.strategy_type]
            strategy_config = config_class(**strategy.config)

            backtest_config = BacktestConfig(
                initial_capital=int(session.initial_capital),
                sl_pct=session.backtest_config.get("sl_pct", 2) / 100,
                tp_rr=session.backtest_config.get("tp_rr", 2),
                fee_pct=0.0005,
                allow_short=True,
            )

            risk_config = RiskManagementConfig(risk_pct=0.01)

            backtester = Backtester(backtest_config, risk_config)
            result = backtester.backtest(df, strategy_class, strategy_config)

            # Bulk insert trades
            total_pnl = 0.0
            trade_objects = []
            for trade in result.trades:
                paper_trade = PaperTrade(
                    paper_trading_session_id=session_id,
                    entry_time=trade.entry_time,
                    exit_time=trade.exit_time,
                    side=trade.side,
                    entry_price=trade.entry_price,
                    exit_price=trade.exit_price,
                    position_size=trade.position_size,
                    stop_loss_price=trade.stop_loss_price,
                    take_profit_price=trade.take_profit_price,
                    pnl=trade.pnl,
                    pnl_pct=trade.pnl_pct,
                    is_winning=1 if trade.pnl > 0 else 0,
                    closed_at=trade.exit_time,
                )
                trade_objects.append(paper_trade)
                total_pnl += trade.pnl

            db.add_all(trade_objects)

            # Update session
            session.total_trades = result.num_trades
            session.winning_trades = result.winning_trades
            session.losing_trades = result.losing_trades
            session.total_return_pct = result.total_return_pct
            session.max_drawdown_pct = result.max_drawdown_pct
            session.current_capital = session.initial_capital + total_pnl
            session.last_update = datetime.utcnow()

            db.commit()

            return {
                "status": "success",
                "session_id": session_id,
                "total_trades": result.num_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "total_return_pct": result.total_return_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
                "current_capital": session.current_capital,
            }

        except Exception as e:
            logger.error(f"Error updating session: {str(e)}", exc_info=True)
            db.rollback()
            if settings.DEBUG:
                return {"error": str(e)[:200]}
            return {"error": "Failed to update session"}

    @staticmethod
    def get_session_details(
        db: Session,
        session_id: int,
    ) -> Dict[str, Any]:
        """Get session details with all trades (eager loaded)."""
        try:
            session = (
                db.query(PaperTradingSession)
                .options(joinedload(PaperTradingSession.trades))
                .filter(PaperTradingSession.id == session_id)
                .first()
            )

            if not session:
                return {"error": "Session not found"}

            return {
                "id": session.id,
                "strategy_id": session.strategy_id,
                "name": session.name,
                "pair": session.pair,
                "timeframe": session.timeframe,
                "initial_capital": session.initial_capital,
                "current_capital": session.current_capital,
                "total_trades": session.total_trades,
                "winning_trades": session.winning_trades,
                "losing_trades": session.losing_trades,
                "total_return_pct": session.total_return_pct,
                "max_drawdown_pct": session.max_drawdown_pct,
                "is_active": session.is_active,
                "start_date": session.start_date.isoformat(),
                "last_update": session.last_update.isoformat(),
                "trades": [
                    {
                        "entry_time": t.entry_time.isoformat(),
                        "exit_time": t.exit_time.isoformat() if t.exit_time else None,
                        "side": t.side,
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "position_size": t.position_size,
                        "pnl": t.pnl,
                        "pnl_pct": t.pnl_pct,
                        "is_winning": t.is_winning,
                    }
                    for t in session.trades
                ],
            }

        except Exception as e:
            logger.error(f"Error fetching session: {str(e)}")
            if settings.DEBUG:
                return {"error": str(e)[:200]}
            return {"error": "Failed to fetch session details"}

    @staticmethod
    def close_session(
        db: Session,
        session_id: int,
    ) -> Dict[str, Any]:
        """Close a paper trading session."""
        try:
            session = (
                db.query(PaperTradingSession)
                .filter(PaperTradingSession.id == session_id)
                .first()
            )

            if not session:
                return {"error": "Session not found"}

            session.is_active = False
            session.end_date = datetime.utcnow()
            db.commit()

            return {
                "status": "success",
                "message": "Session closed",
                "session_id": session_id,
                "final_capital": session.current_capital,
                "total_return_pct": session.total_return_pct,
            }

        except Exception as e:
            logger.error(f"Error closing session: {str(e)}")
            db.rollback()
            if settings.DEBUG:
                return {"error": str(e)[:200]}
            return {"error": "Failed to close session"}
