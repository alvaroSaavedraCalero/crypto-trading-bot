# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack crypto trading bot with a FastAPI backend (JWT auth), React/Vite frontend (dark theme), a pluggable strategy system (20 strategies), an advanced backtesting engine (walk-forward, Monte Carlo), and paper trading simulation. Uses SQLite in development with Alembic migrations.

## Common Commands

### Start Full Stack
```bash
./start_system.sh  # Backend on :8000, Frontend on :3000
```

### Backend Only
```bash
source .venv/bin/activate
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Only
```bash
cd frontend && npm run dev
```

### Tests
```bash
source .venv/bin/activate
pytest -v                          # All 14 tests (tests/ directory)
pytest tests/test_health.py -v     # 4 health endpoint tests
pytest tests/test_strategies.py -v # 10 strategy CRUD + auth tests
python test_integration.py         # Legacy integration tests
python STATUS_REPORT.py            # Component health check
```

### Linting & Formatting
```bash
black --line-length 100 .          # Format Python
isort --profile black .            # Sort imports
flake8 .                           # Lint
mypy .                             # Type check
```

### Frontend Build
```bash
cd frontend && npm run build       # Production build to dist/
cd frontend && npm run lint        # ESLint
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback last
```

## Architecture

### Stack
- **Backend:** FastAPI + SQLAlchemy + Pydantic + JWT Auth (python-jose + passlib)
- **Frontend:** React 18 + Vite + Chart.js + lightweight-charts (TradingView) + react-hot-toast
- **Database:** SQLite (dev), PostgreSQL-ready via SQLAlchemy, Alembic migrations
- **Data sources:** yfinance (OHLCV, cached with TTL), Fear & Greed Index API

### Key Directories
- `backend/app/` — FastAPI application (models, schemas, routes, services, crud)
- `backend/app/api/auth.py` — JWT authentication (register, login, get_current_user)
- `backend/app/api/routes/` — API route modules (health, strategies, backtests, paper_trading, dashboard)
- `backend/app/models/` — 15 SQLAlchemy models (User, Strategy, BacktestRun, BacktestTrade, PaperTradingSession, PaperTrade, Portfolio, PortfolioHolding, Watchlist, Alert, MarketDataCache, UserSettings, AuditLog, StrategyPerformance, OrderHistory)
- `backend/alembic/` — Database migration files
- `frontend/src/` — React SPA (9 pages, chart components, auth context)
- `frontend/src/context/AuthContext.jsx` — JWT token management (login, logout, isAuthenticated)
- `frontend/src/services/api.js` — Axios with JWT interceptor (auto-attaches Bearer token)
- `frontend/src/styles/theme.css` — CSS variables for dark theme
- `strategies/` — 20 trading strategy implementations with registry pattern
- `backtesting/engine.py` — Advanced backtesting engine (walk-forward, Monte Carlo, signal_strength)
- `data/` — Data providers (yfinance with TTL cache, Fear & Greed, abstract base)
- `utils/` — Risk management (`risk.py`), validation helpers (`validation.py`), logging (`logger.py`)
- `tests/` — Test suite (conftest.py with fixtures, test_health.py, test_strategies.py)

### Backend Flow
```
Routes (api/routes/) → Auth (JWT) → Services (services/) → Database (models/)
                                                          → Strategy Registry (strategies/)
                                                          → Backtesting Engine (backtesting/)
                                                          → Data Providers (data/)
```

All API routes prefixed with `/api/v1`. API docs at `http://localhost:8000/docs`.

Route modules: `health.py`, `strategies.py`, `backtests.py`, `paper_trading.py`, `dashboard.py`.

### Authentication
- JWT Bearer tokens via `python-jose` + `passlib[bcrypt]`
- `POST /api/v1/auth/register` — returns JWT
- `POST /api/v1/auth/login` — OAuth2PasswordRequestForm, returns JWT
- `get_current_user` dependency injected into protected routes
- Frontend: AuthContext + axios interceptor auto-attaches token from localStorage

### API Endpoints (30+)
- **Auth (2):** `POST /auth/register`, `POST /auth/login` (public)
- **Health (3):** `GET /health`, `GET /health/ready`, `GET /health/live` (public)
- **Strategies (7):** CRUD + `POST /{id}/clone` + `GET /types` (types is public)
- **Backtests (4):** `GET /`, `POST /` (async), `GET /{id}`, `DELETE /{id}`
- **Paper Trading (6):** `GET /`, `POST /`, `GET /{id}`, `POST /{id}/run`, `GET /{id}/trades`, `POST /{id}/close`
- **Dashboard (2):** `GET /stats`, `GET /summary`
- **Market (2):** `GET /market/prices/{symbol}`, `GET /market/ohlcv/{symbol}`

### Strategy System
All strategies inherit from `strategies/base.py:BaseStrategy` and implement `generate_signals(df) -> DataFrame` which adds a `signal` column (1=long, -1=short, 0=neutral). Optional `signal_strength` column (0.0-1.0) for position sizing.

New strategies must:
1. Create a `@dataclass` config class with validation in `__post_init__`
2. Subclass `BaseStrategy[ConfigT]`
3. Register in `strategies/registry.py:STRATEGY_REGISTRY`

Available types (20): `MA_RSI`, `MACD_ADX`, `KELTNER`, `BB_TREND`, `SQUEEZE`, `SUPERTREND`, `BOLLINGER_MR`, `SMART_MONEY`, `ICT`, `AI_RF`, `VWAP`, `KAMA`, `MEAN_REVERSION`, `ORDER_FLOW`, `VOLUME_PROFILE`, `MULTI_TF`, `GARCH`, `WYCKOFF`, `PAIRS_TRADING`, `COMPOSITE`.

### Backtesting Engine
- Entry at next candle open (no look-ahead bias)
- Intelligent SL/TP resolution (distance from open)
- No same-candle re-entry after exit
- Full equity curve with unrealized PnL for accurate max drawdown
- Metrics: Sharpe, Sortino, Calmar, Expectancy, Recovery Factor, max consecutive W/L
- `walk_forward_backtest()` for rolling train/test analysis
- `monte_carlo()` for outcome distribution simulation
- `signal_strength` support for dynamic position sizing

### Database
15 SQLAlchemy models with Alembic migrations. Enums for strategy_type and trade side. Float types for monetary values. Boolean for is_winning. server_default=func.now() for timestamps. Proper indexes on foreign keys and frequently queried columns. Cascade deletes configured.

### Frontend
9 pages routed via React Router with ProtectedRoute wrapper: Login, Dashboard, Strategies, Backtests, PaperTrading, Portfolio, TradeJournal, RiskAnalytics, Settings. Dark theme with CSS variables. Charts: CandlestickChart (TradingView), EquityCurveChart, DrawdownChart, WinLossChart, RadarChart. All API calls via `frontend/src/services/api.js` (Axios with JWT interceptor). Vite proxies `/api` to `localhost:8000`.

## Code Style
- Python: Black (line-length 100), isort (profile: black), target Python 3.10+
- First-party modules for isort: `strategies`, `backtesting`, `optimization`, `utils`, `data`, `config`
- pytest markers: `slow`, `integration`
- Coverage tracks: `strategies`, `backtesting`, `optimization`, `utils` (branch coverage)
- Frontend: Spanish UI text, CSS variables for theming, no TailwindCSS
