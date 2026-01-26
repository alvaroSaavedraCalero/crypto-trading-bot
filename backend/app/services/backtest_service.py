"""
Servicio de Backtesting
Integra la lógica de backtesting existente con la API
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

import pandas as pd
from sqlalchemy.orm import Session

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from strategies.registry import STRATEGY_REGISTRY
from backtesting.engine import Backtester, BacktestConfig
from utils.risk import RiskManagementConfig, calculate_position_size_spot
from data.yfinance_downloader import get_yfinance_data
from utils.logger import get_logger

from ..models import Strategy as StrategyModel, BacktestRun, BacktestTrade
from ..schemas import BacktestRun as BacktestRunSchema

logger = get_logger(__name__)


class BacktestService:
    """Servicio para ejecutar backtests y guardar resultados"""

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
        """
        Ejecuta un backtest de una estrategia en un par y guarda los resultados.
        
        Args:
            db: Sesión de base de datos
            strategy_id: ID de la estrategia
            pair: Par de trading (ej: EURUSD)
            timeframe: Timeframe (ej: 15m)
            period: Período de datos (ej: 60d)
            limit: Número de candles
            owner_id: ID del usuario propietario
            
        Returns:
            Dict con los resultados del backtest
        """
        try:
            # Obtener estrategia de la BD
            strategy = db.query(StrategyModel).filter(
                StrategyModel.id == strategy_id,
                StrategyModel.owner_id == owner_id,
            ).first()

            if not strategy:
                return {"error": "Estrategia no encontrada"}

            # Obtener datos
            df = get_yfinance_data(
                symbol=pair,
                timeframe=timeframe,
                limit=limit,
                period=period,
            )

            if df is None or df.empty:
                return {"error": f"No se pudieron obtener datos para {pair}"}

            # Obtener clase de estrategia
            if strategy.strategy_type not in STRATEGY_REGISTRY:
                return {"error": f"Estrategia {strategy.strategy_type} no registrada"}

            strategy_class, config_class = STRATEGY_REGISTRY[strategy.strategy_type]

            # Crear instancia de configuración
            strategy_config = config_class(**strategy.config)

            # Configuración de backtest
            backtest_config = BacktestConfig(
                initial_capital=strategy.initial_capital,
                sl_pct=strategy.stop_loss_pct / 100,
                tp_rr=strategy.take_profit_rr,
                fee_pct=0.0005,
                allow_short=True,
            )

            risk_config = RiskManagementConfig(risk_pct=0.01)

            # Ejecutar backtest
            backtester = Backtester(backtest_config, risk_config)
            result = backtester.backtest(df, strategy_class, strategy_config)

            # Guardar en BD
            backtest_run = BacktestRun(
                owner_id=owner_id,
                strategy_id=strategy_id,
                pair=pair,
                timeframe=timeframe,
                start_date=df.index[0].to_pydatetime() if hasattr(df.index[0], 'to_pydatetime') else df.index[0],
                end_date=df.index[-1].to_pydatetime() if hasattr(df.index[-1], 'to_pydatetime') else df.index[-1],
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
            db.flush()  # Para obtener el ID

            # Guardar trades
            for trade in result.trades:
                backtest_trade = BacktestTrade(
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
                    metadata=trade.metadata if hasattr(trade, 'metadata') else None,
                )
                db.add(backtest_trade)

            # Actualizar last_backtest_at
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
            logger.error(f"Error en backtest: {str(e)}", exc_info=True)
            db.rollback()
            return {"error": f"Error en backtest: {str(e)[:100]}"}

    @staticmethod
    def get_backtest_results(db: Session, backtest_id: int) -> Dict[str, Any]:
        """Obtiene los resultados de un backtest con sus trades"""
        try:
            backtest_run = db.query(BacktestRun).filter(
                BacktestRun.id == backtest_id
            ).first()

            if not backtest_run:
                return {"error": "Backtest no encontrado"}

            # Convertir a diccionario
            result = {
                "id": backtest_run.id,
                "strategy_id": backtest_run.strategy_id,
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

            return result

        except Exception as e:
            logger.error(f"Error obteniendo resultados: {str(e)}")
            return {"error": str(e)[:100]}
