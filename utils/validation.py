class ValidationError(Exception):
    pass

def validate_window_size(window: int, name: str, min_window: int = 2, max_window: int = 1000):
    if not isinstance(window, int):
        raise ValidationError(f"{name} debe ser entero")
    if window < min_window or window > max_window:
        raise ValidationError(f"{name} debe estar entre {min_window} y {max_window}")

def validate_rsi_levels(oversold: float, overbought: float):
    if not (0 < oversold < overbought < 100):
        raise ValidationError("Niveles RSI inválidos")

def validate_ma_windows(fast: int, slow: int):
    if fast >= slow:
        raise ValidationError("Fast MA debe ser menor que Slow MA")

def validate_multiplier(value: float, name: str, min_val: float = 0.1, max_val: float = 10.0):
    if not (min_val <= value <= max_val):
        raise ValidationError(f"{name} debe estar entre {min_val} y {max_val}")

def validate_ratio(value: float, name: str, min_val: float = 0.0, max_val: float = 1.0):
    if not (min_val <= value <= max_val):
        raise ValidationError(f"{name} debe estar entre {min_val} y {max_val}")

def validate_range(value: float, min_val: float, max_val: float, name: str):
    if not (min_val <= value <= max_val):
        raise ValidationError(f"{name} debe estar entre {min_val} y {max_val}")

def validate_positive(value: float, name: str):
    if value <= 0:
        raise ValidationError(f"{name} debe ser positivo")
