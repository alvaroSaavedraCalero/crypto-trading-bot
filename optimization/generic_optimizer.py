# optimization/generic_optimizer.py
"""
Optimizador genérico para estrategias de trading.

Este módulo consolida la lógica común de todos los optimizadores específicos,
reduciendo la duplicación de código y facilitando la adición de nuevas estrategias.

Uso:
    from optimization.generic_optimizer import GenericOptimizer

    optimizer = GenericOptimizer(
        strategy_type="SUPERTREND",
        param_ranges={
            "atr_period": [10, 14, 20],
            "atr_multiplier": [2.0, 3.0, 4.0],
            "use_adx_filter": [True, False],
        }
    )

    results = optimizer.optimize(df, metric="profit_factor", min_trades=30)
"""

from __future__ import annotations

from dataclasses import replace, fields, is_dataclass
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
import random

import pandas as pd

from strategies.registry import STRATEGY_REGISTRY, create_strategy
from backtesting.engine import Backtester, BacktestConfig, BacktestResult
from utils.risk import RiskManagementConfig
from utils.logger import get_logger, TradeLogger
from config.settings import BACKTEST_CONFIG, RISK_CONFIG

logger = get_logger(__name__)
trade_logger = TradeLogger()


# Global DataFrame for worker processes
_GLOBAL_DF: Optional[pd.DataFrame] = None
_GLOBAL_OPTIMIZER: Optional["GenericOptimizer"] = None


def _init_worker(df: pd.DataFrame, optimizer_data: dict) -> None:
    """Initialize worker process with DataFrame and optimizer config."""
    global _GLOBAL_DF, _GLOBAL_OPTIMIZER
    _GLOBAL_DF = df
    # Recreate optimizer in worker (can't pickle class instances easily)
    _GLOBAL_OPTIMIZER = GenericOptimizer(
        strategy_type=optimizer_data["strategy_type"],
        param_ranges=optimizer_data["param_ranges"],
        backtest_config=optimizer_data["backtest_config"],
        risk_config=optimizer_data["risk_config"],
        min_trades=optimizer_data["min_trades"],
    )


def _evaluate_single_config(args: Tuple[dict, dict]) -> Optional[Dict[str, Any]]:
    """Evaluate a single configuration in worker process."""
    global _GLOBAL_DF, _GLOBAL_OPTIMIZER

    if _GLOBAL_DF is None or _GLOBAL_OPTIMIZER is None:
        raise RuntimeError("Worker not initialized properly")

    strategy_params, backtest_params = args

    try:
        return _GLOBAL_OPTIMIZER._evaluate_config(
            _GLOBAL_DF, strategy_params, backtest_params
        )
    except Exception as e:
        logger.debug(f"Config evaluation failed: {e}")
        return None


class GenericOptimizer:
    """
    Optimizador genérico para cualquier estrategia registrada.

    Attributes:
        strategy_type: Tipo de estrategia del registro (ej: "SUPERTREND", "BOLLINGER_MR")
        param_ranges: Diccionario con los rangos de parámetros a optimizar
        backtest_config: Configuración base del backtest
        risk_config: Configuración de gestión de riesgo
        min_trades: Número mínimo de trades para considerar válido un resultado
    """

    def __init__(
        self,
        strategy_type: str,
        param_ranges: Dict[str, List[Any]],
        backtest_config: Optional[BacktestConfig] = None,
        risk_config: Optional[RiskManagementConfig] = None,
        min_trades: int = 10,
    ):
        if strategy_type not in STRATEGY_REGISTRY:
            raise ValueError(
                f"Estrategia no registrada: {strategy_type}. "
                f"Disponibles: {list(STRATEGY_REGISTRY.keys())}"
            )

        self.strategy_type = strategy_type
        self.param_ranges = param_ranges
        self.backtest_config = backtest_config or BACKTEST_CONFIG
        self.risk_config = risk_config or RISK_CONFIG
        self.min_trades = min_trades

        # Get config class for this strategy
        _, self.config_cls = STRATEGY_REGISTRY[strategy_type]

        logger.info(
            f"GenericOptimizer inicializado para {strategy_type} "
            f"con {len(param_ranges)} parámetros"
        )

    def _get_config_defaults(self) -> Dict[str, Any]:
        """Get default values for all config fields."""
        defaults = {}
        if is_dataclass(self.config_cls):
            for field in fields(self.config_cls):
                if field.default is not field.default_factory:
                    defaults[field.name] = field.default
                elif field.default_factory is not field.default_factory:
                    defaults[field.name] = field.default_factory()
        return defaults

    def build_param_grid(
        self,
        backtest_param_ranges: Optional[Dict[str, List[Any]]] = None,
        filter_func: Optional[Callable[[dict, dict], bool]] = None,
    ) -> List[Tuple[dict, dict]]:
        """
        Construye el grid de parámetros para optimización.

        Args:
            backtest_param_ranges: Rangos adicionales para parámetros de backtest
                                   (ej: {"sl_pct": [0.01, 0.02], "tp_rr": [2.0, 3.0]})
            filter_func: Función opcional para filtrar combinaciones inválidas
                         Recibe (strategy_params, backtest_params) y retorna bool

        Returns:
            Lista de tuplas (strategy_params_dict, backtest_params_dict)
        """
        backtest_param_ranges = backtest_param_ranges or {}

        # Get default config values
        defaults = self._get_config_defaults()

        # Build strategy parameter combinations
        strategy_keys = list(self.param_ranges.keys())
        strategy_values = [self.param_ranges[k] for k in strategy_keys]

        # Build backtest parameter combinations
        backtest_keys = list(backtest_param_ranges.keys())
        backtest_values = [backtest_param_ranges[k] for k in backtest_keys]

        combos: List[Tuple[dict, dict]] = []

        # Generate all combinations
        for strat_vals in product(*strategy_values) if strategy_values else [()]:
            strategy_params = dict(zip(strategy_keys, strat_vals))

            # Fill in defaults for non-optimized parameters
            full_strategy_params = {**defaults, **strategy_params}

            for bt_vals in product(*backtest_values) if backtest_values else [()]:
                backtest_params = dict(zip(backtest_keys, bt_vals))

                # Apply filter if provided
                if filter_func is not None:
                    if not filter_func(full_strategy_params, backtest_params):
                        continue

                combos.append((full_strategy_params, backtest_params))

        logger.info(f"Grid de parámetros generado: {len(combos)} combinaciones")
        return combos

    def _evaluate_config(
        self,
        df: pd.DataFrame,
        strategy_params: dict,
        backtest_params: dict,
    ) -> Optional[Dict[str, Any]]:
        """
        Evalúa una configuración específica.

        Returns:
            Diccionario con parámetros y métricas, o None si no es válido.
        """
        try:
            # Create strategy config
            config = self.config_cls(**strategy_params)

            # Create strategy
            strategy = create_strategy(self.strategy_type, config)

            # Generate signals
            df_signals = strategy.generate_signals(df)

            # Update backtest config with optimized params
            bt_cfg = replace(self.backtest_config, **backtest_params)

            # Run backtest
            backtester = Backtester(
                backtest_config=bt_cfg,
                risk_config=self.risk_config,
            )
            result = backtester.run(df_signals)

            # Check minimum trades
            if result.num_trades < self.min_trades:
                return None

            # Build result dictionary
            result_dict = {
                **strategy_params,
                **backtest_params,
                "num_trades": result.num_trades,
                "total_return_pct": result.total_return_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
                "winrate_pct": result.winrate_pct,
                "profit_factor": result.profit_factor,
            }

            return result_dict

        except Exception as e:
            logger.debug(f"Error evaluating config: {e}")
            return None

    def optimize(
        self,
        df: pd.DataFrame,
        backtest_param_ranges: Optional[Dict[str, List[Any]]] = None,
        filter_func: Optional[Callable[[dict, dict], bool]] = None,
        max_combos: int = 2000,
        n_jobs: Optional[int] = None,
        seed: int = 42,
        metric: str = "profit_factor",
    ) -> pd.DataFrame:
        """
        Ejecuta la optimización completa.

        Args:
            df: DataFrame con datos OHLCV
            backtest_param_ranges: Rangos para parámetros de backtest
            filter_func: Función para filtrar combinaciones
            max_combos: Máximo de combinaciones a evaluar
            n_jobs: Número de procesos paralelos (None = cpu_count - 1)
            seed: Semilla para muestreo aleatorio
            metric: Métrica principal para ordenar resultados

        Returns:
            DataFrame con resultados ordenados por la métrica especificada
        """
        logger.info(f"Iniciando optimización de {self.strategy_type}")

        # Build parameter grid
        param_grid = self.build_param_grid(backtest_param_ranges, filter_func)
        total_full = len(param_grid)

        logger.info(f"Combinaciones totales: {total_full}")

        # Sample if too many
        if total_full > max_combos:
            logger.info(f"Reduciendo a {max_combos} muestras aleatorias")
            random.seed(seed)
            param_grid = random.sample(param_grid, max_combos)

        total_combos = len(param_grid)

        # Set up parallelization
        if n_jobs is None:
            n_jobs = max(1, cpu_count() - 1)

        logger.info(f"Usando {n_jobs} procesos paralelos")

        # Prepare optimizer data for workers
        optimizer_data = {
            "strategy_type": self.strategy_type,
            "param_ranges": self.param_ranges,
            "backtest_config": self.backtest_config,
            "risk_config": self.risk_config,
            "min_trades": self.min_trades,
        }

        # Run parallel optimization
        results: List[Dict[str, Any]] = []
        progress_step = max(1, total_combos // 20)

        with Pool(
            processes=n_jobs,
            initializer=_init_worker,
            initargs=(df, optimizer_data),
        ) as pool:
            for idx, res in enumerate(
                pool.imap_unordered(_evaluate_single_config, param_grid, chunksize=10),
                start=1,
            ):
                if res is not None:
                    results.append(res)

                if idx % progress_step == 0 or idx == total_combos:
                    pct = idx / total_combos * 100.0
                    trade_logger.optimization_progress(
                        self.strategy_type, idx, total_combos, len(results)
                    )

        if not results:
            logger.warning(f"Optimización de {self.strategy_type}: sin resultados válidos")
            return pd.DataFrame()

        # Create and sort results DataFrame
        df_results = pd.DataFrame(results)

        # Determine sort order based on metric
        if metric in ["max_drawdown_pct"]:
            ascending = True  # Lower is better for drawdown
        else:
            ascending = False  # Higher is better for returns, profit factor, etc.

        df_results = df_results.sort_values(
            by=[metric, "total_return_pct"],
            ascending=[ascending, False],
        ).reset_index(drop=True)

        logger.info(
            f"Optimización completada: {len(results)} resultados válidos. "
            f"Mejor {metric}: {df_results[metric].iloc[0]:.4f}"
        )

        return df_results

    def save_results(
        self,
        df_results: pd.DataFrame,
        symbol: str,
        timeframe: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Guarda los resultados de optimización a CSV.

        Returns:
            Path del archivo guardado
        """
        if df_results.empty:
            logger.warning("No hay resultados para guardar")
            return Path("")

        output_dir = output_dir or Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_symbol = symbol.replace("/", "")
        filename = f"opt_{self.strategy_type.lower()}_{safe_symbol}_{timeframe}.csv"
        output_path = output_dir / filename

        df_results.to_csv(output_path, index=False)
        logger.info(f"Resultados guardados en {output_path}")

        return output_path

    def print_top_results(
        self,
        df_results: pd.DataFrame,
        top_n: int = 20,
        symbol: str = "",
        timeframe: str = "",
    ) -> None:
        """Imprime los mejores resultados."""
        if df_results.empty:
            print(f"{self.strategy_type}: Sin resultados")
            return

        print(f"\nTop {top_n} {self.strategy_type} {symbol} {timeframe}:")
        print(df_results.head(top_n).to_string())


def create_optimizer(
    strategy_type: str,
    **param_ranges: List[Any],
) -> GenericOptimizer:
    """
    Factory function para crear optimizadores fácilmente.

    Example:
        optimizer = create_optimizer(
            "SUPERTREND",
            atr_period=[10, 14, 20],
            atr_multiplier=[2.0, 3.0, 4.0],
        )
    """
    return GenericOptimizer(
        strategy_type=strategy_type,
        param_ranges=param_ranges,
    )


# Ejemplo de uso en script
if __name__ == "__main__":
    from data.downloader import get_datos_cripto_cached

    # Crear optimizador para Supertrend
    optimizer = create_optimizer(
        "SUPERTREND",
        atr_period=[10, 14, 20],
        atr_multiplier=[2.0, 3.0, 4.0],
        use_adx_filter=[True, False],
        adx_period=[14],
        adx_threshold=[20.0, 25.0],
    )

    # Descargar datos
    symbol = "BTC/USDT"
    timeframe = "1h"
    df = get_datos_cripto_cached(symbol=symbol, timeframe=timeframe, limit=5000)

    # Ejecutar optimización
    results = optimizer.optimize(
        df,
        backtest_param_ranges={
            "sl_pct": [0.01, 0.02],
            "tp_rr": [2.0, 3.0],
        },
        max_combos=500,
        metric="profit_factor",
    )

    # Mostrar y guardar resultados
    optimizer.print_top_results(results, symbol=symbol, timeframe=timeframe)
    optimizer.save_results(results, symbol, timeframe)
