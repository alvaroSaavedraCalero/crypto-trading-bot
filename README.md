# Crypto Trading Bot - Full Stack

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.104.1-green.svg)]()
[![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)]()

Sistema completo de trading algoritmico con:
- **Backend**: FastAPI con 30+ endpoints REST y autenticacion JWT
- **Frontend**: React + Vite con dark theme profesional, graficos TradingView y 8 paginas
- **Database**: SQLAlchemy ORM con 15 modelos + migraciones Alembic
- **Strategies**: 20 estrategias de trading pluggables (incluye ML, GARCH, Wyckoff)
- **Backtesting**: Motor avanzado con Sharpe/Sortino/Calmar, walk-forward y Monte Carlo
- **Paper Trading**: Simulacion en tiempo real
- **Data Sources**: yfinance + Fear & Greed Index + cache TTL

---

## Tabla de Contenidos

- [Inicio Rapido](#inicio-rapido)
- [Arquitectura](#arquitectura)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tecnologias](#tecnologias)
- [Estrategias de Trading](#estrategias-de-trading-20)
- [API Endpoints](#api-endpoints-30)
- [Autenticacion](#autenticacion)
- [Database Models](#database-models-15)
- [Testing](#testing)
- [Configuracion](#configuracion)
- [Troubleshooting](#troubleshooting)

---

## Inicio Rapido

### Prerequisitos

- Python 3.10+
- Node.js 16+
- Git

### Setup

```bash
# 1. Clonar
git clone <tu-repo>
cd crypto-trading-bot

# 2. Crear venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 4. Ejecutar
./start_system.sh
```

Accede a:
- **App**: http://localhost:3000 (registrate para comenzar)
- **API Docs**: http://localhost:8000/docs

---

## Arquitectura

```
Frontend (React)          Backend (FastAPI)         Database (SQLAlchemy)
-----------------         -----------------         --------------------
  Login/Register     ->     /api/v1/auth           ->    Users
  Dashboard          ->     /api/v1/dashboard      ->    SQLite (dev)
  Strategies         ->     /api/v1/strategies     ->    PostgreSQL (prod)
  Backtests          ->     /api/v1/backtests
  PaperTrading       ->     /api/v1/paper-trading
  Portfolio          ->     /api/v1/market
  Trade Journal           (30+ endpoints total)
  Risk Analytics          JWT Authentication
  Settings                CORS + Rate Limiting
```

### Flujo de Datos

```
Routes (api/routes/) -> Auth (JWT) -> Services (services/) -> Database (models/)
                                                            -> Strategy Registry (strategies/)
                                                            -> Backtesting Engine (backtesting/)
                                                            -> Data Providers (data/)
```

1. **Frontend** -> API (Axios con interceptor JWT + proxy Vite)
2. **Auth** -> JWT Bearer token validation
3. **API** -> Services (BacktestService, PaperTradingService)
4. **Services** -> Strategies (20) + Backtesting Engine + Data Cache
5. **Database** -> Persistencia (SQLAlchemy ORM + Alembic migrations)

---

## Estructura del Proyecto

```
crypto-trading-bot/
├── backend/                   # FastAPI Application
│   ├── app/
│   │   ├── main.py           # Entry point, CORS, lifespan
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   ├── models/           # 15 modelos ORM
│   │   │   ├── user.py, strategy.py, backtest_run.py, backtest_trade.py
│   │   │   ├── paper_trading_session.py, paper_trade.py
│   │   │   ├── portfolio.py, watchlist.py, alert.py
│   │   │   ├── market_data.py, user_settings.py, audit_log.py
│   │   │   ├── strategy_performance.py, order_history.py
│   │   │   └── __init__.py   # Exports all models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Logica de negocio (async backtesting)
│   │   ├── crud/             # Operaciones BD
│   │   └── api/
│   │       ├── auth.py       # JWT register/login/get_current_user
│   │       └── routes/       # 6 modulos de rutas
│   ├── alembic/              # Database migrations
│   └── alembic.ini
│
├── frontend/                  # React + Vite (Dark Theme)
│   ├── src/
│   │   ├── context/          # AuthContext (JWT management)
│   │   ├── components/
│   │   │   ├── charts/       # CandlestickChart, EquityCurve, Drawdown, WinLoss, Radar
│   │   │   ├── stats/        # StatsGrid, MetricsPanel
│   │   │   ├── Layout.jsx    # Main layout with logout button
│   │   │   └── Sidebar.jsx   # Navigation sidebar
│   │   ├── pages/            # 9 paginas
│   │   │   ├── Login.jsx     # Login/Register con JWT
│   │   │   ├── Dashboard.jsx, Strategies.jsx, Backtests.jsx
│   │   │   ├── PaperTrading.jsx, Portfolio.jsx
│   │   │   ├── TradeJournal.jsx, RiskAnalytics.jsx, Settings.jsx
│   │   ├── services/api.js   # Axios con JWT interceptor
│   │   └── styles/theme.css  # CSS variables (dark theme)
│   └── package.json
│
├── strategies/                # 20 estrategias de trading
│   ├── base.py               # BaseStrategy[ConfigT] + signal_strength support
│   ├── registry.py           # STRATEGY_REGISTRY (20 entries)
│   ├── ma_rsi_strategy.py, macd_adx_trend_strategy.py
│   ├── keltner_breakout_strategy.py, squeeze_momentum_strategy.py
│   ├── supertrend_strategy.py, bollinger_mean_reversion.py
│   ├── smart_money_strategy.py, ict_strategy.py, ai_strategy.py
│   ├── vwap_strategy.py, kama_strategy.py
│   ├── mean_reversion_strategy.py, order_flow_strategy.py
│   ├── volume_profile_strategy.py, multi_tf_strategy.py
│   ├── garch_strategy.py, wyckoff_strategy.py
│   ├── pairs_trading_strategy.py, composite_strategy.py
│   └── archived/             # Archived strategies
│
├── backtesting/               # Motor de backtesting avanzado
│   └── engine.py             # Backtester + walk_forward + monte_carlo
│
├── data/                      # Data providers
│   ├── base_provider.py      # Abstract DataProvider
│   ├── yfinance_downloader.py # OHLCV via yfinance (cached)
│   ├── cache.py              # TTL cache layer
│   └── sentiment/
│       └── fear_greed.py     # Fear & Greed Index
│
├── utils/                     # Utilidades
│   ├── logger.py, risk.py, validation.py
│
├── tests/                     # Test suite (14 tests)
│   ├── conftest.py           # Test DB, fixtures, auth helpers
│   ├── test_health.py        # 4 health endpoint tests
│   └── test_strategies.py    # 10 strategy CRUD + auth tests
│
├── requirements.txt          # Python dependencies
├── start_system.sh           # Script de inicio full-stack
└── CLAUDE.md                 # Instrucciones para Claude Code
```

---

## Tecnologias

### Backend
| Paquete | Version | Uso |
|---------|---------|-----|
| FastAPI | >= 0.104.1 | Framework web |
| SQLAlchemy | >= 2.0.23 | ORM |
| Pydantic | >= 2.5.0 | Validacion de datos |
| python-jose | >= 3.5.0 | JWT Authentication |
| passlib + bcrypt | >= 1.7.4 | Password hashing |
| Alembic | >= 1.18.0 | Database migrations |
| yfinance | >= 0.2.33 | Datos financieros |
| pandas | >= 2.1.3 | Procesamiento de datos |
| numpy | >= 1.26.2 | Calculo numerico |
| ta | >= 0.10.2 | Indicadores tecnicos |
| statsmodels | >= 0.14.0 | Tests estadisticos (ADF, Hurst) |
| arch | >= 8.0.0 | Modelos GARCH |
| scipy | >= 1.17.0 | Computacion cientifica |
| scikit-learn | >= 1.5.0 | Machine Learning |

### Frontend
| Paquete | Version | Uso |
|---------|---------|-----|
| React | ^18.2.0 | UI Library |
| Vite | ^5.0.0 | Build tool |
| Axios | ^1.6.0 | HTTP Client con JWT interceptor |
| React Router | ^6.20.0 | Routing + protected routes |
| lightweight-charts | ^5.1.0 | Graficos TradingView (candlestick) |
| Chart.js + react-chartjs-2 | ^4.4.0 | Equity curves, radar, bar charts |
| react-hot-toast | ^2.6.0 | Toast notifications |
| react-error-boundary | ^6.1.0 | Error boundaries |
| @tanstack/react-query | ^5.90.0 | Data fetching + caching |
| date-fns | ^4.1.0 | Date formatting |
| react-icons | ^4.12.0 | Iconos |

### Database
- **SQLite** (desarrollo) — auto-creado en startup
- **PostgreSQL** (produccion, ready via SQLAlchemy)
- **Alembic** para migraciones de schema

---

## Estrategias de Trading (20)

Todas heredan de `BaseStrategy` e implementan `generate_signals(df) -> DataFrame` con columna `signal` (1=long, -1=short, 0=neutral). Soporte opcional para `signal_strength` (0.0-1.0).

### Estrategias Clasicas
| Tipo | Estrategia | Descripcion |
|------|-----------|-------------|
| `MA_RSI` | Moving Average + RSI | Cruce de medias con filtro RSI + volumen |
| `MACD_ADX` | MACD + ADX Trend | Tendencia con MACD/ADX + filtro DI+/DI- |
| `KELTNER` | Keltner Breakout | Ruptura de canales Keltner |
| `BB_TREND` | Bollinger Band Trend | Tendencia con Bandas de Bollinger |
| `SQUEEZE` | Squeeze Momentum | Momentum en compresion de volatilidad |
| `SUPERTREND` | Supertrend | Indicador Supertrend (vectorizado) |
| `BOLLINGER_MR` | Bollinger Mean Reversion | Reversion a la media |

### Estrategias Avanzadas
| Tipo | Estrategia | Descripcion |
|------|-----------|-------------|
| `SMART_MONEY` | Smart Money Concepts | FVG + Order Blocks institucionales |
| `ICT` | ICT Concepts | Kill zones + MSS + FVG entries |
| `VWAP` | VWAP Bands | Volume Weighted Average Price + std bands |
| `KAMA` | Adaptive Moving Average | Kaufman AMA (adapta velocidad a mercado) |
| `ORDER_FLOW` | Delta Volume | Flujo de ordenes + divergencias |
| `VOLUME_PROFILE` | Volume Profile | POC/VAH/VAL + mean reversion/breakout |
| `WYCKOFF` | Wyckoff Method | Springs + UTAD en rangos de consolidacion |

### Estrategias Cuantitativas
| Tipo | Estrategia | Descripcion |
|------|-----------|-------------|
| `MEAN_REVERSION` | Statistical Mean Reversion | Hurst + ADF + z-score |
| `GARCH` | Volatility Regime | GARCH(1,1) deteccion de regimen |
| `PAIRS_TRADING` | Statistical Arbitrage | Cointegracion + spread z-score |
| `MULTI_TF` | Multi-Timeframe | Confluencia multi-temporalidad |
| `AI_RF` | AI Gradient Boosting | ML con walk-forward training |
| `COMPOSITE` | Strategy Combiner | Combina multiples estrategias (majority/unanimous/weighted) |

---

## API Endpoints (30+)

Todos bajo el prefijo `/api/v1`. Documentacion interactiva en http://localhost:8000/docs

### Auth (2) - Publicos
```
POST   /api/v1/auth/register        Registro (username, email, password) -> JWT
POST   /api/v1/auth/login           Login (OAuth2 form) -> JWT
```

### Health (3) - Publicos
```
GET    /api/v1/health               Status del servidor + metricas
GET    /api/v1/health/ready          Readiness check
GET    /api/v1/health/live           Liveness check
```

### Strategies (7) - Requieren JWT
```
GET    /api/v1/strategies            Listar (filtrada por usuario)
POST   /api/v1/strategies            Crear nueva (valida strategy_type)
GET    /api/v1/strategies/{id}       Detalles
PUT    /api/v1/strategies/{id}       Actualizar
DELETE /api/v1/strategies/{id}       Eliminar
POST   /api/v1/strategies/{id}/clone Clonar estrategia
GET    /api/v1/strategies/types      Listar tipos disponibles (publico)
```

### Backtests (4) - Requieren JWT
```
GET    /api/v1/backtests             Listar (filtrada por usuario)
POST   /api/v1/backtests             Ejecutar nuevo (async)
GET    /api/v1/backtests/{id}        Resultados + trades + metricas
DELETE /api/v1/backtests/{id}        Eliminar
```

### Paper Trading (6) - Requieren JWT
```
GET    /api/v1/paper-trading              Listar sesiones
POST   /api/v1/paper-trading              Crear sesion
GET    /api/v1/paper-trading/{id}         Detalles
POST   /api/v1/paper-trading/{id}/run     Ejecutar simulacion
GET    /api/v1/paper-trading/{id}/trades  Ver trades
POST   /api/v1/paper-trading/{id}/close   Cerrar sesion
```

### Dashboard (2) - Requieren JWT
```
GET    /api/v1/dashboard/stats       KPIs y estadisticas del portafolio
GET    /api/v1/dashboard/summary     Resumen con backtests y estrategias
```

### Market Data (2) - Requieren JWT
```
GET    /api/v1/market/prices/{symbol}  Precio actual (cached 60s)
GET    /api/v1/market/ohlcv/{symbol}   Datos OHLCV historicos
```

---

## Autenticacion

El sistema usa **JWT Bearer tokens**:

1. Registrate via `POST /api/v1/auth/register` con `{username, email, password}`
2. O login via `POST /api/v1/auth/login` con form data `username=...&password=...`
3. Ambos devuelven `{access_token, token_type: "bearer"}`
4. Incluye el token en cada request: `Authorization: Bearer <token>`

El frontend maneja esto automaticamente via axios interceptor.

---

## Database Models (15)

### Core Models
| Modelo | Descripcion |
|--------|-------------|
| **User** | Cuentas (username, email, hashed_password, is_active) |
| **Strategy** | Definicion de estrategia (config JSON, Float para capital/SL/TP) |
| **BacktestRun** | Resultados de backtests (owner filtrado, indexed) |
| **BacktestTrade** | Trades individuales (Boolean is_winning, Enum side) |
| **PaperTradingSession** | Sesiones (cascade delete, indexed) |
| **PaperTrade** | Trades de paper trading |

### New Models
| Modelo | Descripcion |
|--------|-------------|
| **Portfolio** | Portafolios de usuario |
| **PortfolioHolding** | Posiciones por simbolo |
| **Watchlist** | Listas de seguimiento (JSON symbols) |
| **Alert** | Alertas de precio/estrategia |
| **MarketDataCache** | Cache OHLCV local |
| **UserSettings** | Preferencias (tema, timezone, defaults) |
| **AuditLog** | Log de acciones (entity tracking) |
| **StrategyPerformance** | Metricas rolling por estrategia |
| **OrderHistory** | Historial de ordenes (para live trading futuro) |

Migraciones via **Alembic** (`backend/alembic/`). Enums para strategy_type y trade side.

---

## Backtesting Engine

El motor en `backtesting/engine.py` incluye:

- **Entry al next open** (sin look-ahead bias)
- **SL/TP inteligente**: resuelve ambiguedad por distancia al open
- **Sin re-entry en misma vela** tras exit
- **Max drawdown real**: equity curve completa con unrealized PnL
- **Metricas avanzadas**: Sharpe, Sortino, Calmar, Expectancy, Recovery Factor, max consecutive W/L
- **Walk-forward analysis**: `walk_forward_backtest(df, strategy, train_window, test_window, step)`
- **Monte Carlo simulation**: `monte_carlo(trades, n_simulations=1000)`
- **Signal strength**: position sizing dinamico basado en confianza

---

## Testing

```bash
source .venv/bin/activate

# Todos los tests (14 tests)
pytest -v

# Tests individuales
pytest tests/test_health.py -v      # 4 health tests
pytest tests/test_strategies.py -v  # 10 strategy CRUD + auth tests

# Legacy
python test_integration.py
python STATUS_REPORT.py
```

---

## Configuracion

### Backend (.env en backend/)
```env
DATABASE_URL=sqlite:///./trading_bot.db
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
API_PREFIX=/api/v1
```

### Frontend (.env en frontend/)
```env
VITE_API_URL=/api/v1
```

---

## Troubleshooting

### "Not authenticated"
- Asegurate de estar logueado (el token JWT se guarda en localStorage)
- Verifica que el token no haya expirado (default: 24h)
- Revisa la consola del navegador (F12) para errores de red

### "No module named fastapi"
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
lsof -i :8000
kill -9 <PID>
```

### Frontend no se conecta
1. Verifica que el backend esta corriendo en http://localhost:8000
2. Revisa proxy en `frontend/vite.config.js`
3. Abre DevTools (F12) -> Network tab

---

## Estadisticas del Proyecto

| Metrica | Valor |
|---------|-------|
| Endpoints API | 30+ |
| Modelos BD | 15 |
| Estrategias | 20 |
| Paginas Frontend | 9 |
| Componentes Charts | 5 |
| Tests | 14 |
| Metricas Backtest | 10+ (Sharpe, Sortino, Calmar...) |

---

**Ultima actualizacion**: 15 de febrero de 2026
