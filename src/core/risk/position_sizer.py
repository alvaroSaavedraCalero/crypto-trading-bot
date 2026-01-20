# src/core/risk/position_sizer.py
"""
Position sizing calculations.
"""

from .config import RiskConfig


class PositionSizer:
    """
    Calculate position sizes based on risk parameters.
    """

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def calculate(
        self,
        capital: float,
        entry_price: float,
        stop_price: float
    ) -> float:
        """
        Calculate position size based on risk management rules.

        Uses the formula:
        position_size = (capital * risk_pct) / |entry_price - stop_price|

        This ensures that if the stop loss is hit, the loss equals
        risk_pct of the capital.

        Args:
            capital: Available capital
            entry_price: Planned entry price
            stop_price: Stop loss price

        Returns:
            Position size (in base currency units)
        """
        if capital <= 0:
            return 0.0

        if entry_price <= 0:
            return 0.0

        # Risk per trade in currency
        risk_amount = capital * self.config.risk_pct

        # Distance to stop loss
        risk_per_unit = abs(entry_price - stop_price)

        if risk_per_unit <= 0:
            return 0.0

        # Position size based on risk
        position_size = risk_amount / risk_per_unit

        # Apply maximum position constraint
        max_position_value = capital * self.config.max_position_pct
        max_position_size = max_position_value / entry_price

        return min(position_size, max_position_size)

    def calculate_with_leverage(
        self,
        capital: float,
        entry_price: float,
        stop_price: float,
        leverage: float = 1.0
    ) -> float:
        """
        Calculate position size with leverage.

        Args:
            capital: Available capital (margin)
            entry_price: Planned entry price
            stop_price: Stop loss price
            leverage: Leverage multiplier

        Returns:
            Position size accounting for leverage
        """
        if leverage <= 0:
            raise ValueError("Leverage must be positive")

        # Effective capital with leverage
        effective_capital = capital * leverage

        # Use standard calculation with effective capital
        # but still respect position limits based on actual capital
        base_size = self.calculate(
            capital=capital,
            entry_price=entry_price,
            stop_price=stop_price
        )

        # Scale by leverage
        leveraged_size = base_size * leverage

        # Ensure we don't exceed margin requirements
        max_leveraged_value = effective_capital * self.config.max_position_pct
        max_leveraged_size = max_leveraged_value / entry_price

        return min(leveraged_size, max_leveraged_size)

    def calculate_lot_size_forex(
        self,
        capital: float,
        entry_price: float,
        stop_price: float,
        pip_value: float = 10.0,  # Standard lot: $10 per pip
        leverage: float = 100.0
    ) -> float:
        """
        Calculate Forex lot size.

        Args:
            capital: Account balance
            entry_price: Entry price
            stop_price: Stop loss price
            pip_value: Value per pip for 1 standard lot
            leverage: Account leverage

        Returns:
            Lot size (1.0 = standard lot, 0.1 = mini, 0.01 = micro)
        """
        risk_amount = capital * self.config.risk_pct

        # Calculate pip distance
        pip_distance = abs(entry_price - stop_price) * 10000  # For most pairs

        if pip_distance <= 0:
            return 0.0

        # Risk per pip needed
        risk_per_pip = risk_amount / pip_distance

        # Convert to lots
        lot_size = risk_per_pip / pip_value

        # Cap based on available margin with leverage
        margin_required = entry_price * 100000 / leverage  # Per standard lot
        max_lots = (capital * 0.5) / margin_required  # Use max 50% margin

        return min(lot_size, max_lots)
