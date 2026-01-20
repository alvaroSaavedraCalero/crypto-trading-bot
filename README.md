# 🤖 Crypto Trading Bot

[![Tests](https://img.shields.io/badge/tests-115%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Bot de trading algorítmico modular y optimizado para criptomonedas. Incluye motor de backtesting, optimización de estrategias, análisis exhaustivo y configuraciones listas para producción.

## 🎯 Características Principales

- **Estrategias Optimizadas**: 4 estrategias con parámetros optimizados mediante 7000+ configuraciones
- **Backtesting Robusto**: Motor vectorizado con gestión de riesgo, SL/TP y métricas avanzadas
- **Optimización Automática**: Framework completo para optimización multi-parámetro con paralelización
- **Testing Comprehensivo**: 115 tests automatizados con 100% de éxito
- **Análisis Detallado**: Documentación completa de rendimiento y recomendaciones
- **Múltiples Pares**: Configuraciones específicas para BTC/USDT, ETH/USDT, BNB/USDT

## 📊 Resultados de Optimización

### Estrategias Listas para Producción

| Estrategia | Par | Profit Factor | Retorno | Winrate | Trades | Mejora |
|------------|-----|---------------|---------|---------|--------|--------|
| **KELTNER** | BTC/USDT | **2.01** | **+27.29%** | 40.9% | 44 | +89.6% |
| **BOLLINGER_MR** | BTC/USDT | **2.23** | **+18.17%** | 48.1% | 27 | +137.2% |
| **BOLLINGER_MR** | ETH/USDT | **1.43** | **+10.40%** | 37.5% | 32 | - |
| **BOLLINGER_MR** | BNB/USDT | **1.40** | **+8.02%** | 50.0% | 30 | - |

> **Nota**: Resultados basados en optimización de 10,000 velas (15m timeframe). Ver [OPTIMIZATION_RESULTS.md](OPTIMIZATION_RESULTS.md) para detalles completos.

### Mejoras Logradas

- ✅ **KELTNER**: De -2.97% → +27.29% (+30.26 puntos)
- ✅ **BOLLINGER_MR**: De -8.99% → +18.17% (+27.16 puntos)
- ✅ **Tests**: De 107/115 → 115/115 (100% pasando)
- ✅ **Documentación**: +600 líneas de análisis y guías

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/alvaroSaavedraCalero/crypto-trading-bot.git
cd crypto-trading-bot

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar dependencias de desarrollo (opcional)
pip install -r requirements-dev.txt

# Configurar PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### Verificar Instalación

```bash
# Ejecutar tests
pytest tests/ -v

# Evaluación rápida de estrategias
python quick_strategy_test.py
```

## 📖 Uso

### 1. Evaluación Rápida de Estrategias

Prueba todas las estrategias con configuraciones actuales:

```bash
python quick_strategy_test.py
```

**Salida**: Tabla comparativa con rendimiento de cada estrategia en BTC, ETH, BNB.

### 2. Backtest de Estrategias Optimizadas

Ejecuta backtest con las mejores configuraciones:

```bash
python scripts/backtest_strategies.py
```

**Incluye**:
- KELTNER BTC/USDT (PF 2.01)
- BOLLINGER_MR BTC/ETH/BNB (PF 2.23, 1.43, 1.40)

### 3. Optimización de Estrategias

#### Optimización Focalizada (Recomendado)

Optimiza solo las estrategias más prometedoras:

```bash
python optimize_best_strategies.py
```

**Optimiza**:
- KELTNER para BTC/USDT (3600 combinaciones)
- BOLLINGER_MR para BTC/ETH/BNB (5000+ combinaciones)

**Resultados**: Archivos CSV con mejores parámetros.

#### Optimización Comprehensiva

Pipeline completo para múltiples estrategias:

```bash
python comprehensive_optimization.py
```

**Incluye**:
- Optimización de todas las estrategias
- Validación cruzada entre pares
- Generación de reporte HTML automático

### 4. Paper Trading

Ejecuta una estrategia en tiempo real (simulado):

```bash
# Editar RUN_CONFIG en scripts/paper_runner.py
python scripts/paper_runner.py
```

### 5. Backtesting Avanzado

#### Backtest de 2025 (Year-to-Date)

```bash
python scripts/backtest_2025.py
```

#### Backtest Personalizado

```python
from backtesting.engine import Backtester, BacktestConfig
from strategies.registry import create_strategy
from data.downloader import get_datos_cripto_cached
from config.settings import KELTNER_BTC15M_OPT_CONFIG, KELTNER_BTC15M_OPT_BT_CONFIG

# Descargar datos
df = get_datos_cripto_cached("BTC/USDT", "15m", 5000)

# Crear estrategia
strategy = create_strategy("KELTNER", KELTNER_BTC15M_OPT_CONFIG)
df_signals = strategy.generate_signals(df)

# Ejecutar backtest
backtester = Backtester(
    backtest_config=KELTNER_BTC15M_OPT_BT_CONFIG,
    risk_config=RISK_CONFIG
)
result = backtester.run(df_signals)

print(f"Return: {result.total_return_pct:.2f}%")
print(f"Winrate: {result.winrate_pct:.2f}%")
print(f"Profit Factor: {result.profit_factor:.2f}")
```

## 📁 Estructura del Proyecto

```
crypto-trading-bot/
├── backtesting/           # Motor de backtesting
│   └── engine.py         # Backtester principal
├── config/               # Configuraciones
│   └── settings.py       # ⭐ Configuraciones optimizadas
├── data/                 # Gestión de datos
│   ├── downloader.py     # Descarga de OHLCV vía CCXT
│   └── downloadedData/   # Cache local de datos
├── optimization/         # Scripts de optimización
│   ├── generic_optimizer.py      # Optimizador genérico
│   ├── optimize_bollinger.py     # Optimización específica
│   └── optimize_*.py             # Otros optimizadores
├── strategies/           # Implementación de estrategias
│   ├── registry.py       # Registro de estrategias
│   ├── base.py          # Clase base
│   ├── ma_rsi_strategy.py
│   ├── supertrend_strategy.py
│   ├── bollinger_mean_reversion.py
│   ├── keltner_breakout_strategy.py
│   ├── macd_adx_trend_strategy.py
│   ├── squeeze_momentum_strategy.py
│   ├── smart_money_strategy.py
│   ├── ict_strategy.py
│   └── ai_strategy.py
├── tests/                # Suite de tests
│   ├── conftest.py       # Fixtures
│   ├── test_*.py         # Tests por módulo
│   └── 115 tests pasando ✅
├── utils/                # Utilidades
│   ├── risk.py          # Gestión de riesgo
│   ├── validation.py    # Validaciones
│   └── logger.py        # Logging
├── scripts/              # Scripts de ejecución
│   ├── backtest_strategies.py    # Backtest todas
│   ├── backtest_2025.py          # Backtest YTD
│   └── paper_runner.py           # Paper trading
├── reporting/            # Generación de reportes
│   └── summary.py       # Resumen de resultados
├── visualization/        # Gráficos y dashboards
│   └── charts.py        # Generación de gráficos
│
├── 🆕 Scripts de Análisis y Optimización
├── quick_strategy_test.py           # ⭐ Evaluación rápida
├── optimize_best_strategies.py      # ⭐ Optimización focalizada
├── comprehensive_optimization.py    # Pipeline completo
│
├── 📚 Documentación
├── README.md                        # Este archivo
├── STRATEGY_ANALYSIS.md             # ⭐ Análisis detallado
├── OPTIMIZATION_RESULTS.md          # ⭐ Resultados de optimización
├── IMPROVEMENTS_SUMMARY.md          # ⭐ Resumen de mejoras
├── BRANCH_CLEANUP_GUIDE.md          # Guía de limpieza de ramas
│
└── 📊 Archivos de Configuración
    ├── pyproject.toml              # Configuración del proyecto
    ├── requirements.txt            # Dependencias
    ├── requirements-dev.txt        # Dependencias de desarrollo
    └── .pre-commit-config.yaml     # Hooks de pre-commit
```

## 🎪 Estrategias Disponibles

### Estrategias Optimizadas (Listas para Producción)

#### 1. KELTNER Breakout (BTC/USDT) 🏆
**Mejor Estrategia General**

```python
# En config/settings.py
KELTNER_BTC15M_OPT_CONFIG
```

- **Profit Factor**: 2.01
- **Retorno**: +27.29%
- **Winrate**: 40.9%
- **Uso**: Breakouts en mercados trending
- **Parámetros Clave**: `kc_window=40, kc_mult=2.0, sl=0.015, tp_rr=3.0`

#### 2. Bollinger Mean Reversion (BTC/USDT) 🥇
**Mejor Mean Reversion**

```python
BOLLINGER_MR_BTC15M_OPT_CONFIG
```

- **Profit Factor**: 2.23
- **Retorno**: +18.17%
- **Winrate**: 48.1%
- **Uso**: Reversiones en sobrecompra/sobreventa
- **Parámetros Clave**: `bb_window=25, rsi_oversold=15.0, sl=0.01, tp_rr=2.5`

#### 3. Bollinger Mean Reversion (ETH/USDT)

```python
BOLLINGER_MR_ETH15M_OPT_CONFIG
```

- **Profit Factor**: 1.43
- **Retorno**: +10.40%
- **Parámetros**: Optimizados específicamente para ETH

#### 4. Bollinger Mean Reversion (BNB/USDT)

```python
BOLLINGER_MR_BNB15M_OPT_CONFIG
```

- **Profit Factor**: 1.40
- **Retorno**: +8.02%
- **Winrate**: 50.0%

### Estrategias Legacy (No Optimizadas)

Disponibles pero requieren optimización antes de uso en producción:

- **MA + RSI**: Cruce de medias móviles con filtro RSI
- **MACD + ADX**: Momentum con filtro de tendencia
- **Supertrend**: Seguimiento de tendencia con ATR
- **Squeeze Momentum**: Detección de compresión de volatilidad
- **Smart Money / ICT**: Conceptos institucionales
- **AI Strategy**: Gradient Boosting para predicción

Ver [STRATEGY_ANALYSIS.md](STRATEGY_ANALYSIS.md) para análisis detallado y recomendaciones.

## 🔧 Configuración

### Configuraciones Principales

Todas las configuraciones están en `config/settings.py`:

```python
# Configuración de riesgo
RISK_CONFIG = RiskManagementConfig(
    risk_pct=0.01,  # 1% de capital por trade
)

# Configuración de backtest
BACKTEST_CONFIG = BacktestConfig(
    initial_capital=1000.0,
    sl_pct=0.015,
    tp_rr=3.0,
    fee_pct=0.0005,
    allow_short=True,
)

# Lista de estrategias a ejecutar
OPTIMIZED_STRATEGIES = [
    KELTNER_BTC15M_OPT_RUN,
    BOLLINGER_MR_BTC15M_OPT_RUN,
    BOLLINGER_MR_ETH15M_OPT_RUN,
    BOLLINGER_MR_BNB15M_OPT_RUN,
    # ... más estrategias
]
```

### Personalización

1. **Agregar nuevo par**:
   ```python
   KELTNER_SOL15M_CONFIG = KeltnerBreakoutStrategyConfig(
       kc_window=40,
       kc_mult=2.0,
       # ... más parámetros
   )
   ```

2. **Modificar gestión de riesgo**:
   ```python
   RISK_CONFIG = RiskManagementConfig(
       risk_pct=0.02,  # 2% por trade
   )
   ```

3. **Cambiar SL/TP**:
   ```python
   BACKTEST_CONFIG = BacktestConfig(
       sl_pct=0.02,    # 2% stop loss
       tp_rr=2.5,      # Take profit 1:2.5
   )
   ```

## 📚 Documentación Detallada

### Guías Principales

- **[STRATEGY_ANALYSIS.md](STRATEGY_ANALYSIS.md)**: Análisis completo de todas las estrategias
  - Performance breakdown por estrategia y par
  - Recomendaciones específicas de mejora
  - Plan de acción en 4 fases
  - Mejoras generales (filtros, gestión de riesgo, ensemble)

- **[OPTIMIZATION_RESULTS.md](OPTIMIZATION_RESULTS.md)**: Resultados de optimización
  - Parámetros óptimos encontrados
  - Comparación baseline vs optimizado
  - Top 5 configuraciones por estrategia
  - Recomendaciones de implementación

- **[IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)**: Resumen ejecutivo
  - Bugs corregidos
  - Métricas de impacto
  - Estado de optimizaciones
  - Próximos pasos

- **[BRANCH_CLEANUP_GUIDE.md](BRANCH_CLEANUP_GUIDE.md)**: Guía de gestión de ramas

### Análisis por Estrategia

Cada estrategia incluye:
- ✅ Fortalezas y debilidades
- ✅ Recomendaciones de mejora
- ✅ Parámetros óptimos
- ✅ Condiciones de mercado ideales
- ✅ Prioridad de optimización

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_strategies.py -v
pytest tests/test_backtester.py -v

# Con cobertura
pytest tests/ --cov=. --cov-report=html
```

### Estado de Tests

- ✅ **115/115 tests pasando**
- ✅ Cobertura de estrategias
- ✅ Cobertura de backtesting
- ✅ Cobertura de validaciones
- ✅ Cobertura de optimización

## 📊 Datos

### Fuente de Datos

- **Exchange**: Binance vía CCXT
- **Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d
- **Pares**: BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, etc.

### Cache Local

Los datos se cachean en `data/downloadedData/`:

```
data/downloadedData/
├── BTCUSDT_15m.csv
├── ETHUSDT_15m.csv
├── BNBUSDT_15m.csv
└── ...
```

### Actualizar Datos

```python
from data.downloader import get_datos_cripto_cached

# Forzar descarga nueva
df = get_datos_cripto_cached(
    symbol="BTC/USDT",
    timeframe="15m",
    limit=10000,
    force_download=True  # ⬅️ Descargar datos frescos
)
```

## ⚠️ Advertencias Importantes

### Antes de Trading en Producción

**🚨 CRÍTICO - Completar validación antes de uso real:**

1. ✅ **Walk-Forward Analysis**
   - Optimizar en periodo N, validar en N+1
   - Verificar robustez de parámetros

2. ✅ **Out-of-Sample Testing**
   - Reservar últimas 2000 velas como test
   - Rendimiento esperado > 70% del optimizado

3. ✅ **Paper Trading**
   - Mínimo 2 semanas en demo
   - Monitorear slippage real

4. ✅ **Stress Testing**
   - Probar en condiciones extremas
   - Verificar drawdown máximo

### Limitaciones Actuales

- **Overfitting Risk**: Optimizaciones en 10,000 velas pueden estar sobreajustadas
- **Condiciones de Mercado**: Periodo evaluado puede no representar el futuro
- **Slippage Real**: Simulación usa 0.05% comisión, real puede ser 1-3% mayor
- **Tamaño de Muestra**: Algunas estrategias tienen < 50 trades (preferible > 100)

### Disclaimer

> **⚠️ Este software es solo para fines educativos y de investigación.**
>
> El trading de criptomonedas conlleva riesgos significativos. Los resultados pasados no garantizan rendimientos futuros. Nunca inviertas más de lo que puedas permitirte perder. Los autores no se hacen responsables de pérdidas financieras derivadas del uso de este software.

## 🛠️ Desarrollo

### Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Pre-commit Hooks

Instalar hooks de calidad de código:

```bash
pip install pre-commit
pre-commit install
```

Incluye:
- Black (formateo)
- isort (ordenar imports)
- flake8 (linting)
- mypy (type checking)
- bandit (seguridad)

### Agregar Nueva Estrategia

1. **Crear archivo de estrategia**:
   ```python
   # strategies/my_strategy.py
   from strategies.base import BaseStrategy

   class MyStrategy(BaseStrategy):
       def generate_signals(self, df):
           # Implementar lógica
           pass
   ```

2. **Registrar en registry.py**:
   ```python
   STRATEGY_REGISTRY["MY_STRATEGY"] = (MyStrategy, MyStrategyConfig)
   ```

3. **Agregar configuración en settings.py**:
   ```python
   MY_STRATEGY_CONFIG = MyStrategyConfig(...)
   ```

4. **Crear tests**:
   ```python
   # tests/test_my_strategy.py
   def test_my_strategy():
       # Implementar tests
       pass
   ```

## 📈 Roadmap

### Versión Actual (v1.0)
- ✅ 4 estrategias optimizadas
- ✅ Framework de optimización
- ✅ Tests completos
- ✅ Documentación exhaustiva

### Próximas Versiones

**v1.1 - Validación Avanzada**
- [ ] Walk-forward analysis automatizado
- [ ] Out-of-sample testing
- [ ] Stress testing framework
- [ ] Monte Carlo simulation

**v1.2 - Estrategias Adicionales**
- [ ] Optimizar SUPERTREND con filtro ADX
- [ ] Refactorizar MA_RSI con filtros de tendencia
- [ ] Evaluar MACD_ADX y SQUEEZE
- [ ] Estrategias en timeframes 1h y 4h

**v1.3 - Mejoras del Sistema**
- [ ] Trailing stops adaptativos
- [ ] Position sizing dinámico
- [ ] Filtros de volatilidad y volumen
- [ ] Ensemble de múltiples estrategias

**v2.0 - Trading en Vivo**
- [ ] Integración con exchanges
- [ ] Gestión de órdenes real
- [ ] Monitoreo en tiempo real
- [ ] Dashboard web interactivo
- [ ] Sistema de alertas

## 🤝 Soporte

### Recursos

- **Issues**: [GitHub Issues](https://github.com/alvaroSaavedraCalero/crypto-trading-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alvaroSaavedraCalero/crypto-trading-bot/discussions)
- **Email**: alvaro@example.com

### FAQ

**P: ¿Puedo usar esto en trading real?**
R: Solo después de validación exhaustiva (walk-forward, paper trading, stress testing).

**P: ¿Qué estrategia es mejor?**
R: KELTNER (PF 2.01) para trending markets, BOLLINGER_MR (PF 2.23) para mean reversion.

**P: ¿Funcionan estas configuraciones en otros timeframes?**
R: Requieren re-optimización. Las configuraciones son específicas para 15m.

**P: ¿Por qué algunas estrategias no están optimizadas?**
R: Prioridad basada en resultados iniciales. Ver STRATEGY_ANALYSIS.md para roadmap.

**P: ¿Cómo actualizo los datos?**
R: `force_download=True` en `get_datos_cripto_cached()` o elimina los CSV del cache.

## 📝 Changelog

### [1.0.0] - 2026-01-14

#### Added
- ✨ Framework completo de optimización multi-estrategia
- ✨ 4 estrategias con configuraciones optimizadas (7000+ tests)
- ✨ Scripts de evaluación rápida y optimización focalizada
- ✨ Documentación exhaustiva (600+ líneas)
- ✨ Fixture `backtester` para tests

#### Changed
- ♻️ Configuraciones en `settings.py` con versiones optimizadas
- ♻️ OPTIMIZED_STRATEGIES ahora prioriza estrategias optimizadas
- 📝 README completamente reescrito

#### Fixed
- 🐛 Tests corregidos (115/115 pasando)
- 🐛 Validación de dataframes vacíos en Supertrend
- 🐛 Parámetros incorrectos en fixtures
- 🐛 Parámetro `n_jobs` en optimizador

#### Performance
- ⚡ KELTNER: +89.6% mejora (PF 1.06 → 2.01)
- ⚡ BOLLINGER_MR: +137.2% mejora (PF 0.94 → 2.23)

## 📜 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🌟 Agradecimientos

- **CCXT**: Por la librería de exchange unificada
- **TA-Lib / ta**: Por indicadores técnicos
- **Pandas / NumPy**: Por procesamiento de datos eficiente
- **Pytest**: Por framework de testing robusto
- **Rich**: Por output de consola hermoso

---

<div align="center">

**⭐ Si este proyecto te resultó útil, considera darle una estrella en GitHub ⭐**

[Documentación](docs/) · [Reportar Bug](issues) · [Solicitar Feature](issues)

Hecho con ❤️ por [Alvaro Saavedra](https://github.com/alvaroSaavedraCalero)

</div>
