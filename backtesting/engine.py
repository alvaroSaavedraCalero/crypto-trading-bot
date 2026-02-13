from dataclasses import dataclass, field
from typing import List, Dict, Any, Type
import pandas as pd
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

        capital = self.config.initial_capital
        trades: List[TradeResult] = []
        in_position = False
        entry_price = 0.0
        entry_time = None
        side = ""
        position_size = 0.0
        sl_price = 0.0
        tp_price = 0.0
        peak_capital = capital

        for i in range(len(df_signals)):
            row = df_signals.iloc[i]
            signal = int(row.get("signal", 0))
            high = row["high"]
            low = row["low"]
            close = row["close"]
            ts = row["timestamp"] if "timestamp" in df_signals.columns else df_signals.index[i]

            if in_position:
                # Check if SL or TP hit during this candle
                exited = False
                exit_price = 0.0
                exit_reason = ""

                if side == "long":
                    if low <= sl_price:
                        exit_price = sl_price
                        exit_reason = "sl"
                        exited = True
                    elif high >= tp_price:
                        exit_price = tp_price
                        exit_reason = "tp"
                        exited = True
                elif side == "short":
                    if high >= sl_price:
                        exit_price = sl_price
                        exit_reason = "sl"
                        exited = True
                    elif low <= tp_price:
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
                    pnl_pct = (pnl / (entry_price * position_size)) * 100 if position_size > 0 else 0.0

                    capital += pnl

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
                            metadata={"exit_reason": exit_reason},
                        )
                    )
                    in_position = False

            # Open new position on signal (only if not already in position)
            if not in_position and signal != 0:
                if signal == -1 and not self.config.allow_short:
                    continue

                entry_price = close
                entry_time = ts if isinstance(ts, datetime) else ts.to_pydatetime()
                side = "long" if signal == 1 else "short"

                # Calculate SL/TP prices
                if side == "long":
                    sl_price = entry_price * (1 - self.config.sl_pct)
                    tp_price = entry_price * (1 + self.config.sl_pct * self.config.tp_rr)
                else:
                    sl_price = entry_price * (1 + self.config.sl_pct)
                    tp_price = entry_price * (1 - self.config.sl_pct * self.config.tp_rr)

                # Position sizing using risk management
                risk_pct = self.risk_config.risk_pct if hasattr(self.risk_config, "risk_pct") else 0.01
                position_size = calculate_position_size_spot(
                    capital=capital,
                    entry=entry_price,
                    stop_loss=sl_price,
                    risk_pct=risk_pct,
                )

                if position_size <= 0:
                    continue

                in_position = True

            # Track peak capital for drawdown
            if capital > peak_capital:
                peak_capital = capital

        # Calculate metrics
        result = self._calculate_metrics(trades, capital, peak_capital)
        return result

    def _calculate_metrics(
        self, trades: List[TradeResult], final_capital: float, peak_capital: float
    ) -> BacktestResult:
        """Calculate backtest performance metrics from trade list."""
        if not trades:
            return BacktestResult()

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

        # Max drawdown from equity curve
        max_dd = self._calculate_max_drawdown(trades)

        return BacktestResult(
            total_return_pct=round(total_return_pct, 4),
            winrate_pct=round(winrate, 2),
            profit_factor=round(profit_factor, 4),
            max_drawdown_pct=round(max_dd, 4),
            num_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            trades=trades,
        )

    def _calculate_max_drawdown(self, trades: List[TradeResult]) -> float:
        """Calculate maximum drawdown percentage from trade sequence."""
        if not trades:
            return 0.0

        equity = self.config.initial_capital
        peak = equity
        max_dd = 0.0

        for trade in trades:
            equity += trade.pnl
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return max_dd
