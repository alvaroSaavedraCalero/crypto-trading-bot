#!/usr/bin/env python3
"""
Forex Historical Data Download Script

Downloads historical Forex data for offline backtesting.
Useful when you don't have reliable internet or want faster backtests.

Data sources:
1. FXCM free data API
2. Yahoo Finance (fallback)

For higher quality data, you can also manually download from:
- HistData.com: https://www.histdata.com/download-free-forex-data/
- Dukascopy: https://www.dukascopy.com/swiss/english/marketwatch/historical/
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.types import Symbol, Timeframe, MarketType
from src.adapters.data_sources import FXCMAdapter, CSVDataLoader


def download_forex_data():
    """Download historical data for common Forex pairs."""
    print("=" * 60)
    print("FOREX DATA DOWNLOADER")
    print("=" * 60)

    # Pairs to download
    pairs = [
        ("EUR", "USD"),
        ("GBP", "USD"),
        ("USD", "JPY"),
        ("AUD", "USD"),
        ("EUR", "GBP"),
    ]

    timeframes = ["15m", "1h", "4h", "1d"]

    output_dir = Path("./data/forex")
    output_dir.mkdir(parents=True, exist_ok=True)

    adapter = FXCMAdapter()

    for base, quote in pairs:
        symbol = Symbol(base, quote, MarketType.FOREX)
        print(f"\n{symbol}:")

        for tf_str in timeframes:
            timeframe = Timeframe.from_string(tf_str)
            filepath = output_dir / f"{base}{quote}_{tf_str}.csv"

            if filepath.exists():
                print(f"  {tf_str}: Already exists, skipping")
                continue

            print(f"  {tf_str}: Downloading...", end=" ")

            try:
                # Try to download
                saved_path = adapter.download_historical_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    years=3,
                    output_dir=str(output_dir)
                )
                print(f"OK -> {saved_path}")

            except Exception as e:
                print(f"Failed: {e}")

    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"Data saved to: {output_dir.absolute()}")
    print("\nTo use this data in backtests:")
    print('  adapter = DataSourceFactory.create_csv("./data/forex")')


def download_single_pair():
    """Download data for a specific pair interactively."""
    print("Enter the currency pair (e.g., EURUSD): ", end="")
    pair = input().strip().upper()

    if len(pair) != 6:
        print("Invalid pair format. Use 6 characters like EURUSD")
        return

    base, quote = pair[:3], pair[3:]
    symbol = Symbol(base, quote, MarketType.FOREX)

    print("Enter timeframe (1m, 5m, 15m, 1h, 4h, 1d): ", end="")
    tf_str = input().strip()

    print("Enter years of history (1-10): ", end="")
    years = int(input().strip())

    adapter = FXCMAdapter()

    print(f"\nDownloading {symbol} {tf_str} for {years} years...")

    try:
        filepath = adapter.download_historical_data(
            symbol=symbol,
            timeframe=Timeframe.from_string(tf_str),
            years=years,
            output_dir="./data/forex"
        )
        print(f"Success! Data saved to: {filepath}")

    except Exception as e:
        print(f"Download failed: {e}")
        print("\nAlternative: Download manually from HistData.com")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download Forex historical data")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Download a single pair interactively"
    )
    parser.add_argument(
        "--pair",
        type=str,
        help="Download specific pair (e.g., EURUSD)"
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="15m",
        help="Timeframe (default: 15m)"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="Years of history (default: 3)"
    )

    args = parser.parse_args()

    if args.interactive:
        download_single_pair()
    elif args.pair:
        symbol = Symbol(args.pair[:3], args.pair[3:], MarketType.FOREX)
        adapter = FXCMAdapter()

        print(f"Downloading {symbol} {args.timeframe} for {args.years} years...")
        filepath = adapter.download_historical_data(
            symbol=symbol,
            timeframe=Timeframe.from_string(args.timeframe),
            years=args.years,
            output_dir="./data/forex"
        )
        print(f"Saved to: {filepath}")
    else:
        download_forex_data()
