"""
Servicio de Paper Trading
Integra la lógica de paper trading existente con la API
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

from ..models import (
    Strategy as StrategyModel,
    PaperTradingSession,
    PaperTrade,
)

logger = get_logger(__name__)


class PaperTradingService:
    """Servicio para gestionar paper trading"""

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
        """Crea una nueva sesión de paper trading"""
        try:
            # Obtener estrategia
            strategy = db.query(StrategyModel).filter(
                StrategyModel.id == strategy_id,
                StrategyModel.owner_id == owner_id,
            ).first()

            if not strategy:
                return {"error": "Estrategia no encontrada"}

            # Crear sesión
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
            logger.error(f"Error creando sesión: {str(e)}")
            db.rollback()
            return {"error": str(e)[:100]}

    @staticmethod
    def update_session_with_backtest(
        db: Session,
        session_id: int,
        pair: str,
        timeframe: str = "15m",
        period: str = "60d",
        limit: int = 2500,
    ) -> Dict[str, Any]:
        """
        Actualiza una sesión de paper trading ejecutando un backtest
        y guardando los trades generados
        """
        try:
            session = db.query(PaperTradingSession).filter(
                PaperTradingSession.id == session_id,
            ).first()

            if not session:
                return {"error": "Sesión no encontrada"}

            # Obtener estrategia
            strategy = db.query(StrategyModel).filter(
                StrategyModel.id == session.strategy_id,
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
            strategy_config = config_class(**strategy.config)

            # Configuración de backtest
            backtest_config = BacktestConfig(
                initial_capital=int(session.initial_capital),
                sl_pct=session.backtest_config.get("sl_pct", 2) / 100,
                tp_rr=session.backtest_config.get("tp_rr", 2),
                fee_pct=0.0005,
                allow_short=True,
            )

            risk_config = RiskManagementConfig(risk_pct=0.01)

            # Ejecutar backtest
            backtester = Backtester(backtest_config, risk_config)
            result = backtester.backtest(df, strategy_class, strategy_config)

            # Guardar trades
            total_pnl = 0.0
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
                db.add(paper_trade)
                total_pnl += trade.pnl

            # Actualizar sesión
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
            logger.error(f"Error actualizando sesión: {str(e)}", exc_info=True)
            db.rollback()
            return {"error": str(e)[:100]}

    @staticmethod
    def get_session_details(
        db: Session,
        session_id: int,
    ) -> Dict[str, Any]:
        """Obtiene detalles de una sesión con todos sus trades"""
        try:
            session = db.query(PaperTradingSession).filter(
                PaperTradingSession.id == session_id,
            ).first()

            if not session:
                return {"error": "Sesión no encontrada"}

            result = {
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

            return result

        except Exception as e:
            logger.error(f"Error obteniendo sesión: {str(e)}")
            return {"error": str(e)[:100]}

    @staticmethod
    def close_session(
        db: Session,
        session_id: int,
    ) -> Dict[str, Any]:
        """Cierra una sesión de paper trading"""
        try:
            session = db.query(PaperTradingSession).filter(
                PaperTradingSession.id == session_id,
            ).first()

            if not session:
                return {"error": "Sesión no encontrada"}

            session.is_active = False
            session.end_date = datetime.utcnow()
            db.commit()

            return {
                "status": "success",
                "message": "Sesión cerrada",
                "session_id": session_id,
                "final_capital": session.current_capital,
                "total_return_pct": session.total_return_pct,
            }

        except Exception as e:
            logger.error(f"Error cerrando sesión: {str(e)}")
            db.rollback()
            return {"error": str(e)[:100]}
