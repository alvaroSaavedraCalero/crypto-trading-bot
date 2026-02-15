"""Backtest Service - integrates backtesting engine with API."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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
from ..models import Strategy as StrategyModel, BacktestRun, BacktestTrade

logger = get_logger(__name__)


class BacktestService:
    """Service for running backtests and saving results."""

    @staticmethod
    def run_backtest(
        db: Session,
        strategy_id: int,
        pair: str,
        timeframe: str = "15m",
        period: str = "60d",
        limit: int = 2000,
        owner_id: int = 1,
    ) -> Dict[str, Any]:
        """Run a backtest for a strategy and save results."""
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
                initial_capital=strategy.initial_capital,
                sl_pct=strategy.stop_loss_pct / 100,
                tp_rr=strategy.take_profit_rr,
                fee_pct=0.0005,
                allow_short=True,
            )

            risk_config = RiskManagementConfig(risk_pct=0.01)

            backtester = Backtester(backtest_config, risk_config)
            result = backtester.backtest(df, strategy_class, strategy_config)

            backtest_run = BacktestRun(
                owner_id=owner_id,
                strategy_id=strategy_id,
                pair=pair,
                timeframe=timeframe,
                start_date=(
                    pd.Timestamp(df["timestamp"].iloc[0]).to_pydatetime()
                    if "timestamp" in df.columns
                    else df.index[0]
                ),
                end_date=(
                    pd.Timestamp(df["timestamp"].iloc[-1]).to_pydatetime()
                    if "timestamp" in df.columns
                    else df.index[-1]
                ),
                total_return_pct=result.total_return_pct,
                winrate_pct=result.winrate_pct,
                profit_factor=result.profit_factor,
                max_drawdown_pct=result.max_drawdown_pct,
                num_trades=result.num_trades,
                winning_trades=result.winning_trades,
                losing_trades=result.losing_trades,
                backtest_config=backtest_config.__dict__,
                strategy_config=strategy.config,
            )

            db.add(backtest_run)
            db.flush()

            # Bulk insert trades
            trade_objects = [
                BacktestTrade(
                    backtest_run_id=backtest_run.id,
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
                    extra_data=trade.metadata if hasattr(trade, "metadata") else None,
                )
                for trade in result.trades
            ]
            db.add_all(trade_objects)

            strategy.last_backtest_at = datetime.utcnow()
            db.commit()

            return {
                "status": "success",
                "backtest_id": backtest_run.id,
                "pair": pair,
                "timeframe": timeframe,
                "total_return_pct": result.total_return_pct,
                "winrate_pct": result.winrate_pct,
                "profit_factor": result.profit_factor,
                "max_drawdown_pct": result.max_drawdown_pct,
                "num_trades": result.num_trades,
                "start_date": backtest_run.start_date.isoformat(),
                "end_date": backtest_run.end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Backtest error: {str(e)}", exc_info=True)
            db.rollback()
            if settings.DEBUG:
                return {"error": f"Backtest error: {str(e)[:200]}"}
            return {"error": "Backtest execution failed"}

    @staticmethod
    def get_backtest_results(db: Session, backtest_id: int) -> Dict[str, Any]:
        """Get backtest results with trades (eager loaded)."""
        try:
            backtest_run = (
                db.query(BacktestRun)
                .options(joinedload(BacktestRun.trades), joinedload(BacktestRun.strategy))
                .filter(BacktestRun.id == backtest_id)
                .first()
            )

            if not backtest_run:
                return {"error": "Backtest not found"}

            return {
                "id": backtest_run.id,
                "owner_id": backtest_run.owner_id,
                "strategy_id": backtest_run.strategy_id,
                "strategy_type": backtest_run.strategy.strategy_type.value if backtest_run.strategy else None,
                "pair": backtest_run.pair,
                "timeframe": backtest_run.timeframe,
                "total_return_pct": backtest_run.total_return_pct,
                "winrate_pct": backtest_run.winrate_pct,
                "profit_factor": backtest_run.profit_factor,
                "max_drawdown_pct": backtest_run.max_drawdown_pct,
                "num_trades": backtest_run.num_trades,
                "winning_trades": backtest_run.winning_trades,
                "losing_trades": backtest_run.losing_trades,
                "start_date": backtest_run.start_date.isoformat(),
                "end_date": backtest_run.end_date.isoformat(),
                "created_at": backtest_run.created_at.isoformat(),
                "trades": [
                    {
                        "entry_time": t.entry_time.isoformat(),
                        "exit_time": t.exit_time.isoformat(),
                        "side": t.side,
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "position_size": t.position_size,
                        "pnl": t.pnl,
                        "pnl_pct": t.pnl_pct,
                        "is_winning": t.is_winning,
                    }
                    for t in backtest_run.trades
                ],
            }

        except Exception as e:
            logger.error(f"Error fetching backtest results: {str(e)}")
            if settings.DEBUG:
                return {"error": str(e)[:200]}
            return {"error": "Failed to fetch backtest results"}
