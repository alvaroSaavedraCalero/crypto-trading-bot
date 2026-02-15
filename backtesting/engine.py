from dataclasses import dataclass, field
from typing import List, Dict, Any, Type
import pandas as pd
import numpy as np
from datetime import datetime

from utils.risk import calculate_position_size_spot


@dataclass
class BacktestConfig:
    initial_capital: float
    sl_pct: float
    tp_rr: float
    fee_pct: float = 0.0005
    allow_short: bool = True


@dataclass
class TradeResult:
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: float
    exit_price: float
    position_size: float
    stop_loss_price: float
    take_profit_price: float
    pnl: float
    pnl_pct: float
    duration_candles: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    total_return_pct: float = 0.0
    winrate_pct: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    num_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    avg_trade_duration: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    expectancy: float = 0.0
    recovery_factor: float = 0.0
    equity_curve: List[float] = field(default_factory=list)
    trades: List[TradeResult] = field(default_factory=list)


class Backtester:
    def __init__(self, config: BacktestConfig, risk_config: Any):
        self.config = config
        self.risk_config = risk_config

    def backtest(
        self, df: pd.DataFrame, strategy_class: Type, strategy_config: Any
    ) -> BacktestResult:
        """
        Run a full backtest: generate signals, simulate trades, calculate metrics.

        Fixes applied:
        - Entry at NEXT candle's open (no look-ahead bias)
        - Pessimistic SL/TP check: whichever is closer to open hits first
        - No same-candle exit and re-entry
        - Intra-trade max drawdown via full equity curve
        - Signal strength support for position sizing

        Args:
            df: OHLCV DataFrame with DatetimeIndex
            strategy_class: Strategy class from registry
            strategy_config: Config dataclass for the strategy

        Returns:
            BacktestResult with trades and performance metrics
        """
        # Instantiate strategy and generate signals
        strategy = strategy_class(config=strategy_config)
        df_signals = strategy.generate_signals(df)

        if df_signals.empty or "signal" not in df_signals.columns:
            return BacktestResult()

        has_signal_strength = "signal_strength" in df_signals.columns

        capital = self.config.initial_capital
        trades: List[TradeResult] = []
        in_position = False
        entry_price = 0.0
        entry_time = None
        entry_candle_idx = 0
        side = ""
        position_size = 0.0
        sl_price = 0.0
        tp_price = 0.0

        # Pending signal from previous candle (for next-candle entry)
        pending_signal = 0
        pending_signal_strength = 1.0

        # Track equity curve every candle (including unrealized PnL)
        equity_curve: List[float] = []

        just_exited = False

        for i in range(len(df_signals)):
            row = df_signals.iloc[i]
            signal = int(row.get("signal", 0))
            sig_strength = float(row.get("signal_strength", 1.0)) if has_signal_strength else 1.0
            high = row["high"]
            low = row["low"]
            close = row["close"]
            open_price = row["open"]
            ts = row["timestamp"] if "timestamp" in df_signals.columns else df_signals.index[i]

            # Reset just_exited at start of each new candle
            exited_this_candle = False

            if in_position:
                # Check if SL or TP hit during this candle
                exit_price = 0.0
                exit_reason = ""
                exited = False

                if side == "long":
                    sl_hit = low <= sl_price
                    tp_hit = high >= tp_price
                    if sl_hit and tp_hit:
                        # Both could hit -- whichever is closer to open
                        dist_sl = abs(open_price - sl_price)
                        dist_tp = abs(open_price - tp_price)
                        if dist_sl <= dist_tp:
                            exit_price = sl_price
                            exit_reason = "sl"
                        else:
                            exit_price = tp_price
                            exit_reason = "tp"
                        exited = True
                    elif sl_hit:
                        exit_price = sl_price
                        exit_reason = "sl"
                        exited = True
                    elif tp_hit:
                        exit_price = tp_price
                        exit_reason = "tp"
                        exited = True

                elif side == "short":
                    sl_hit = high >= sl_price
                    tp_hit = low <= tp_price
                    if sl_hit and tp_hit:
                        dist_sl = abs(open_price - sl_price)
                        dist_tp = abs(open_price - tp_price)
                        if dist_sl <= dist_tp:
                            exit_price = sl_price
                            exit_reason = "sl"
                        else:
                            exit_price = tp_price
                            exit_reason = "tp"
                        exited = True
                    elif sl_hit:
                        exit_price = sl_price
                        exit_reason = "sl"
                        exited = True
                    elif tp_hit:
                        exit_price = tp_price
                        exit_reason = "tp"
                        exited = True

                # Also exit on opposing signal
                if not exited and signal != 0:
                    if (side == "long" and signal == -1) or (
                        side == "short" and signal == 1
                    ):
                        exit_price = close
                        exit_reason = "signal_reversal"
                        exited = True

                if exited:
                    # Calculate PnL
                    if side == "long":
                        raw_pnl = (exit_price - entry_price) * position_size
                    else:
                        raw_pnl = (entry_price - exit_price) * position_size

                    # Deduct fees (entry + exit)
                    fee_cost = (
                        entry_price * position_size * self.config.fee_pct
                        + exit_price * position_size * self.config.fee_pct
                    )
                    pnl = raw_pnl - fee_cost
                    pnl_pct = (
                        (pnl / (entry_price * position_size)) * 100
                        if position_size > 0
                        else 0.0
                    )

                    capital += pnl
                    duration = i - entry_candle_idx

                    trades.append(
                        TradeResult(
                            entry_time=entry_time,
                            exit_time=ts if isinstance(ts, datetime) else ts.to_pydatetime(),
                            side=side,
                            entry_price=entry_price,
                            exit_price=exit_price,
                            position_size=position_size,
                            stop_loss_price=sl_price,
                            take_profit_price=tp_price,
                            pnl=round(pnl, 4),
                            pnl_pct=round(pnl_pct, 4),
                            duration_candles=duration,
                            metadata={"exit_reason": exit_reason},
                        )
                    )
                    in_position = False
                    exited_this_candle = True

            # Execute pending entry from previous candle's signal (enter at this candle's open)
            if not in_position and not exited_this_candle and pending_signal != 0:
                if pending_signal == -1 and not self.config.allow_short:
                    pending_signal = 0
                    pending_signal_strength = 1.0
                else:
                    entry_price = open_price
                    entry_time = ts if isinstance(ts, datetime) else ts.to_pydatetime()
                    entry_candle_idx = i
                    side = "long" if pending_signal == 1 else "short"

                    # Calculate SL/TP prices
                    if side == "long":
                        sl_price = entry_price * (1 - self.config.sl_pct)
                        tp_price = entry_price * (1 + self.config.sl_pct * self.config.tp_rr)
                    else:
                        sl_price = entry_price * (1 + self.config.sl_pct)
                        tp_price = entry_price * (1 - self.config.sl_pct * self.config.tp_rr)

                    # Position sizing using risk management
                    risk_pct = (
                        self.risk_config.risk_pct
                        if hasattr(self.risk_config, "risk_pct")
                        else 0.01
                    )
                    # Scale risk by signal strength
                    effective_risk = risk_pct * pending_signal_strength
                    position_size = calculate_position_size_spot(
                        capital=capital,
                        entry=entry_price,
                        stop_loss=sl_price,
                        risk_pct=effective_risk,
                    )

                    pending_signal = 0
                    pending_signal_strength = 1.0

                    if position_size <= 0:
                        in_position = False
                    else:
                        in_position = True

            # Store signal for next candle entry (only if not already in position)
            if not in_position and signal != 0:
                pending_signal = signal
                pending_signal_strength = sig_strength
            elif in_position:
                # Clear any pending signal while in position
                pending_signal = 0
                pending_signal_strength = 1.0

            # Update equity curve with unrealized PnL
            if in_position:
                if side == "long":
                    unrealized = (close - entry_price) * position_size
                else:
                    unrealized = (entry_price - close) * position_size
                equity_curve.append(capital + unrealized)
            else:
                equity_curve.append(capital)

        # Calculate metrics
        result = self._calculate_metrics(trades, capital, equity_curve)
        return result

    def _calculate_metrics(
        self,
        trades: List[TradeResult],
        final_capital: float,
        equity_curve: List[float],
    ) -> BacktestResult:
        """Calculate backtest performance metrics from trade list."""
        if not trades:
            return BacktestResult(
                equity_curve=equity_curve if equity_curve else [self.config.initial_capital]
            )

        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]

        total_return_pct = (
            (final_capital - self.config.initial_capital) / self.config.initial_capital
        ) * 100

        winrate = (len(winning) / len(trades)) * 100 if trades else 0.0

        gross_profit = sum(t.pnl for t in winning)
        gross_loss = abs(sum(t.pnl for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        if profit_factor == float("inf"):
            profit_factor = 99.99

        # Max drawdown from full equity curve (intra-trade)
        max_dd = self._calculate_max_drawdown_from_curve(equity_curve)

        # Sharpe, Sortino, Calmar ratios
        sharpe = self._calculate_sharpe_ratio(equity_curve)
        sortino = self._calculate_sortino_ratio(equity_curve)
        annualized_return = total_return_pct / 100  # as a fraction
        calmar = (annualized_return / (max_dd / 100)) if max_dd > 0 else 99.99

        # Average trade duration
        avg_duration = (
            sum(t.duration_candles for t in trades) / len(trades) if trades else 0.0
        )

        # Max consecutive wins/losses
        max_consec_wins, max_consec_losses = self._max_consecutive(trades)

        # Expectancy
        win_rate_frac = len(winning) / len(trades) if trades else 0
        loss_rate_frac = len(losing) / len(trades) if trades else 0
        avg_win = gross_profit / len(winning) if winning else 0
        avg_loss = gross_loss / len(losing) if losing else 0
        expectancy = (win_rate_frac * avg_win) - (loss_rate_frac * avg_loss)

        # Recovery factor
        total_profit = final_capital - self.config.initial_capital
        recovery_factor = total_profit / (max_dd / 100 * self.config.initial_capital) if max_dd > 0 else 99.99

        return BacktestResult(
            total_return_pct=round(total_return_pct, 4),
            winrate_pct=round(winrate, 2),
            profit_factor=round(profit_factor, 4),
            max_drawdown_pct=round(max_dd, 4),
            num_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            calmar_ratio=round(calmar, 4),
            avg_trade_duration=round(avg_duration, 2),
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            expectancy=round(expectancy, 4),
            recovery_factor=round(recovery_factor, 4),
            equity_curve=equity_curve,
            trades=trades,
        )

    def _calculate_max_drawdown_from_curve(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown percentage from the full equity curve."""
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self, equity_curve: List[float]) -> float:
        """Annualized Sharpe Ratio from equity curve returns (assuming 252 trading days)."""
        if len(equity_curve) < 2:
            return 0.0

        arr = np.array(equity_curve)
        returns = np.diff(arr) / arr[:-1]

        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        return float((np.mean(returns) / np.std(returns)) * np.sqrt(252))

    def _calculate_sortino_ratio(self, equity_curve: List[float]) -> float:
        """Annualized Sortino Ratio (downside deviation only)."""
        if len(equity_curve) < 2:
            return 0.0

        arr = np.array(equity_curve)
        returns = np.diff(arr) / arr[:-1]

        downside = returns[returns < 0]
        if len(downside) == 0:
            return 99.99

        downside_std = np.std(downside)
        if downside_std == 0:
            return 99.99

        return float((np.mean(returns) / downside_std) * np.sqrt(252))

    @staticmethod
    def _max_consecutive(trades: List[TradeResult]) -> tuple:
        """Return (max_consecutive_wins, max_consecutive_losses)."""
        max_wins = 0
        max_losses = 0
        cur_wins = 0
        cur_losses = 0

        for t in trades:
            if t.pnl > 0:
                cur_wins += 1
                cur_losses = 0
                if cur_wins > max_wins:
                    max_wins = cur_wins
            else:
                cur_losses += 1
                cur_wins = 0
                if cur_losses > max_losses:
                    max_losses = cur_losses

        return max_wins, max_losses

    def walk_forward_backtest(
        self,
        df: pd.DataFrame,
        strategy_class: Type,
        config: Any,
        train_window: int = 500,
        test_window: int = 100,
        step: int = 50,
    ) -> List[BacktestResult]:
        """
        Walk-forward analysis: rolling train/test windows.

        Slides a window across the data, running a backtest on each test segment.
        Returns a list of BacktestResult objects, one per test window.
        """
        results = []
        n = len(df)
        start = 0

        while start + train_window + test_window <= n:
            test_start = start + train_window
            test_end = test_start + test_window

            # Use the test window slice for backtesting
            test_df = df.iloc[test_start:test_end].copy().reset_index(drop=True)

            if len(test_df) < 10:
                break

            result = self.backtest(test_df, strategy_class, config)
            results.append(result)

            start += step

        return results

    def monte_carlo(
        self, trades: List[TradeResult], n_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Monte Carlo simulation: shuffle trade PnLs and compute distribution of outcomes.

        Returns dict with percentile stats of final equity and max drawdown.
        """
        if not trades:
            return {"final_equity": {}, "max_drawdown": {}}

        pnls = np.array([t.pnl for t in trades])
        initial = self.config.initial_capital

        final_equities = []
        max_drawdowns = []

        rng = np.random.default_rng(seed=42)

        for _ in range(n_simulations):
            shuffled = rng.permutation(pnls)
            equity = initial
            peak = equity
            max_dd = 0.0

            for pnl in shuffled:
                equity += pnl
                if equity > peak:
                    peak = equity
                dd = ((peak - equity) / peak) * 100 if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd

            final_equities.append(equity)
            max_drawdowns.append(max_dd)

        final_equities = np.array(final_equities)
        max_drawdowns = np.array(max_drawdowns)

        percentiles = [5, 25, 50, 75, 95]

        return {
            "final_equity": {
                f"p{p}": round(float(np.percentile(final_equities, p)), 2)
                for p in percentiles
            },
            "max_drawdown": {
                f"p{p}": round(float(np.percentile(max_drawdowns, p)), 4)
                for p in percentiles
            },
            "mean_final_equity": round(float(np.mean(final_equities)), 2),
            "mean_max_drawdown": round(float(np.mean(max_drawdowns)), 4),
        }
