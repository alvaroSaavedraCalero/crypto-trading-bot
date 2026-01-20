# src/core/backtesting/engine.py
"""
Advanced backtesting engine with comprehensive metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, List
from uuid import uuid4

import numpy as np
import pandas as pd

from ..types import (
    Trade, BacktestResult, BacktestMetrics,
    Symbol, Timeframe, PositionSide
)
from ..risk import RiskConfig, PositionSizer


@dataclass
class BacktestConfig:
    """
    Configuration for the backtesting engine.

    Supports both fixed percentage and ATR-based stop loss/take profit.
    """
    initial_capital: float = 10000.0

    # Fixed percentage SL/TP (used if atr_mult_sl is None)
    sl_pct: Optional[float] = 0.02  # 2% stop loss
    tp_rr: Optional[float] = 2.0    # Risk:Reward ratio for TP

    # ATR-based SL/TP (takes precedence if set)
    atr_mult_sl: Optional[float] = None  # e.g., 1.5 * ATR
    atr_mult_tp: Optional[float] = None  # e.g., 3.0 * ATR

    # Costs
    fee_pct: float = 0.001      # 0.1% commission
    slippage_pct: float = 0.0005  # 0.05% slippage

    # Trading rules
    allow_short: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")

        if self.fee_pct < 0:
            raise ValueError("fee_pct cannot be negative")

        if self.slippage_pct < 0 or self.slippage_pct > 0.05:
            raise ValueError("slippage_pct must be between 0 and 0.05")

        # Validate that we have either fixed or ATR-based SL/TP
        has_fixed = self.sl_pct is not None and self.tp_rr is not None
        has_atr = self.atr_mult_sl is not None and self.atr_mult_tp is not None

        if not has_fixed and not has_atr:
            raise ValueError(
                "Must configure either sl_pct/tp_rr or atr_mult_sl/atr_mult_tp"
            )

    @property
    def uses_atr(self) -> bool:
        """Check if ATR-based SL/TP is configured."""
        return self.atr_mult_sl is not None and self.atr_mult_tp is not None


class Backtester:
    """
    Event-driven backtesting engine.

    Features:
    - Fixed or ATR-based stop loss/take profit
    - Realistic slippage simulation
    - Commission handling
    - Comprehensive metrics calculation
    """

    REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "signal"}

    def __init__(
        self,
        config: BacktestConfig,
        risk_config: Optional[RiskConfig] = None
    ) -> None:
        self.config = config
        self.risk_config = risk_config or RiskConfig()
        self.position_sizer = PositionSizer(self.risk_config)

    def run(
        self,
        df: pd.DataFrame,
        symbol: Optional[Symbol] = None,
        timeframe: Optional[Timeframe] = None
    ) -> BacktestResult:
        """
        Run backtest on signal-annotated DataFrame.

        Args:
            df: DataFrame with OHLCV data and 'signal' column
            symbol: Optional symbol for metadata
            timeframe: Optional timeframe for metadata

        Returns:
            BacktestResult with trades, equity curve, and metrics
        """
        self._validate_dataframe(df)

        # Prepare data
        data = df.sort_values("timestamp").reset_index(drop=True).copy()

        # State
        capital = self.config.initial_capital
        equity_history: List[float] = []
        time_history: List[pd.Timestamp] = []
        trades: List[Trade] = []
        open_trade: Optional[Trade] = None

        for i in range(len(data)):
            row = data.iloc[i]

            # Check existing trade for exit
            if open_trade is not None:
                exit_price = self._check_exit(open_trade, row)

                if exit_price is not None:
                    # Close trade
                    open_trade = self._close_trade(
                        open_trade, row["timestamp"], exit_price
                    )
                    capital += open_trade.pnl
                    trades.append(open_trade)
                    open_trade = None

            # Record equity
            equity_history.append(capital)
            time_history.append(row["timestamp"])

            # Try to open new trade
            if open_trade is None:
                signal = int(row["signal"])
                open_trade = self._try_open_trade(signal, row, capital, symbol)

        # Close any remaining open trade at last close
        if open_trade is not None:
            last_row = data.iloc[-1]
            open_trade = self._close_trade(
                open_trade,
                last_row["timestamp"],
                float(last_row["close"])
            )
            capital += open_trade.pnl
            trades.append(open_trade)

        # Build equity curve
        equity_curve = pd.Series(
            equity_history,
            index=pd.to_datetime(time_history)
        )

        # Calculate metrics
        metrics = self._calculate_metrics(trades, equity_curve)

        return BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            symbol=symbol,
            timeframe=timeframe,
        )

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame has required columns."""
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if self.config.uses_atr and "atr" not in df.columns:
            raise ValueError("ATR-based SL/TP requires 'atr' column in DataFrame")

    def _compute_sl_tp(
        self,
        side: PositionSide,
        entry_price: float,
        atr: Optional[float]
    ) -> tuple[float, float]:
        """Calculate stop loss and take profit prices."""
        if self.config.uses_atr:
            if atr is None or np.isnan(atr):
                raise ValueError("ATR value required but not available")

            if side == PositionSide.LONG:
                sl = entry_price - atr * self.config.atr_mult_sl
                tp = entry_price + atr * self.config.atr_mult_tp
            else:
                sl = entry_price + atr * self.config.atr_mult_sl
                tp = entry_price - atr * self.config.atr_mult_tp
        else:
            if side == PositionSide.LONG:
                sl = entry_price * (1 - self.config.sl_pct)
                tp = entry_price * (1 + self.config.sl_pct * self.config.tp_rr)
            else:
                sl = entry_price * (1 + self.config.sl_pct)
                tp = entry_price * (1 - self.config.sl_pct * self.config.tp_rr)

        return sl, tp

    def _try_open_trade(
        self,
        signal: int,
        row: pd.Series,
        capital: float,
        symbol: Optional[Symbol]
    ) -> Optional[Trade]:
        """Attempt to open a new trade based on signal."""
        if signal == 0:
            return None

        if signal == -1 and not self.config.allow_short:
            return None

        side = PositionSide.LONG if signal == 1 else PositionSide.SHORT

        # Apply slippage to entry
        base_price = float(row["close"])
        slippage = self.config.slippage_pct

        if side == PositionSide.LONG:
            entry_price = base_price * (1 + slippage)
        else:
            entry_price = base_price * (1 - slippage)

        # Get ATR if available
        atr = float(row["atr"]) if "atr" in row.index else None

        # Calculate SL/TP
        sl, tp = self._compute_sl_tp(side, entry_price, atr)

        # Calculate position size
        size = self.position_sizer.calculate(
            capital=capital,
            entry_price=entry_price,
            stop_price=sl
        )

        if size <= 0:
            return None

        # Calculate entry fee
        fee = entry_price * size * self.config.fee_pct

        return Trade(
            id=str(uuid4())[:8],
            symbol=symbol,
            side=side,
            entry_time=row["timestamp"],
            exit_time=None,
            entry_price=entry_price,
            exit_price=None,
            size=size,
            stop_loss=sl,
            take_profit=tp,
            fees=fee,
        )

    def _check_exit(self, trade: Trade, row: pd.Series) -> Optional[float]:
        """Check if trade should exit, return exit price or None."""
        high = float(row["high"])
        low = float(row["low"])
        slippage = self.config.slippage_pct

        if trade.side == PositionSide.LONG:
            # Check stop loss first (conservative)
            if low <= trade.stop_loss:
                return trade.stop_loss * (1 - slippage)
            # Then take profit
            if high >= trade.take_profit:
                return trade.take_profit * (1 - slippage)
        else:
            # Short position
            if high >= trade.stop_loss:
                return trade.stop_loss * (1 + slippage)
            if low <= trade.take_profit:
                return trade.take_profit * (1 + slippage)

        return None

    def _close_trade(
        self,
        trade: Trade,
        exit_time: pd.Timestamp,
        exit_price: float
    ) -> Trade:
        """Close trade and calculate PnL."""
        # Exit fee
        exit_fee = exit_price * trade.size * self.config.fee_pct
        total_fees = trade.fees + exit_fee

        # Calculate PnL
        if trade.side == PositionSide.LONG:
            gross_pnl = (exit_price - trade.entry_price) * trade.size
        else:
            gross_pnl = (trade.entry_price - exit_price) * trade.size

        net_pnl = gross_pnl - total_fees

        # Calculate PnL percentage
        trade_value = trade.entry_price * trade.size
        pnl_pct = (net_pnl / trade_value) * 100 if trade_value > 0 else 0

        return replace(
            trade,
            exit_time=exit_time,
            exit_price=exit_price,
            pnl=net_pnl,
            pnl_pct=pnl_pct,
            fees=total_fees,
        )

    def _calculate_metrics(
        self,
        trades: List[Trade],
        equity_curve: pd.Series
    ) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics."""
        if not trades:
            return BacktestMetrics(
                total_return_pct=0.0,
                num_trades=0
            )

        # Basic counts
        num_trades = len(trades)
        pnl_values = np.array([t.pnl for t in trades if t.pnl is not None])

        if len(pnl_values) == 0:
            return BacktestMetrics(num_trades=num_trades)

        # Win/Loss
        winners = pnl_values[pnl_values > 0]
        losers = pnl_values[pnl_values < 0]

        winning_trades = len(winners)
        losing_trades = len(losers)
        win_rate = (winning_trades / num_trades) * 100

        # Profit metrics
        gross_profit = float(winners.sum()) if len(winners) > 0 else 0.0
        gross_loss = float(abs(losers.sum())) if len(losers) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Return
        initial = self.config.initial_capital
        final = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial
        total_return_pct = ((final - initial) / initial) * 100
        total_pnl = final - initial

        # Drawdown
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown_pct = float(drawdown.min()) * 100

        # Max drawdown duration
        is_dd = drawdown < 0
        dd_groups = (~is_dd).cumsum()
        dd_lengths = is_dd.groupby(dd_groups).sum()
        max_dd_duration = int(dd_lengths.max()) if len(dd_lengths) > 0 else 0

        # Trade averages
        avg_trade_pnl = float(pnl_values.mean())
        avg_winning_trade = float(winners.mean()) if len(winners) > 0 else 0.0
        avg_losing_trade = float(losers.mean()) if len(losers) > 0 else 0.0
        largest_winning_trade = float(winners.max()) if len(winners) > 0 else 0.0
        largest_losing_trade = float(losers.min()) if len(losers) > 0 else 0.0

        # Expectancy
        expectancy = (win_rate / 100 * avg_winning_trade) - ((1 - win_rate / 100) * abs(avg_losing_trade))

        # Risk-adjusted returns
        returns = equity_curve.pct_change().dropna()
        sharpe_ratio = self._calculate_sharpe(returns)
        sortino_ratio = self._calculate_sortino(returns)
        calmar_ratio = total_return_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0

        # Recovery factor
        recovery_factor = total_pnl / gross_loss if gross_loss > 0 else 0.0

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
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            avg_trade_pnl=avg_trade_pnl,
            avg_winning_trade=avg_winning_trade,
            avg_losing_trade=avg_losing_trade,
            largest_winning_trade=largest_winning_trade,
            largest_losing_trade=largest_losing_trade,
            expectancy=expectancy,
            recovery_factor=recovery_factor,
        )

    @staticmethod
    def _calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate annualized Sharpe ratio."""
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        std = excess_returns.std()

        if std == 0 or np.isnan(std):
            return 0.0

        return float((excess_returns.mean() / std) * np.sqrt(252))

    @staticmethod
    def _calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate annualized Sortino ratio (downside deviation only)."""
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        downside = excess_returns[excess_returns < 0]

        if len(downside) == 0:
            return float('inf')

        downside_std = downside.std()
        if downside_std == 0 or np.isnan(downside_std):
            return 0.0

        return float((excess_returns.mean() / downside_std) * np.sqrt(252))
