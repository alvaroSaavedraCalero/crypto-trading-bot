# Arquitectura Full Stack - Crypto Trading Bot

## 🏗️ Visión General

Arquitectura moderna con separación clara entre frontend, backend y base de datos.

```
┌─────────────────┐
│   FRONTEND      │  React + Vite
│   (Port 3000)   │  ↓ HTTP/WebSocket
├─────────────────┤
│   BACKEND       │  FastAPI + SQLAlchemy
│   (Port 8000)   │  ↓ SQL
├─────────────────┤
│   DATABASE      │  SQLite/PostgreSQL
│                 │
└─────────────────┘
```

## 📦 Componentes

### Backend (FastAPI)

**Responsabilidades:**
- API REST endpoints
- Lógica de backtesting
- Gestión de paper trading
- Persistencia de datos
- Validación y seguridad

**Tecnologías:**
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Pydantic 2.5.0
- Python 3.10+

**Estructura:**
```
backend/
├── app/
│   ├── models/          # ORM models (Strategy, User, BacktestRun, etc)
│   ├── schemas/         # Pydantic validation schemas
│   ├── crud/            # Database operations
│   ├── api/routes/      # API endpoints
│   ├── services/        # Business logic
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   └── main.py          # FastAPI app
├── migrations/          # Alembic (future)
├── requirements.txt
└── main.py              # Entry point
```

### Frontend (React + Vite)

**Responsabilidades:**
- UI interactiva
- Visualización de datos
- Formularios
- Dashboard en tiempo real

**Tecnologías:**
- React 18
- Vite 5
- Axios (HTTP client)
- Chart.js (gráficos)
- React Router (navigation)

**Estructura:**
```
frontend/
├── src/
│   ├── components/      # Reutilizables (Layout, Sidebar)
│   ├── pages/           # Rutas principales
│   ├── services/        # Cliente API
│   ├── App.jsx
│   └── main.jsx
├── package.json
├── vite.config.js
└── index.html
```

### Base de datos

**Tablas:**

1. **users** - Usuarios del sistema
   - id, username, email, is_active, created_at

2. **strategies** - Definiciones de estrategias
   - id, owner_id, name, strategy_type, config, is_active

3. **backtest_runs** - Ejecuciones de backtests
   - id, strategy_id, pair, timeframe, results (return, winrate, dd, etc)

4. **backtest_trades** - Trades generados en backtests
   - id, backtest_run_id, entry/exit data, pnl, is_winning

5. **paper_trading_sessions** - Sesiones de simulación
   - id, strategy_id, pair, capital, results

6. **paper_trades** - Trades en paper trading
   - id, session_id, entry/exit data, pnl

**Relaciones:**
```
User (1) ─── (N) Strategy
User (1) ─── (N) BacktestRun
User (1) ─── (N) PaperTradingSession
Strategy (1) ─── (N) BacktestRun
Strategy (1) ─── (N) PaperTradingSession
BacktestRun (1) ─── (N) BacktestTrade
PaperTradingSession (1) ─── (N) PaperTrade
```

## 🔄 Flujos principales

### 1. Crear y ejecutar estrategia

```
Frontend (Crear formulario)
  ↓
Backend (POST /strategies)
  ↓
Database (INSERT strategy)
  ↓
Response + ID
  ↓
Frontend (Actualizar lista)
```

### 2. Ejecutar backtest

```
Frontend (Seleccionar estrategia + parámetros)
  ↓
Backend (POST /backtests)
  ↓
Backend Service (Cargar datos, ejecutar backtest)
  ↓
Database (Guardar resultados + trades)
  ↓
Frontend (Mostrar gráficos)
```

### 3. Monitorear paper trading

```
Backend (Cron job o WebSocket)
  ↓
Fetch latest candles
  ↓
Generate signals
  ↓
Execute trades
  ↓
Database (Actualizar PaperTrade)
  ↓
Frontend (WebSocket o polling)
  ↓
Dashboard actualizado en tiempo real
```

## 🚀 Guía de inicio

### 1. Instalar Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

API disponible en: http://localhost:8000
Docs: http://localhost:8000/docs

### 2. Instalar Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible en: http://localhost:3000

### 3. Acceder

- Dashboard: http://localhost:3000
- API REST: http://localhost:8000/api/v1

## 🔐 Seguridad (TODO)

- [ ] JWT authentication
- [ ] Role-based access control (RBAC)
- [ ] Input validation + sanitization
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Environment variables

## 📊 Escalabilidad

**Optimizaciones futuras:**
- [ ] Cacheo con Redis
- [ ] WebSockets para real-time updates
- [ ] Message queue (Celery) para backtests largos
- [ ] Database connection pooling
- [ ] CDN para assets frontend
- [ ] Containerización (Docker)
- [ ] Kubernetes deployment

## 📈 Integración con código existente

El código existente (backtesting, optimización, paper trading) puede:

1. **Mantenerse como módulos Python** y ser importados por los servicios del backend
2. **Exponerse a través de endpoints API** para ser consumido por el frontend
3. **Ejecutarse en tareas asincrónicas** para no bloquear la API

Ejemplo:
```python
# backend/app/services/backtest_service.py
from backtesting.engine import Backtester
from optimization.optimize_ma_rsi import optimize_ma_rsi

async def run_backtest(strategy_config):
    # Utilizar código existente
    backtester = Backtester(config)
    result = backtester.backtest(df)
    # Guardar en BD
    return result
```

## 📝 Próximos pasos

1. **Conectar lógica existente** a los servicios del backend
2. **Implementar autenticación** (JWT)
3. **Agregar WebSockets** para actualizaciones en tiempo real
4. **Crear más endpoints** (descarga de reportes, histórico, etc)
5. **Tests** unitarios e integración
6. **Documentación API** completa
7. **Deployment** en servidor
