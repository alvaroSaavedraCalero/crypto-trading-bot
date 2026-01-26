#!/usr/bin/env python3
"""
Optimized Forex Strategy Configurations
Generated: 2026-01-26
Pairs: EURUSD, USDJPY
Timeframe: 15m
"""

from dataclasses import dataclass

# ============================================================================
# BOLLINGER MEAN REVERSION - Optimized for USDJPY
# ============================================================================
@dataclass
class BollingerMROptimized:
    bb_window: int = 15
    bb_std: float = 2.0
    rsi_window: int = 14
    rsi_oversold: float = 25.0
    rsi_overbought: float = 70.0
    
    # Expected Performance: -2.11% on USDJPY (2 trades)
    # Best for: Mean reversion setups, support/resistance bounces


# ============================================================================
# KELTNER BREAKOUT - Optimized for USDJPY
# ============================================================================
@dataclass
class KeltnerOptimized:
    kc_window: int = 25
    kc_mult: float = 2.5
    atr_window: int = 20
    atr_min_percentile: float = 0.4
    
    # Expected Performance: -2.09% on USDJPY (2 trades)
    # Best for: Channel breakouts, momentum trades


# ============================================================================
# MA_RSI STRATEGY - Optimized for USDJPY
# ============================================================================
@dataclass
class MARequiredOptimized:
    fast_window: int = 10
    slow_window: int = 20
    rsi_window: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    use_rsi_filter: bool = False
    
    # Expected Performance: -1.08% on USDJPY (1 trade)
    # Best for: Moving average crosses, trend confirmation


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

from strategies.registry import STRATEGY_REGISTRY

# Example 1: Using BOLLINGER_MR
config = BollingerMROptimized()
strategy_class, config_class = STRATEGY_REGISTRY["BOLLINGER_MR"]
strategy = strategy_class(config_class(**config.__dict__))

# Example 2: Using KELTNER
config = KeltnerOptimized()
strategy_class, config_class = STRATEGY_REGISTRY["KELTNER"]
strategy = strategy_class(config_class(**config.__dict__))

# Example 3: Using MA_RSI
config = MARequired  Optimized()
strategy_class, config_class = STRATEGY_REGISTRY["MA_RSI"]
strategy = strategy_class(config_class(**config.__dict__))
