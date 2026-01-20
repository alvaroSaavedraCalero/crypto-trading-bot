# src/core/backtesting/metrics.py
"""
Metrics calculation utilities for backtesting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from ..types import Trade, BacktestMetrics


class MetricsCalculator:
    """
    Utility class for calculating trading metrics.
    """

    @staticmethod
    def from_trades_and_equity(
        trades: List[Trade],
        equity_curve: pd.Series,
        initial_capital: float
    ) -> BacktestMetrics:
        """
        Calculate comprehensive metrics from trades and equity curve.
        """
        if not trades:
            return BacktestMetrics()

        pnl_values = np.array([t.pnl for t in trades if t.pnl is not None])

        if len(pnl_values) == 0:
            return BacktestMetrics(num_trades=len(trades))

        # Win/Loss analysis
        winners = pnl_values[pnl_values > 0]
        losers = pnl_values[pnl_values < 0]

        num_trades = len(trades)
        winning_trades = len(winners)
        losing_trades = len(losers)
        win_rate = (winning_trades / num_trades) * 100 if num_trades > 0 else 0.0

        # Profit analysis
        gross_profit = float(winners.sum()) if len(winners) > 0 else 0.0
        gross_loss = float(abs(losers.sum())) if len(losers) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Returns
        final = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_capital
        total_return_pct = ((final - initial_capital) / initial_capital) * 100
        total_pnl = final - initial_capital

        # Drawdown
        max_drawdown_pct, max_dd_duration = MetricsCalculator._calculate_drawdown(equity_curve)

        # Trade statistics
        avg_trade_pnl = float(pnl_values.mean())
        avg_winning_trade = float(winners.mean()) if len(winners) > 0 else 0.0
        avg_losing_trade = float(losers.mean()) if len(losers) > 0 else 0.0

        # Risk-adjusted metrics
        returns = equity_curve.pct_change().dropna()
        sharpe = MetricsCalculator._sharpe_ratio(returns)
        sortino = MetricsCalculator._sortino_ratio(returns)

        return BacktestMetrics(
            total_return_pct=total_return_pct,
            total_pnl=total_pnl,
            num_trades=num_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_duration=max_dd_duration,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            avg_trade_pnl=avg_trade_pnl,
            avg_winning_trade=avg_winning_trade,
            avg_losing_trade=avg_losing_trade,
        )

    @staticmethod
    def _calculate_drawdown(equity: pd.Series) -> tuple[float, int]:
        """Calculate maximum drawdown percentage and duration."""
        if len(equity) == 0:
            return 0.0, 0

        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max
        max_dd_pct = float(drawdown.min()) * 100

        # Duration calculation
        is_dd = drawdown < 0
        dd_groups = (~is_dd).cumsum()
        dd_lengths = is_dd.groupby(dd_groups).sum()
        max_dd_duration = int(dd_lengths.max()) if len(dd_lengths) > 0 else 0

        return max_dd_pct, max_dd_duration

    @staticmethod
    def _sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
        """Annualized Sharpe ratio."""
        if len(returns) < 2:
            return 0.0

        excess = returns - risk_free / 252
        std = excess.std()

        if std == 0 or np.isnan(std):
            return 0.0

        return float((excess.mean() / std) * np.sqrt(252))

    @staticmethod
    def _sortino_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
        """Annualized Sortino ratio."""
        if len(returns) < 2:
            return 0.0

        excess = returns - risk_free / 252
        downside = excess[excess < 0]

        if len(downside) == 0:
            return float('inf')

        dd_std = downside.std()
        if dd_std == 0 or np.isnan(dd_std):
            return 0.0

        return float((excess.mean() / dd_std) * np.sqrt(252))

    @staticmethod
    def rolling_sharpe(
        equity: pd.Series,
        window: int = 252
    ) -> pd.Series:
        """Calculate rolling Sharpe ratio."""
        returns = equity.pct_change()
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        return (rolling_mean / rolling_std) * np.sqrt(252)

    @staticmethod
    def monte_carlo_analysis(
        trades: List[Trade],
        initial_capital: float,
        num_simulations: int = 1000,
        confidence_level: float = 0.95
    ) -> dict:
        """
        Run Monte Carlo simulation on trade sequence.

        Returns statistics on potential outcomes with shuffled trade order.
        """
        if not trades:
            return {}

        pnl_values = [t.pnl for t in trades if t.pnl is not None]
        if not pnl_values:
            return {}

        final_equities = []
        max_drawdowns = []

        for _ in range(num_simulations):
            # Shuffle trade PnLs
            shuffled = np.random.permutation(pnl_values)

            # Build equity curve
            equity = [initial_capital]
            for pnl in shuffled:
                equity.append(equity[-1] + pnl)

            equity_series = pd.Series(equity)
            final_equities.append(equity[-1])

            # Calculate drawdown
            running_max = equity_series.cummax()
            dd = (equity_series - running_max) / running_max
            max_drawdowns.append(dd.min() * 100)

        # Statistics
        final_arr = np.array(final_equities)
        dd_arr = np.array(max_drawdowns)

        percentile_low = (1 - confidence_level) / 2 * 100
        percentile_high = (1 + confidence_level) / 2 * 100

        return {
            "mean_final_equity": float(final_arr.mean()),
            "median_final_equity": float(np.median(final_arr)),
            "std_final_equity": float(final_arr.std()),
            f"final_equity_{int(percentile_low)}pct": float(np.percentile(final_arr, percentile_low)),
            f"final_equity_{int(percentile_high)}pct": float(np.percentile(final_arr, percentile_high)),
            "worst_final_equity": float(final_arr.min()),
            "best_final_equity": float(final_arr.max()),
            "mean_max_drawdown": float(dd_arr.mean()),
            "worst_max_drawdown": float(dd_arr.min()),
            "probability_of_profit": float((final_arr > initial_capital).mean() * 100),
        }
