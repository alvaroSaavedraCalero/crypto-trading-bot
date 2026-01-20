# src/core/strategies/registry.py
"""
Strategy registry for dynamic strategy instantiation.
"""

from __future__ import annotations

from typing import Dict, Type, Optional, Any, Callable
from functools import wraps

from .base import BaseStrategy, StrategyConfig


# Global registry
_STRATEGY_REGISTRY: Dict[str, tuple[Type[BaseStrategy], Type[StrategyConfig]]] = {}


def register_strategy(
    name: str,
    config_class: Type[StrategyConfig]
) -> Callable[[Type[BaseStrategy]], Type[BaseStrategy]]:
    """
    Decorator to register a strategy class.

    Usage:
        @register_strategy("MA_RSI", MovingAverageRSIConfig)
        class MovingAverageRSIStrategy(BaseStrategy):
            ...
    """
    def decorator(strategy_class: Type[BaseStrategy]) -> Type[BaseStrategy]:
        _STRATEGY_REGISTRY[name.upper()] = (strategy_class, config_class)
        return strategy_class
    return decorator


class StrategyRegistry:
    """
    Factory for creating strategy instances.
    """

    @staticmethod
    def get_available_strategies() -> list[str]:
        """Return list of registered strategy names."""
        return list(_STRATEGY_REGISTRY.keys())

    @staticmethod
    def is_registered(name: str) -> bool:
        """Check if strategy is registered."""
        return name.upper() in _STRATEGY_REGISTRY

    @staticmethod
    def create(
        name: str,
        config: Optional[StrategyConfig] = None,
        **config_kwargs: Any
    ) -> BaseStrategy:
        """
        Create a strategy instance by name.

        Args:
            name: Strategy name (case-insensitive)
            config: Optional pre-created config object
            **config_kwargs: Config parameters if config not provided

        Returns:
            Strategy instance

        Raises:
            ValueError: If strategy not found
        """
        name_upper = name.upper()

        if name_upper not in _STRATEGY_REGISTRY:
            available = ", ".join(_STRATEGY_REGISTRY.keys())
            raise ValueError(
                f"Strategy '{name}' not found. Available: {available}"
            )

        strategy_class, config_class = _STRATEGY_REGISTRY[name_upper]

        if config is None:
            config = config_class(**config_kwargs)

        return strategy_class(config)

    @staticmethod
    def get_config_class(name: str) -> Type[StrategyConfig]:
        """Get the config class for a strategy."""
        name_upper = name.upper()

        if name_upper not in _STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{name}' not found")

        return _STRATEGY_REGISTRY[name_upper][1]

    @staticmethod
    def get_strategy_class(name: str) -> Type[BaseStrategy]:
        """Get the strategy class by name."""
        name_upper = name.upper()

        if name_upper not in _STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{name}' not found")

        return _STRATEGY_REGISTRY[name_upper][0]
