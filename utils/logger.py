# utils/logger.py
"""
Sistema de logging centralizado para el bot de trading.

Proporciona:
- Logging estructurado con niveles configurables
- Rotación automática de archivos de log
- Formato consistente con timestamps
- Soporte para logging a consola y archivo
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# Directorio por defecto para logs
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = "trading.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

# Formato estándar para logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Cache de loggers ya configurados
_configured_loggers: dict[str, logging.Logger] = {}


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None,
    level: int = DEFAULT_LOG_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """
    Configura y devuelve un logger con las opciones especificadas.

    Args:
        name: Nombre del logger (típicamente __name__ del módulo).
        log_file: Nombre del archivo de log. Si es None, usa DEFAULT_LOG_FILE.
        log_dir: Directorio para los logs. Si es None, usa DEFAULT_LOG_DIR.
        level: Nivel de logging (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_bytes: Tamaño máximo del archivo antes de rotar.
        backup_count: Número de archivos de backup a mantener.
        console_output: Si True, también muestra logs en consola.
        file_output: Si True, guarda logs en archivo.

    Returns:
        Logger configurado.

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Trade ejecutado correctamente")
        >>> logger.error("Error al conectar con exchange", exc_info=True)
    """
    # Si el logger ya está configurado, devolverlo
    if name in _configured_loggers:
        return _configured_loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicar handlers si el logger ya existe
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Handler para archivo con rotación
    if file_output:
        log_dir = log_dir or DEFAULT_LOG_DIR
        log_file = log_file or DEFAULT_LOG_FILE

        # Crear directorio si no existe
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / log_file

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Handler para consola
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # No propagar a loggers padre
    logger.propagate = False

    # Cachear el logger
    _configured_loggers[name] = logger

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger existente o crea uno nuevo con configuración por defecto.

    Args:
        name: Nombre del logger.

    Returns:
        Logger configurado.
    """
    if name in _configured_loggers:
        return _configured_loggers[name]
    return setup_logger(name)


def set_global_level(level: int) -> None:
    """
    Cambia el nivel de logging para todos los loggers configurados.

    Args:
        level: Nuevo nivel de logging.
    """
    for logger in _configured_loggers.values():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


class TradeLogger:
    """
    Logger especializado para operaciones de trading.
    Proporciona métodos específicos para diferentes tipos de eventos de trading.
    """

    def __init__(self, name: str = "trading"):
        self.logger = setup_logger(
            name,
            log_file="trades.log",
            console_output=True,
            file_output=True,
        )

    def trade_opened(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        size: float,
        sl_price: float,
        tp_price: float,
    ) -> None:
        """Registra la apertura de una operación."""
        self.logger.info(
            f"TRADE OPENED | {symbol} | {direction.upper()} | "
            f"Entry: {entry_price:.8f} | Size: {size:.8f} | "
            f"SL: {sl_price:.8f} | TP: {tp_price:.8f}"
        )

    def trade_closed(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_pct: float,
        reason: str = "unknown",
    ) -> None:
        """Registra el cierre de una operación."""
        result = "WIN" if pnl > 0 else "LOSS"
        self.logger.info(
            f"TRADE CLOSED | {symbol} | {direction.upper()} | {result} | "
            f"Entry: {entry_price:.8f} | Exit: {exit_price:.8f} | "
            f"PnL: {pnl:.2f} ({pnl_pct:+.2f}%) | Reason: {reason}"
        )

    def signal_generated(
        self,
        strategy: str,
        symbol: str,
        signal: int,
        price: float,
    ) -> None:
        """Registra la generación de una señal."""
        signal_str = {1: "LONG", -1: "SHORT", 0: "NEUTRAL"}.get(signal, "UNKNOWN")
        self.logger.debug(
            f"SIGNAL | {strategy} | {symbol} | {signal_str} | Price: {price:.8f}"
        )

    def backtest_started(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        initial_capital: float,
    ) -> None:
        """Registra el inicio de un backtest."""
        self.logger.info(
            f"BACKTEST STARTED | {strategy} | {symbol} | {timeframe} | "
            f"Capital: {initial_capital:.2f}"
        )

    def backtest_completed(
        self,
        strategy: str,
        num_trades: int,
        total_return_pct: float,
        max_drawdown_pct: float,
        winrate_pct: float,
        profit_factor: float,
    ) -> None:
        """Registra la finalización de un backtest."""
        self.logger.info(
            f"BACKTEST COMPLETED | {strategy} | "
            f"Trades: {num_trades} | Return: {total_return_pct:+.2f}% | "
            f"MaxDD: {max_drawdown_pct:.2f}% | WinRate: {winrate_pct:.1f}% | "
            f"PF: {profit_factor:.2f}"
        )

    def optimization_progress(
        self,
        strategy: str,
        current: int,
        total: int,
        valid_results: int,
    ) -> None:
        """Registra el progreso de una optimización."""
        pct = current / total * 100.0 if total > 0 else 0
        self.logger.info(
            f"OPTIMIZATION | {strategy} | Progress: {current}/{total} ({pct:.1f}%) | "
            f"Valid: {valid_results}"
        )

    def error(self, message: str, exc_info: bool = False) -> None:
        """Registra un error."""
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message: str) -> None:
        """Registra una advertencia."""
        self.logger.warning(message)


# Instancia global del TradeLogger para uso conveniente
trade_logger = TradeLogger()
