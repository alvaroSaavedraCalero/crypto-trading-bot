#!/usr/bin/env python3
"""
Export Optimized Forex Parameters for Configuration
Generates configuration files ready to use in trading
"""

import json
from pathlib import Path
from rich.console import Console

console = Console()

# Load best parameters
BEST_PARAMS_FILE = "forex_best_params_20260126_154943.json"

if not Path(BEST_PARAMS_FILE).exists():
    console.print(f"[red]Error: {BEST_PARAMS_FILE} not found[/red]")
    exit(1)

with open(BEST_PARAMS_FILE, "r") as f:
    best_params = json.load(f)

console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
console.print("[bold cyan]     OPTIMIZED PARAMETERS - QUICK REFERENCE GUIDE            [/bold cyan]")
console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")

# Python configuration
python_config = """#!/usr/bin/env python3
\"\"\"
Optimized Forex Strategy Configurations
Generated: 2026-01-26
Pairs: EURUSD, USDJPY
Timeframe: 15m
\"\"\"

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
"""

# YAML configuration
yaml_config = """
# Optimized Forex Strategy Parameters
# Generated: 2026-01-26
# Pairs: EURUSD, USDJPY | Timeframe: 15m

strategies:
  BOLLINGER_MR:
    name: "Bollinger Mean Reversion"
    description: "Mean reversion using Bollinger Bands + RSI"
    optimized_for: "USDJPY"
    expected_return: "-2.11%"
    parameters:
      bb_window: 15          # Bollinger Bands period
      bb_std: 2.0            # Standard deviations
      rsi_window: 14         # RSI period
      rsi_oversold: 25.0     # Oversold threshold
      rsi_overbought: 70.0   # Overbought threshold
    
  KELTNER:
    name: "Keltner Breakout"
    description: "Breakout strategy using Keltner Channel"
    optimized_for: "USDJPY"
    expected_return: "-2.09%"
    parameters:
      kc_window: 25              # Channel period
      kc_mult: 2.5               # ATR multiplier
      atr_window: 20             # ATR period
      atr_min_percentile: 0.4    # Minimum volatility filter
  
  MA_RSI:
    name: "Moving Average + RSI"
    description: "MA cross strategy with RSI confirmation"
    optimized_for: "USDJPY"
    expected_return: "-1.08%"
    parameters:
      fast_window: 10        # Fast MA period
      slow_window: 20        # Slow MA period
      rsi_window: 14         # RSI period
      rsi_overbought: 70.0   # Overbought level
      rsi_oversold: 30.0     # Oversold level
      use_rsi_filter: false  # Don't use additional RSI filter
"""

# JSON configuration (already exists, but show format)
json_config = json.dumps(best_params, indent=2)

# Display all formats
console.print("[bold magenta]1. PYTHON DATACLASS FORMAT[/bold magenta]\n")
console.print("[cyan]" + python_config + "[/cyan]\n")

console.print("[bold magenta]2. YAML CONFIGURATION FORMAT[/bold magenta]\n")
console.print("[cyan]" + yaml_config + "[/cyan]\n")

console.print("[bold magenta]3. JSON FORMAT[/bold magenta]\n")
console.print("[cyan]" + json_config + "[/cyan]\n")

# Save to files
with open("optimized_strategies_config.py", "w") as f:
    f.write(python_config)

with open("optimized_strategies_config.yaml", "w") as f:
    f.write(yaml_config)

console.print("[bold green]✓ Configuration files saved:[/bold green]")
console.print("  • optimized_strategies_config.py")
console.print("  • optimized_strategies_config.yaml")
console.print("  • forex_best_params_20260126_154943.json (existing)\n")

# Summary table
from rich.table import Table

summary = Table(title="Optimized Strategy Summary")
summary.add_column("Strategy", style="cyan")
summary.add_column("Best Pair")
summary.add_column("Expected Return")
summary.add_column("Key Parameters")

for strategy, config in best_params.items():
    params = config["parameters"]
    key_params = ", ".join([f"{k[:6]}={v}" for k, v in list(params.items())[:2]])
    
    summary.add_row(
        strategy,
        config["best_pair"],
        f"{config['return']:.2f}%",
        key_params + "..."
    )

console.print(summary)
console.print()
