# CLAUDE.MD

Documentación para Claude Code sobre el proyecto Crypto Trading Bot.

## Descripción del Proyecto

Bot modular de trading y backtesting para estrategias cuantitativas en mercados cripto. Implementa múltiples estrategias de trading, motor de backtesting vectorizado, optimización de parámetros, validación cruzada y paper trading.

## Tecnologías Principales

- **Python 3.10+** (probado con 3.14)
- **CCXT**: Descarga de datos OHLCV de exchanges
- **Pandas/NumPy**: Procesamiento vectorizado de datos
- **TA-Lib/pandas-ta**: Indicadores técnicos
- **scikit-learn**: Estrategias con ML (AI Strategy)

## Estructura del Proyecto

```
crypto-trading-bot/
├── backtesting/          # Motor de backtesting vectorizado
│   └── engine.py         # BacktestEngine principal
├── config/
│   └── settings.py       # Configuraciones de estrategias (OPTIMIZED_STRATEGIES)
├── data/
│   ├── downloader.py     # Descarga datos OHLCV vía CCXT
│   ├── downloadedData/   # Caché local de datos históricos (CSV)
│   └── yfinance_downloader.py
├── execution/
│   ├── models.py         # Position, Trade, OrderSide
│   └── paper_broker.py   # PaperBroker para paper trading
├── optimization/         # Scripts de optimización por estrategia
│   ├── base_optimizer.py
│   ├── generic_optimizer.py
│   ├── optimize_bollinger.py
│   ├── optimize_keltner.py
│   ├── optimize_macd_adx.py
│   ├── optimize_ma_rsi.py
│   ├── optimize_squeeze.py
│   └── optimize_supertrend.py
├── reporting/
│   └── summary.py        # Generación de reportes y comparativas
├── scripts/
│   ├── backtest_2025.py       # Backtest YTD 2025 todas las estrategias
│   ├── backtest_strategies.py # Backtest con configs optimizadas
│   └── paper_runner.py        # Paper trading de una estrategia
├── strategies/           # Implementación de estrategias
│   ├── base.py          # BaseStrategy (clase abstracta)
│   ├── registry.py      # create_strategy() - factory pattern
│   ├── ma_rsi_strategy.py
│   ├── macd_adx_trend_strategy.py
│   ├── supertrend_strategy.py
│   ├── keltner_breakout_strategy.py
│   ├── bollinger_mean_reversion.py
│   ├── squeeze_momentum_strategy.py
│   └── ai_strategy.py   # ML-based strategy (RandomForest, GradientBoosting)
├── tests/               # Tests con pytest
│   ├── conftest.py
│   ├── test_all_strategies.py
│   ├── test_backtester.py
│   ├── test_engine.py
│   └── test_strategies.py
├── utils/
│   ├── atr.py          # Cálculo ATR
│   ├── risk.py         # Gestión de riesgo
│   ├── logger.py       # Logging configurado
│   └── validation.py   # Validación cruzada
├── validation/         # Scripts de validación por estrategia
└── visualization/
    ├── chart.py
    └── interactive_chart.py
```

## Conceptos Clave

### 1. Estrategias (strategies/)

Todas las estrategias heredan de `BaseStrategy` y deben implementar:
- `generate_signals(df: pd.DataFrame) -> pd.DataFrame`: Genera señales (1=long, -1=short, 0=neutral)
- Parámetros configurables pasados en `__init__`

**Estrategias disponibles:**
- `ma_rsi`: Moving Average + RSI
- `macd_adx`: MACD + ADX
- `supertrend`: Supertrend indicator
- `keltner`: Keltner Channel Breakout
- `bollinger`: Bollinger Bands Mean Reversion
- `squeeze`: Squeeze Momentum (Bollinger + Keltner)
- `ai_rf`: AI con Random Forest
- `ai_gb`: AI con Gradient Boosting

### 2. Configuración (config/settings.py)

`OPTIMIZED_STRATEGIES`: Lista de `StrategyRunConfig` con:
- `strategy_name`: Nombre de la estrategia
- `symbol`: Par de trading (ej: "BTC/USDT")
- `timeframe`: Velas (ej: "1h", "15m")
- `params`: Diccionario con parámetros de la estrategia
- `risk_config`: RiskConfig con SL/TP (porcentual o ATR)

### 3. Backtesting (backtesting/engine.py)

`BacktestEngine` ejecuta backtests vectorizados:
- Gestión de posiciones long/short
- Stop Loss y Take Profit (porcentual o basado en ATR)
- Métricas: retorno total, drawdown máximo, win rate, profit factor, Sharpe ratio

### 4. Optimización (optimization/)

Scripts que usan grid search o Bayesian optimization para encontrar mejores parámetros:
- Genera archivos `opt_*.csv` con resultados
- Usa validación cruzada (walk-forward o rolling window)
- Selecciona mejores configs por múltiples métricas

### 5. Paper Trading (scripts/paper_runner.py)

Simula trading en tiempo real con `PaperBroker`:
- Usa datos históricos con delay simulado
- Gestiona posiciones, órdenes y balance
- Útil para validar estrategias antes de trading real

## Comandos Comunes

### Setup inicial
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### Ejecutar backtests
```bash
# Todas las estrategias optimizadas
PYTHONPATH=$(pwd):$PYTHONPATH python scripts/backtest_strategies.py

# Backtest YTD 2025
PYTHONPATH=$(pwd):$PYTHONPATH python scripts/backtest_2025.py
```

### Optimizar estrategias
```bash
# Optimizar una estrategia específica
PYTHONPATH=$(pwd):$PYTHONPATH python optimization/optimize_bollinger.py

# Ejecutar todos los optimizadores
PYTHONPATH=$(pwd):$PYTHONPATH python run_all_optimizers.py
```

### Paper trading
```bash
# Editar RUN_CONFIG en paper_runner.py primero
PYTHONPATH=$(pwd):$PYTHONPATH python scripts/paper_runner.py
```

### Tests
```bash
# Ejecutar todos los tests
pytest tests/

# Test específico con coverage
pytest tests/test_all_strategies.py -v --cov=strategies
```

### Pre-commit hooks
```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

## Patrones de Código

### Crear nueva estrategia

1. Crear archivo en `strategies/mi_estrategia.py`:
```python
from strategies.base import BaseStrategy
import pandas as pd

class MiEstrategia(BaseStrategy):
    def __init__(self, param1: int = 10, param2: float = 0.5, **kwargs):
        super().__init__(**kwargs)
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Calcular indicadores
        # ...
        # Generar señales
        df['signal'] = 0
        # Lógica de señales
        return df
```

2. Registrar en `strategies/registry.py`:
```python
def create_strategy(strategy_name: str, params: Dict[str, Any]) -> BaseStrategy:
    if strategy_name == "mi_estrategia":
        return MiEstrategia(**params)
    # ...
```

3. Agregar a `config/settings.py`:
```python
StrategyRunConfig(
    strategy_name="mi_estrategia",
    symbol="BTC/USDT",
    timeframe="1h",
    params={"param1": 10, "param2": 0.5},
    risk_config=RiskConfig(...)
)
```

### Crear optimizador para estrategia

1. Crear `optimization/optimize_mi_estrategia.py`:
```python
from optimization.generic_optimizer import GenericOptimizer

# Definir espacio de búsqueda
param_space = {
    'param1': [10, 20, 30],
    'param2': [0.3, 0.5, 0.7]
}

optimizer = GenericOptimizer(
    strategy_name="mi_estrategia",
    symbol="BTC/USDT",
    timeframe="1h",
    param_space=param_space
)

results = optimizer.optimize(output_csv="optimization/opt_mi_estrategia.csv")
```

## Datos

### Caché de datos
- Datos históricos en `data/downloadedData/` como CSV
- Formato: `{exchange}_{symbol}_{timeframe}.csv`
- Se descargan automáticamente si no existen

### Descargar datos manualmente
```python
from data.downloader import download_data

df = download_data(
    symbol="BTC/USDT",
    timeframe="1h",
    days_back=365,
    exchange_name="binance"
)
```

## Métricas de Backtesting

- **Total Return**: Retorno porcentual total
- **Max Drawdown**: Máxima caída desde pico
- **Win Rate**: Porcentaje de trades ganadores
- **Profit Factor**: Ganancia bruta / Pérdida bruta
- **Sharpe Ratio**: Retorno ajustado por riesgo
- **Total Trades**: Número de trades ejecutados

## Convenciones

### Naming
- Archivos: `snake_case.py`
- Clases: `PascalCase`
- Funciones/variables: `snake_case`
- Constantes: `UPPER_CASE`

### Signals
- `1`: Señal de compra (LONG)
- `-1`: Señal de venta (SHORT)
- `0`: Sin señal (neutral)

### Timeframes
- Formato CCXT: "1m", "5m", "15m", "1h", "4h", "1d"

### Risk Management
- Stop Loss: porcentual (`sl_pct`) o ATR-based (`sl_atr_mult`)
- Take Profit: porcentual (`tp_pct`) o ATR-based (`tp_atr_mult`)
- Configurado en `RiskConfig` dentro de `StrategyRunConfig`

## Tips para Desarrollo

### Debugging backtests
- Usar `utils/logger.py` para logging consistente
- Inspeccionar `df` después de `generate_signals()`
- Verificar que señales no sean NaN/inf

### Optimización de rendimiento
- Backtesting es vectorizado (evitar loops)
- Caché de datos reduce tiempo de descarga
- Usar `head_limit` en optimizadores para pruebas rápidas

### Validación
- Siempre validar con datos out-of-sample
- Usar validación cruzada (walk-forward)
- Scripts en `validation/` para cada estrategia

### Testing
- Tests en `tests/` usan pytest
- `conftest.py` tiene fixtures comunes
- Usar `test_all_strategies.py` para validar todas las estrategias

## Archivos de Documentación

- **README.md**: Overview del proyecto
- **OPTIMIZATION_RESULTS.md**: Resultados de optimizaciones
- **STRATEGY_ANALYSIS.md**: Análisis de estrategias
- **IMPROVEMENTS_SUMMARY.md**: Mejoras implementadas
- **BRANCH_CLEANUP_GUIDE.md**: Guía de limpieza de ramas
- **FUNCTIONALITY_TEST_REPORT.md**: Reporte de tests funcionales

## Git Workflow

- Branch principal: `main`
- Branches de desarrollo: `claude/*`
- Pre-commit hooks activos (black, flake8, mypy)
- Commits descriptivos con prefijo: `feat:`, `fix:`, `docs:`, `refactor:`

## Recursos Externos

- [CCXT Documentation](https://docs.ccxt.com/)
- [TA-Lib Indicators](https://mrjbq7.github.io/ta-lib/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Backtesting Best Practices](https://www.quantstart.com/articles/Successful-Backtesting-of-Algorithmic-Trading-Strategies-Part-I/)

## Notas Importantes

1. **No hacer trading real**: Este bot es para backtesting y paper trading. Trading real requiere manejo de API keys, gestión de errores robusta y más validación.

2. **Riesgo de overfitting**: Las optimizaciones pueden sobreajustar. Siempre validar con datos out-of-sample.

3. **Datos históricos**: Performance pasado no garantiza resultados futuros.

4. **PYTHONPATH**: Siempre configurar `PYTHONPATH=$(pwd):$PYTHONPATH` antes de ejecutar scripts.

5. **Dependencias**: Si hay errores de import, verificar que todas las dependencias estén instaladas con `pip install -r requirements.txt`.

---

*Este documento está diseñado para ayudar a Claude Code a entender y trabajar con este proyecto de manera eficiente.*
