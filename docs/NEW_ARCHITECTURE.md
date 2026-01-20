# Trading Bot - Nueva Arquitectura v2.0

## Estructura del Proyecto

El proyecto ha sido reorganizado siguiendo una arquitectura por **capas técnicas**, separando claramente las responsabilidades:

```
crypto-trading-bot/
├── src/                           # Código fuente principal
│   ├── core/                      # Lógica de dominio (sin dependencias externas)
│   │   ├── types.py              # Tipos centrales (Symbol, Timeframe, Trade, etc.)
│   │   ├── strategies/           # Estrategias de trading
│   │   │   ├── base.py          # Clase base BaseStrategy
│   │   │   ├── registry.py      # Registry para crear estrategias dinámicamente
│   │   │   └── implementations/ # Implementaciones concretas
│   │   ├── backtesting/         # Motor de backtesting
│   │   │   ├── engine.py        # Backtester principal
│   │   │   └── metrics.py       # Cálculo de métricas
│   │   ├── optimization/        # Optimización y walk-forward
│   │   │   ├── optimizer.py     # Base optimizer
│   │   │   ├── grid_search.py   # Grid search con multiprocessing
│   │   │   └── walk_forward.py  # Walk-forward analysis
│   │   └── risk/                # Gestión de riesgo
│   │       ├── config.py        # Configuración de riesgo
│   │       └── position_sizer.py # Cálculo de tamaño de posición
│   │
│   ├── adapters/                 # Integraciones externas
│   │   └── data_sources/        # Fuentes de datos
│   │       ├── base.py          # Interfaz base
│   │       ├── fxcm.py          # Adaptador FXCM (Forex)
│   │       ├── binance.py       # Adaptador Binance (Crypto)
│   │       ├── csv_loader.py    # Carga de CSV offline
│   │       └── factory.py       # Factory para crear adaptadores
│   │
│   ├── services/                 # Servicios de aplicación
│   │   ├── paper_trading/       # Paper trading
│   │   └── live_trading/        # Trading en vivo
│   │
│   └── interfaces/              # Interfaces de usuario
│       ├── cli/                 # Línea de comandos
│       └── api/                 # API REST (futuro)
│
├── examples/                     # Ejemplos de uso
│   ├── forex_backtest.py        # Backtesting de Forex
│   ├── forex_optimization.py    # Optimización con walk-forward
│   └── download_forex_data.py   # Descarga de datos históricos
│
├── tests/                        # Tests
│   └── test_new_architecture.py # Tests de la nueva arquitectura
│
├── strategies/                   # [LEGACY] Estrategias antiguas
├── backtesting/                  # [LEGACY] Motor antiguo
├── optimization/                 # [LEGACY] Optimizadores antiguos
└── config/                       # [LEGACY] Configuraciones antiguas
```

## Uso Rápido

### 1. Backtesting de Forex

```python
from src.core.types import Symbol, Timeframe, MarketType
from src.core.backtesting import Backtester, BacktestConfig
from src.core.risk import RiskConfig
from src.core.strategies.implementations.supertrend import SupertrendStrategy, SupertrendConfig
from src.adapters.data_sources import DataSourceFactory

# Crear símbolo y timeframe
symbol = Symbol("EUR", "USD", MarketType.FOREX)
timeframe = Timeframe.from_string("15m")

# Obtener datos
adapter = DataSourceFactory.create_forex()
df = adapter.fetch_ohlcv(symbol, timeframe, limit=5000)

# Configurar y ejecutar estrategia
strategy = SupertrendStrategy(SupertrendConfig(
    atr_period=10,
    atr_multiplier=3.0,
    allow_short=True
))
df_signals = strategy.generate_signals(df)

# Ejecutar backtest
backtester = Backtester(
    BacktestConfig(initial_capital=10000, sl_pct=0.01, tp_rr=2.0),
    RiskConfig(risk_pct=0.01)
)
result = backtester.run(df_signals, symbol, timeframe)

# Ver resultados
print(f"Return: {result.metrics.total_return_pct:.2f}%")
print(f"Profit Factor: {result.metrics.profit_factor:.2f}")
```

### 2. Optimización de Parámetros

```python
from src.core.optimization import GridSearchOptimizer, OptimizationConfig

optimizer = GridSearchOptimizer(
    OptimizationConfig(optimize_metric="profit_factor", min_trades=20)
)

param_grid = {
    "bb_window": [15, 20, 25],
    "bb_std": [1.5, 2.0, 2.5],
    "rsi_oversold": [25.0, 30.0],
    "rsi_overbought": [70.0, 75.0],
}

result = optimizer.optimize(
    df=df,
    strategy_class=BollingerMRStrategy,
    backtest_config=backtest_config,
    param_grid=param_grid
)

print(f"Best params: {result.best_params}")
print(f"Best PF: {result.best_metrics.profit_factor}")
```

### 3. Walk-Forward Analysis

```python
from src.core.optimization import WalkForwardAnalyzer, WalkForwardConfig

analyzer = WalkForwardAnalyzer(
    WalkForwardConfig(n_splits=5, train_pct=0.8),
    OptimizationConfig(optimize_metric="profit_factor")
)

wf_result = analyzer.analyze(
    df=df,
    strategy_class=BollingerMRStrategy,
    backtest_config=backtest_config,
    param_grid=param_grid
)

print(wf_result.summary())
```

## Características Principales

### Motor de Backtesting Avanzado

- **Métricas completas**: Return, Profit Factor, Sharpe, Sortino, Calmar, Max Drawdown, etc.
- **Slippage realista**: Simulación de deslizamiento de precios
- **Comisiones/Spread**: Soporte para fees de crypto y spreads de forex
- **SL/TP dinámico**: Basado en porcentaje fijo o ATR

### Optimización

- **Grid Search paralelo**: Usa todos los cores del CPU
- **Train/Validation split**: Detecta overfitting
- **Walk-Forward Analysis**: Validación robusta con múltiples ventanas
- **Estabilidad de parámetros**: Análisis de variabilidad de params óptimos

### Fuentes de Datos Forex (sin OANDA)

1. **FXCM API gratuita**: Datos históricos sin cuenta
2. **Yahoo Finance**: Fallback automático
3. **CSV offline**: HistData.com, Dukascopy

### Multiplataforma

- ✅ Windows
- ✅ Linux
- ✅ macOS
- ✅ Disponible en Europa (sin restricciones de OANDA)

## Estrategias Incluidas

| Estrategia | Tipo | Mercados | Descripción |
|------------|------|----------|-------------|
| Supertrend | Trend-following | Crypto, Forex | Sigue tendencias con ATR |
| Bollinger MR | Mean-reversion | Crypto, Forex | RSI + Bollinger para reversión |
| Keltner | Breakout | Crypto, Forex | Rupturas de canal Keltner |
| MA + RSI | Trend-following | Crypto, Forex | Cruces de medias con filtro RSI |

## Migración desde v1.0

El código legacy en las carpetas `strategies/`, `backtesting/`, `optimization/` sigue funcionando.
Para migrar gradualmente:

1. Las nuevas estrategias están en `src/core/strategies/implementations/`
2. Usa `DataSourceFactory` en lugar de los downloaders antiguos
3. El nuevo `Backtester` en `src/core/backtesting/` tiene más métricas

## Próximos Pasos

- [ ] Migrar todas las estrategias legacy
- [ ] Añadir interfaz CLI mejorada
- [ ] Dashboard web con FastAPI
- [ ] Soporte para live trading
