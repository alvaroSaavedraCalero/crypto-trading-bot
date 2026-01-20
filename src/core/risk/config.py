# src/core/risk/config.py
"""
Risk management configuration.
"""

from dataclasses import dataclass


@dataclass
class RiskConfig:
    """
    Risk management configuration.

    Attributes:
        risk_pct: Percentage of capital to risk per trade (0.01 = 1%)
        max_position_pct: Maximum position size as percentage of capital
        max_daily_loss_pct: Maximum daily loss before stopping trading
        max_open_positions: Maximum number of concurrent open positions
    """
    risk_pct: float = 0.01  # 1% risk per trade
    max_position_pct: float = 0.25  # Max 25% of capital per position
    max_daily_loss_pct: float = 0.05  # Stop after 5% daily loss
    max_open_positions: int = 3

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0 < self.risk_pct <= 0.1:
            raise ValueError("risk_pct must be between 0 and 0.1 (10%)")

        if not 0 < self.max_position_pct <= 1.0:
            raise ValueError("max_position_pct must be between 0 and 1.0")

        if not 0 < self.max_daily_loss_pct <= 0.5:
            raise ValueError("max_daily_loss_pct must be between 0 and 0.5")

        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be at least 1")
