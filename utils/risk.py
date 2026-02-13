from dataclasses import dataclass

@dataclass
class RiskManagementConfig:
    risk_pct: float = 0.01

def calculate_position_size_spot(capital: float, entry: float, stop_loss: float, risk_pct: float) -> float:
    risk_amount = capital * risk_pct
    price_diff = abs(entry - stop_loss)
    if price_diff == 0:
        return 0.0
    position = risk_amount / price_diff
    # Limitar al capital disponible
    max_position = capital / entry
    return min(position, max_position)
