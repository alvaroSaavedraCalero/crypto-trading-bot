# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack crypto trading bot with a FastAPI backend, React/Vite frontend, a pluggable strategy system (10 strategies), a backtesting engine, and paper trading simulation. Uses SQLite in development.

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
pytest -v                          # All tests (tests/ directory)
pytest -m integration              # Integration tests only
pytest -m "not slow"               # Skip slow tests
pytest tests/test_foo.py::test_bar # Single test
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
```

## Architecture

### Stack
- **Backend:** FastAPI + SQLAlchemy + Pydantic (Python 3.10+)
- **Frontend:** React 18 + Vite + TailwindCSS + Chart.js
- **Database:** SQLite (dev), PostgreSQL-ready via SQLAlchemy
- **Data source:** yfinance for OHLCV market data

### Key Directories
- `backend/app/` — FastAPI application (models, schemas, routes, services, crud)
- `frontend/src/` — React SPA (pages, components, services/api.js)
- `strategies/` — Trading strategy implementations with registry pattern
- `backtesting/engine.py` — Backtesting engine (BacktestConfig, Backtester, TradeResult)
- `data/yfinance_downloader.py` — Market data fetcher
- `utils/` — Risk management, validation helpers, logging

### Backend Flow
```
Routes (api/routes/) → Services (services/) → Database (models/)
                                             → Strategy Registry (strategies/)
                                             → Backtesting Engine (backtesting/)
```

All API routes are prefixed with `/api/v1`. API docs at `http://localhost:8000/docs`.

Route modules: `health.py`, `strategies.py`, `backtests.py`, `paper_trading.py`, `dashboard.py`.

### Strategy System
All strategies inherit from `strategies/base.py:BaseStrategy` and implement `generate_signals(df) -> DataFrame` which adds a `signal` column (1=long, -1=short, 0=neutral).

New strategies must:
1. Create a `@dataclass` config class with validation in `__post_init__`
2. Subclass `BaseStrategy[ConfigT]`
3. Register in `strategies/registry.py:STRATEGY_REGISTRY`

Available types: `MA_RSI`, `MACD_ADX`, `KELTNER`, `BB_TREND`, `SQUEEZE`, `SUPERTREND`, `BOLLINGER_MR`, `SMART_MONEY`, `ICT`, `AI_RF`.

### Database
7 SQLAlchemy models: User, Strategy, BacktestRun, BacktestTrade, PaperTradingSession, PaperTrade, plus Base. Tables auto-created on startup via `init_db()`. No Alembic migrations configured — schema changes require recreating the DB or manual ALTER.

Strategy configs are stored as JSON columns for flexibility.

### Frontend
4 pages routed via React Router: Dashboard, Strategies, Backtests, PaperTrading. All API calls go through `frontend/src/services/api.js` (Axios). Vite proxies `/api` to `localhost:8000`.

## Code Style
- Python: Black (line-length 100), isort (profile: black), target Python 3.10+
- First-party modules for isort: `strategies`, `backtesting`, `optimization`, `utils`, `data`, `config`
- pytest markers: `slow`, `integration`
- Coverage tracks: `strategies`, `backtesting`, `optimization`, `utils` (branch coverage)
