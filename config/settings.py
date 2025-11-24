# config/settings.py

from dataclasses import dataclass

from backtesting.engine import BacktestConfig

from strategies.macd_adx_trend_strategy import MACDADXTrendStrategyConfig
from strategies.supertrend_strategy import SupertrendStrategyConfig
from strategies.keltner_breakout_strategy import KeltnerBreakoutStrategyConfig
from strategies.bollinger_mean_reversion import BollingerMeanReversionStrategyConfig

from utils.risk import RiskManagementConfig


# ==========================
# Configuración general
# ==========================

# Velas máximas por defecto para backtests
DEFAULT_LIMIT_CANDLES: int = 5000

# Config base de backtest (se usa como "plantilla" en optimizadores)
BACKTEST_CONFIG = BacktestConfig(
    initial_capital=1000.0,
    sl_pct=0.005,      # valor por defecto; los optimizadores lo sobreescriben con replace(...)
    tp_rr=2.0,
    fee_pct=0.0005,
    allow_short=True,
    atr_window=None,
    atr_mult_sl=None,
    atr_mult_tp=None,
)

# Riesgo general (spot): 1% por operación
RISK_CONFIG = RiskManagementConfig(
    risk_pct=0.01,
)


# ==========================
# Tipo genérico de "run" de estrategia
# ==========================

@dataclass
class StrategyRunConfig:
    name: str
    symbol: str
    timeframe: str
    limit_candles: int
    strategy_type: str       # "MA_RSI", "MACD_ADX", "KELTNER", etc.
    strategy_config: object
    backtest_config: BacktestConfig





# ==========================
# Estrategia 2: MACD+ADX+Trend (ETH/USDT 15m)
# ==========================

MACD_ADX_ETH15M_CONFIG = MACDADXTrendStrategyConfig(
    fast_ema=12,
    slow_ema=20,
    signal_ema=6,
    trend_ema_window=100,
    adx_window=14,
    adx_threshold=20.0,
    allow_short=False,
)

MACD_ADX_ETH15M_BT_CONFIG = BacktestConfig(
    initial_capital=1000.0,
    sl_pct=0.01,     # 1% SL
    tp_rr=2.5,       # TP 1:2.5
    fee_pct=0.0005,
    allow_short=False,
    atr_window=None,
    atr_mult_sl=None,
    atr_mult_tp=None,
)

MACD_ADX_ETH15M_RUN = StrategyRunConfig(
    name="MACD_ADX_TREND_OPT_ETHUSDT_15m",
    symbol="ETH/USDT",
    timeframe="15m",
    limit_candles=DEFAULT_LIMIT_CANDLES,
    strategy_type="MACD_ADX",
    strategy_config=MACD_ADX_ETH15M_CONFIG,
    backtest_config=MACD_ADX_ETH15M_BT_CONFIG,
)





# ==========================
# Estrategia 2: Supertrend (BTC/USDT 15m)
# ==========================

SUPERTREND_BTC15M_CONFIG = SupertrendStrategyConfig(
    atr_period=20,
    atr_multiplier=4.0,
    use_adx_filter=True,
    adx_period=14,
    adx_threshold=25.0,
)

SUPERTREND_BTC15M_BT_CONFIG = BacktestConfig(
    initial_capital=1000.0,
    sl_pct=0.01,     # 1% SL
    tp_rr=5.0,       # TP 1:5
    fee_pct=0.0005,
    allow_short=True,
)

SUPERTREND_BTC15M_RUN = StrategyRunConfig(
    name="SUPERTREND_OPT_BTCUSDT_15m",
    symbol="BTC/USDT",
    timeframe="15m",
    limit_candles=DEFAULT_LIMIT_CANDLES,
    strategy_type="SUPERTREND",
    strategy_config=SUPERTREND_BTC15M_CONFIG,
    backtest_config=SUPERTREND_BTC15M_BT_CONFIG,
)


# ==========================
# Estrategia 3: Bollinger Mean Reversion (BNB/USDT 15m)
# ==========================

# Keltner Breakout (SOL/USDT 15m) - Optimized
KELTNER_SOL15M_CONFIG = KeltnerBreakoutStrategyConfig(
    kc_window=30,
    kc_mult=2.5,
    atr_window=20,
    atr_min_percentile=0.4,
    use_trend_filter=False,
    trend_ema_window=100,
    allow_short=True,
    side_mode="both",
)

KELTNER_SOL15M_BT_CONFIG = BacktestConfig(
    initial_capital=1000.0,
    sl_pct=0.0075,   # 0.75% SL
    tp_rr=2.0,       # TP 1:2
    fee_pct=0.0005,
    allow_short=True,
    atr_window=None,
    atr_mult_sl=None,
    atr_mult_tp=None,
)

KELTNER_SOL15M_RUN = StrategyRunConfig(
    name="KELTNER_BREAKOUT_OPT_SOLUSDT_15m",
    symbol="SOL/USDT",
    timeframe="15m",
    limit_candles=DEFAULT_LIMIT_CANDLES,
    strategy_type="KELTNER",
    strategy_config=KELTNER_SOL15M_CONFIG,
    backtest_config=KELTNER_SOL15M_BT_CONFIG,
)


# ==========================
# Registro de estrategias optimizadas
# (usado por backtest_strategies.py)
# ==========================

OPTIMIZED_STRATEGIES = [
    MACD_ADX_ETH15M_RUN,
    SUPERTREND_BTC15M_RUN,
    KELTNER_SOL15M_RUN,
]
