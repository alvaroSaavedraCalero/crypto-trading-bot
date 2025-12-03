
import unittest
import pandas as pd
import numpy as np
from backtesting.engine import Backtester, BacktestConfig, Trade
from utils.risk import RiskManagementConfig

class TestBacktester(unittest.TestCase):
    def setUp(self):
        self.risk_config = RiskManagementConfig(
            risk_pct=0.01
        )
        self.backtest_config = BacktestConfig(
            initial_capital=10000.0,
            sl_pct=0.01,
            tp_rr=2.0,
            fee_pct=0.0, # Simplify fees for testing
            allow_short=True
        )
        
        # Create dummy data
        dates = pd.date_range(start="2023-01-01", periods=10, freq="1min")
        self.df = pd.DataFrame({
            "timestamp": dates,
            "open": [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
            "high": [101, 102, 103, 104, 105, 104, 103, 102, 101, 100],
            "low":  [99, 100, 101, 102, 103, 102, 101, 100, 99, 98],
            "close": [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
            "volume": [1000] * 10,
            "signal": [0] * 10
        })

    def test_long_entry_exit_tp(self):
        # Signal LONG at index 1 (price 101)
        self.df.loc[1, "signal"] = 1
        # TP is 2% above 101 -> 103.02
        # Price reaches 104 at index 4, so it should hit TP
        
        bt = Backtester(self.backtest_config, self.risk_config)
        result = bt.run(self.df)
        
        self.assertEqual(result.num_trades, 1)
        trade = result.trades[0]
        self.assertEqual(trade.direction, "long")
        self.assertEqual(trade.entry_price, 101)
        self.assertAlmostEqual(trade.exit_price, 101 * 1.02) # TP hit
        self.assertGreater(trade.pnl, 0)

    def test_long_entry_exit_sl(self):
        # Signal LONG at index 1 (price 101)
        self.df.loc[1, "signal"] = 1
        # SL is 1% below 101 -> 99.99
        # Low at index 0 is 99, but we enter at index 1.
        # At index 8, low is 99, so it should hit SL.
        
        # Modify data to ensure SL hit later
        self.df.loc[2:7, "low"] = 100.5 # Stay above SL
        self.df.loc[2:8, "high"] = 101.5 # Stay below TP (103.02)
        self.df.loc[8, "low"] = 99.0 # Hit SL
        
        bt = Backtester(self.backtest_config, self.risk_config)
        result = bt.run(self.df)
        
        self.assertEqual(result.num_trades, 1)
        trade = result.trades[0]
        self.assertEqual(trade.direction, "long")
        self.assertAlmostEqual(trade.exit_price, 101 * 0.99) # SL hit
        self.assertLess(trade.pnl, 0)

    def test_short_entry_exit_tp(self):
        # Signal SHORT at index 4 (price 104)
        self.df.loc[4, "signal"] = -1
        # TP is 2% below 104 -> 101.92
        # Price drops to 99 at index 9
        
        bt = Backtester(self.backtest_config, self.risk_config)
        result = bt.run(self.df)
        
        self.assertEqual(result.num_trades, 1)
        trade = result.trades[0]
        self.assertEqual(trade.direction, "short")
        self.assertEqual(trade.entry_price, 104)
        self.assertAlmostEqual(trade.exit_price, 104 * (1 - 0.02)) # TP hit
        self.assertGreater(trade.pnl, 0)

if __name__ == "__main__":
    unittest.main()
