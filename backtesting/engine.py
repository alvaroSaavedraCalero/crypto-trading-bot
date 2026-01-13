# backtesting/engine.py

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd

from utils.risk import RiskManagementConfig, calculate_position_size_spot


@dataclass
class BacktestConfig:
    initial_capital: float
    sl_pct: Optional[float] = 0.01      # stop loss fijo (puede ser None)
    tp_rr: Optional[float] = 2.0        # ratio TP:SL (solo si sl_pct no es None)
    fee_pct: float = 0.0005
    allow_short: bool = True

    # Parámetros ATR opcionales
    atr_window: Optional[int] = None    # si None, no se exige columna 'atr'
    atr_mult_sl: Optional[float] = None # si no es None -> usar ATR para SL
    atr_mult_tp: Optional[float] = None # idem para TP


def compute_sl_tp(
    cfg: BacktestConfig,
    side: str,
    entry_price: float,
    atr: float | None,
) -> tuple[float, float]:
    """
    Calcula SL y TP según la configuración:
    - Si cfg.atr_mult_sl no es None -> usa ATR.
    - Si no -> usa sl_pct y tp_rr.

    side: "long" o "short".
    """
    # Modo ATR dinámico
    if cfg.atr_mult_sl is not None and cfg.atr_mult_tp is not None:
        if atr is None or np.isnan(atr):
            raise ValueError(
                "Se ha solicitado usar ATR para SL/TP, pero no hay columna 'atr' válida en el DataFrame."
            )

        if side == "long":
            sl_price = entry_price - atr * cfg.atr_mult_sl
            tp_price = entry_price + atr * cfg.atr_mult_tp
        else:  # short
            sl_price = entry_price + atr * cfg.atr_mult_sl
            tp_price = entry_price - atr * cfg.atr_mult_tp

        return sl_price, tp_price

    # Modo SL fijo por porcentaje
    if cfg.sl_pct is None or cfg.tp_rr is None:
        raise ValueError(
            "Ni ATR ni SL fijo están correctamente configurados. "
            "Configura atr_mult_sl/atr_mult_tp o sl_pct/tp_rr."
        )

    if side == "long":
        sl_price = entry_price * (1.0 - cfg.sl_pct)
        tp_price = entry_price * (1.0 + cfg.sl_pct * cfg.tp_rr)
    else:  # short
        sl_price = entry_price * (1.0 + cfg.sl_pct)
        tp_price = entry_price * (1.0 - cfg.sl_pct * cfg.tp_rr)

    return sl_price, tp_price


@dataclass
class Trade:
    """
    Representa una operación individual.
    """
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp]
    direction: str  # "long" o "short"
    entry_price: float
    exit_price: Optional[float]
    size: float
    stop_price: float
    tp_price: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


@dataclass
class BacktestResult:
    """
    Resultado del backtest.
    """
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series | None = None
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    winrate_pct: float = 0.0
    profit_factor: float = 0.0
    num_trades: int = 0


class Backtester:
    """
    Motor de backtesting simple basado en señales:
    - Usa la columna 'signal' (1, -1, 0) del DataFrame.
    - Usa reglas de SL/TP basadas en porcentaje o ATR dinámico.
    - Usa gestión de riesgo separada (utils.risk).
    """

    def __init__(
        self,
        backtest_config: BacktestConfig,
        risk_config: RiskManagementConfig,
    ) -> None:
        if backtest_config is None:
            raise ValueError("backtest_config no puede ser None")
        if risk_config is None:
            raise ValueError("risk_config no puede ser None")

        self.backtest_config = backtest_config
        self.risk_config = risk_config

    def run(self, df: pd.DataFrame) -> BacktestResult:
        """
        Ejecuta el backtest sobre un DataFrame que debe contener al menos:
        - timestamp
        - open
        - high
        - low
        - close
        - signal

        Si se usan parámetros ATR (atr_mult_*), el DataFrame debe tener una
        columna 'atr' coherente con atr_window (esto se comprueba en compute_sl_tp).

        Devuelve un BacktestResult con trades, equity curve y métricas.
        """
        self._validate_dataframe(df)
        data = df.sort_values("timestamp").reset_index(drop=True).copy()

        capital = self.backtest_config.initial_capital
        equity_list: List[float] = []
        equity_times: List[pd.Timestamp] = []
        trades: List[Trade] = []
        open_trade: Optional[Trade] = None

        for i in range(len(data)):
            row = data.iloc[i]

            # Check and close existing trade if stop-loss or take-profit hit
            if open_trade is not None:
                open_trade, capital = self._check_and_close_trade(
                    open_trade, row, capital, trades
                )

            # Record equity after handling potential trade closure
            equity_list.append(capital)
            equity_times.append(row["timestamp"])

            # Try to open new trade based on signal
            if open_trade is None:
                open_trade, capital = self._try_open_trade(row, capital)

        equity_series = pd.Series(equity_list, index=pd.to_datetime(equity_times))
        return self._calculate_metrics(trades, equity_series)

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate that the DataFrame contains all required columns."""
        required_cols = {"timestamp", "open", "high", "low", "close", "signal"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Faltan columnas necesarias en el DataFrame: {missing}")

    def _check_and_close_trade(
        self,
        open_trade: Trade,
        row: pd.Series,
        capital: float,
        trades: List[Trade],
    ) -> tuple[Optional[Trade], float]:
        """
        Check if an open trade should be closed due to SL or TP being hit.
        Returns updated open_trade (None if closed) and capital.
        """
        exit_price = self._get_exit_price(open_trade, row)

        if exit_price is None:
            return open_trade, capital

        # Calculate PnL and close trade
        pnl = self._calculate_trade_pnl(open_trade, exit_price)
        fee_exit = exit_price * open_trade.size * self.backtest_config.fee_pct
        pnl_after_fees = pnl - fee_exit
        capital += pnl_after_fees

        # Update trade with exit information
        open_trade.exit_time = row["timestamp"]
        open_trade.exit_price = exit_price
        open_trade.pnl = pnl_after_fees
        open_trade.pnl_pct = pnl_after_fees / self.backtest_config.initial_capital * 100.0

        trades.append(open_trade)
        return None, capital

    def _get_exit_price(self, trade: Trade, row: pd.Series) -> Optional[float]:
        """
        Determine if trade should exit and return exit price.
        Checks SL first (conservative), then TP.
        Returns None if neither SL nor TP was hit.
        """
        high = float(row["high"])
        low = float(row["low"])

        if trade.direction == "long":
            if low <= trade.stop_price:
                return trade.stop_price  # SL hit
            if high >= trade.tp_price:
                return trade.tp_price  # TP hit
        else:  # short
            if high >= trade.stop_price:
                return trade.stop_price  # SL hit
            if low <= trade.tp_price:
                return trade.tp_price  # TP hit

        return None

    def _calculate_trade_pnl(self, trade: Trade, exit_price: float) -> float:
        """Calculate the PnL for a trade (before fees)."""
        if trade.direction == "long":
            return (exit_price - trade.entry_price) * trade.size
        else:  # short
            return (trade.entry_price - exit_price) * trade.size

    def _try_open_trade(
        self,
        row: pd.Series,
        capital: float,
    ) -> tuple[Optional[Trade], float]:
        """
        Try to open a new trade based on the signal in the current row.
        Returns updated open_trade and capital.
        """
        signal = int(row["signal"])
        if signal == 0:
            return None, capital

        direction = self._get_trade_direction(signal)
        if direction is None:
            return None, capital

        entry_price = float(row["close"])
        atr_value = float(row["atr"]) if "atr" in row.index else None

        # Calculate stop-loss and take-profit prices
        sl_price, tp_price = compute_sl_tp(
            cfg=self.backtest_config,
            side=direction,
            entry_price=entry_price,
            atr=atr_value,
        )

        # Calculate position size
        size = calculate_position_size_spot(
            capital=capital,
            entry_price=entry_price,
            stop_price=sl_price,
            config=self.risk_config,
        )

        if size <= 0:
            return None, capital

        # Deduct entry fee from capital
        fee_entry = entry_price * size * self.backtest_config.fee_pct
        capital -= fee_entry

        new_trade = Trade(
            entry_time=row["timestamp"],
            exit_time=None,
            direction=direction,
            entry_price=entry_price,
            exit_price=None,
            size=size,
            stop_price=sl_price,
            tp_price=tp_price,
        )

        return new_trade, capital

    def _get_trade_direction(self, signal: int) -> Optional[str]:
        """Convert signal to trade direction, respecting allow_short config."""
        if signal == 1:
            return "long"
        if signal == -1 and self.backtest_config.allow_short:
            return "short"
        return None

    def _calculate_metrics(
        self,
        trades: List[Trade],
        equity_curve: pd.Series,
    ) -> BacktestResult:
        """
        Calcula métricas básicas a partir de la lista de trades y la equity curve.
        """
        num_trades = len(trades)

        if len(equity_curve) == 0:
            total_return_pct = 0.0
        else:
            initial = equity_curve.iloc[0]
            final = equity_curve.iloc[-1]
            total_return_pct = (final / initial - 1.0) * 100.0

        # Max drawdown
        if len(equity_curve) > 0:
            running_max = equity_curve.cummax()
            drawdown = (equity_curve - running_max) / running_max
            max_drawdown_pct = drawdown.min() * 100.0
        else:
            max_drawdown_pct = 0.0

        # Winrate y profit factor
        pnl_list = [t.pnl for t in trades if t.pnl is not None]
        pnl_array = np.array(pnl_list) if pnl_list else np.array([])

        if len(pnl_array) > 0:
            wins = pnl_array[pnl_array > 0]
            losses = pnl_array[pnl_array < 0]

            winrate_pct = (len(wins) / len(pnl_array)) * 100.0 if len(pnl_array) > 0 else 0.0
            gross_profit = wins.sum() if len(wins) > 0 else 0.0
            gross_loss = losses.sum() if len(losses) > 0 else 0.0

            if gross_loss < 0:
                profit_factor = gross_profit / abs(gross_loss) if abs(gross_loss) > 0 else np.nan
            else:
                profit_factor = np.nan
        else:
            winrate_pct = 0.0
            profit_factor = 0.0

        return BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            winrate_pct=winrate_pct,
            profit_factor=profit_factor,
            num_trades=num_trades,
        )
