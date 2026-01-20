#!/usr/bin/env python3
"""
Forex Backtesting Example

This example demonstrates how to:
1. Fetch Forex data using FXCM adapter
2. Run a backtest with Supertrend strategy
3. Display comprehensive metrics

Works on any OS (Windows, Linux, macOS) and in Europe.
No OANDA account required.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta

from src.core.types import Symbol, Timeframe, MarketType
from src.core.backtesting import Backtester, BacktestConfig
from src.core.risk import RiskConfig
from src.core.strategies.implementations.supertrend import SupertrendStrategy, SupertrendConfig
from src.adapters.data_sources import DataSourceFactory, FXCMConfig


def run_forex_backtest():
    """Run a simple Forex backtest."""
    print("=" * 60)
    print("FOREX BACKTESTING EXAMPLE")
    print("=" * 60)

    # 1. Setup symbol and timeframe
    symbol = Symbol("EUR", "USD", MarketType.FOREX)
    timeframe = Timeframe.from_string("15m")

    print(f"\nSymbol: {symbol}")
    print(f"Timeframe: {timeframe}")

    # 2. Create data adapter
    # Option A: Use FXCM adapter (fetches from free API or yfinance)
    adapter = DataSourceFactory.create_forex()

    # Option B: Use offline CSV data (if you have downloaded data)
    # adapter = DataSourceFactory.create_forex(offline_data_dir="./data/forex")

    # 3. Fetch historical data
    print("\nFetching data...")
    try:
        df = adapter.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=5000  # ~52 days of 15m data
        )
        print(f"Loaded {len(df)} candles")
        print(f"Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    except Exception as e:
        print(f"\nCould not fetch live data: {e}")
        print("\nTo use offline data, download historical data from:")
        print("  - HistData.com: https://www.histdata.com/download-free-forex-data/")
        print("  - Dukascopy: https://www.dukascopy.com/swiss/english/marketwatch/historical/")
        print("\nThen use:")
        print('  adapter = DataSourceFactory.create_csv("./data/forex")')
        return

    # 4. Configure strategy
    strategy_config = SupertrendConfig(
        atr_period=10,
        atr_multiplier=3.0,
        use_adx_filter=True,
        adx_threshold=20.0,
        allow_short=True
    )

    strategy = SupertrendStrategy(strategy_config)
    print(f"\nStrategy: {strategy.metadata.name}")

    # 5. Generate signals
    print("Generating signals...")
    df_signals = strategy.generate_signals(df)

    signal_counts = df_signals["signal"].value_counts()
    print(f"Signals generated:")
    print(f"  Long (1): {signal_counts.get(1, 0)}")
    print(f"  Short (-1): {signal_counts.get(-1, 0)}")
    print(f"  Neutral (0): {signal_counts.get(0, 0)}")

    # 6. Configure backtest
    backtest_config = BacktestConfig(
        initial_capital=10000.0,
        sl_pct=0.01,       # 1% stop loss
        tp_rr=2.0,         # 1:2 risk/reward
        fee_pct=0.0002,    # Spread (2 pips for EUR/USD)
        slippage_pct=0.0001,
        allow_short=True
    )

    risk_config = RiskConfig(
        risk_pct=0.01,  # 1% risk per trade
        max_position_pct=0.25
    )

    # 7. Run backtest
    print("\nRunning backtest...")
    backtester = Backtester(backtest_config, risk_config)
    result = backtester.run(df_signals, symbol=symbol, timeframe=timeframe)

    # 8. Display results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)

    metrics = result.metrics
    print(f"\nPerformance Metrics:")
    print(f"  Total Return: {metrics.total_return_pct:.2f}%")
    print(f"  Total PnL: ${metrics.total_pnl:.2f}")
    print(f"  Number of Trades: {metrics.num_trades}")

    print(f"\nWin/Loss Metrics:")
    print(f"  Win Rate: {metrics.win_rate:.1f}%")
    print(f"  Winning Trades: {metrics.winning_trades}")
    print(f"  Losing Trades: {metrics.losing_trades}")

    print(f"\nProfit Metrics:")
    print(f"  Profit Factor: {metrics.profit_factor:.2f}")
    print(f"  Gross Profit: ${metrics.gross_profit:.2f}")
    print(f"  Gross Loss: ${metrics.gross_loss:.2f}")

    print(f"\nRisk Metrics:")
    print(f"  Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"  Sortino Ratio: {metrics.sortino_ratio:.2f}")

    print(f"\nTrade Statistics:")
    print(f"  Avg Trade PnL: ${metrics.avg_trade_pnl:.2f}")
    print(f"  Avg Winner: ${metrics.avg_winning_trade:.2f}")
    print(f"  Avg Loser: ${metrics.avg_losing_trade:.2f}")
    print(f"  Expectancy: ${metrics.expectancy:.2f}")

    # 9. Show sample trades
    if result.trades:
        print(f"\nSample Trades (first 5):")
        for trade in result.trades[:5]:
            pnl_str = f"${trade.pnl:.2f}" if trade.pnl else "Open"
            print(f"  {trade.entry_time} | {trade.side.value.upper():5} | "
                  f"Entry: {trade.entry_price:.5f} | Exit: {trade.exit_price:.5f if trade.exit_price else 'N/A':>8} | "
                  f"PnL: {pnl_str}")

    print("\n" + "=" * 60)
    print("Backtest complete!")

    return result


if __name__ == "__main__":
    run_forex_backtest()
