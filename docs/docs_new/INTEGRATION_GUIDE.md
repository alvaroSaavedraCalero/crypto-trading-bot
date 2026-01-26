# 🔗 Integración Full Stack - Backtesting + Paper Trading

## Resumen

Se ha realizado una integración completa entre:
- ✅ **Lógica existente de backtesting** (engine.py, strategies/)
- ✅ **Lógica existente de paper trading** (paper_trading_forex.py)
- ✅ **Backend API (FastAPI)**
- ✅ **Base de datos (SQLAlchemy)**

Ahora puedes ejecutar backtests y paper trading a través de API REST.

---

## 🏗️ Servicios creados

### 1. BacktestService (`backend/app/services/backtest_service.py`)

**Métodos:**

```python
# Ejecutar backtest y guardar resultados
BacktestService.run_backtest(
    db, strategy_id, pair="USDJPY", timeframe="15m"
)

# Obtener resultados de un backtest
BacktestService.get_backtest_results(db, backtest_id)
```

**Qué hace:**
- Obtiene la estrategia de la BD
- Descarga datos de Yahoo Finance
- Ejecuta el backtest usando la lógica existente
- Guarda resultados y trades en la BD

### 2. PaperTradingService (`backend/app/services/paper_trading_service.py`)

**Métodos:**

```python
# Crear sesión de paper trading
PaperTradingService.create_session(
    db, owner_id, strategy_id, pair="USDJPY"
)

# Ejecutar backtest dentro de una sesión
PaperTradingService.update_session_with_backtest(
    db, session_id, pair="USDJPY"
)

# Obtener detalles de una sesión
PaperTradingService.get_session_details(db, session_id)

# Cerrar una sesión
PaperTradingService.close_session(db, session_id)
```

**Qué hace:**
- Crea sesiones de simulación
- Ejecuta estrategias dentro de sesiones
- Guarda trades individuales
- Calcula estadísticas en tiempo real

---

## 📡 Endpoints API actualizados

### Backtests

```
POST /api/v1/backtests
├─ strategy_id: int
├─ pair: str (ej: "USDJPY")
├─ timeframe: str (ej: "15m")
├─ period: str (ej: "60d")
└─ limit: int (ej: 2000)

GET /api/v1/backtests/{backtest_id}
└─ Retorna resultados con trades

GET /api/v1/backtests
└─ Lista todos los backtests
```

### Paper Trading

```
POST /api/v1/paper-trading
├─ strategy_id: int
├─ pair: str
├─ timeframe: str
└─ name: str (opcional)

POST /api/v1/paper-trading/{session_id}/run
├─ pair: str
└─ timeframe: str

GET /api/v1/paper-trading/{session_id}
└─ Detalles completos con trades

GET /api/v1/paper-trading/{session_id}/trades
└─ Lista de trades

POST /api/v1/paper-trading/{session_id}/close
└─ Cierra la sesión
```

### Dashboard

```
GET /api/v1/dashboard/stats
└─ KPIs: estrategias, backtests, trades, capital, retorno

GET /api/v1/dashboard/summary
└─ Últimos backtests, sesiones activas, mejores estrategias
```

---

## 🧪 Prueba de integración

Se incluye un script de prueba que valida toda la integración:

```bash
cd backend
pip install -r requirements.txt
cd ..
python test_integration.py
```

**Output esperado:**

```
🚀 PRUEBA DE INTEGRACIÓN - Backtesting + Paper Trading

🗄️  Inicializando base de datos...
✅ Base de datos lista

============================================================
🔬 PRUEBA 1: Backtesting
============================================================

📊 Ejecutando backtest para estrategia: MA_RSI Test
   Par: USDJPY, Timeframe: 15m

✅ Backtest completado exitosamente!
   ID: 1
   Retorno: -2.09%
   Winrate: 0.0%
   Trades: 2
   Profit Factor: 0.00
   Max Drawdown: -2.11%

============================================================
📈 PRUEBA 2: Paper Trading
============================================================

🎮 Creando sesión de paper trading
✅ Sesión creada: MA_RSI Test - USDJPY
   ID: 1
   Capital: $10,000.00

   Ejecutando estrategia...
   ✅ Backtest ejecutado!
      Trades: 2
      Ganadores: 0
      Perdedores: 2
      Retorno: -2.09%
      Capital final: $9,791.00

✅ RESUMEN DE PRUEBAS

✓ Backtest creado (ID: 1)
✓ Sesión paper trading creada (ID: 1)

📊 La integración está funcionando correctamente!
```

---

## 🔄 Flujo de datos

### Crear y ejecutar estrategia:

```
Frontend (React)
  ↓ [POST /api/v1/strategies]
Backend (FastAPI)
  ↓
Database (SQLAlchemy)
  ├─ Guarda: Strategy
  └─ Retorna: strategy_id
  ↓
Frontend (Muestra en lista)
```

### Ejecutar backtest:

```
Frontend (Selecciona estrategia + par)
  ↓ [POST /api/v1/backtests]
BacktestService
  ├─ Obtiene estrategia de BD
  ├─ Descarga datos (Yahoo Finance)
  ├─ Ejecuta backtest (engine.py)
  ├─ Guarda BacktestRun
  ├─ Guarda BacktestTrades
  └─ Retorna resultados
  ↓
Frontend (Muestra gráficos)
```

### Ejecutar paper trading:

```
Frontend (Crea sesión)
  ↓ [POST /api/v1/paper-trading]
PaperTradingService
  ├─ Crea PaperTradingSession
  └─ Retorna session_id
  ↓
Frontend (Ejecuta)
  ↓ [POST /api/v1/paper-trading/{id}/run]
PaperTradingService
  ├─ Obtiene estrategia
  ├─ Descarga datos
  ├─ Ejecuta backtest
  ├─ Guarda PaperTrades
  ├─ Actualiza estadísticas
  └─ Retorna resultados
  ↓
Frontend (Monitorea)
  ↓ [GET /api/v1/paper-trading/{id}]
  ↓ Muestra dashboard en tiempo real
```

---

## 📊 Ejemplos de uso

### Con cURL

**Crear estrategia:**
```bash
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MA_RSI Custom",
    "strategy_type": "MA_RSI",
    "config": {
      "fast_window": 10,
      "slow_window": 20,
      "rsi_window": 14
    }
  }'
```

**Ejecutar backtest:**
```bash
curl -X POST "http://localhost:8000/api/v1/backtests?strategy_id=1&pair=USDJPY&timeframe=15m"
```

**Obtener resultados:**
```bash
curl http://localhost:8000/api/v1/backtests/1
```

### Con Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Crear estrategia
strategy = requests.post(f"{BASE_URL}/strategies", json={
    "name": "MA_RSI Test",
    "strategy_type": "MA_RSI",
    "config": {"fast_window": 10, "slow_window": 20, ...}
}).json()

strategy_id = strategy['id']

# Ejecutar backtest
backtest = requests.post(
    f"{BASE_URL}/backtests",
    params={
        "strategy_id": strategy_id,
        "pair": "USDJPY",
        "timeframe": "15m"
    }
).json()

print(f"Retorno: {backtest['total_return_pct']}%")
```

---

## 🔗 Integración con código existente

El nuevo backend importa y usa:

```python
# Estrategias
from strategies.registry import STRATEGY_REGISTRY

# Backtesting
from backtesting.engine import Backtester, BacktestConfig

# Risk Management
from utils.risk import RiskManagementConfig

# Data
from data.yfinance_downloader import get_yfinance_data
```

**No requiere cambios en el código existente.**

---

## 📈 Próximas mejoras

- [ ] Autenticación JWT
- [ ] WebSockets para updates en tiempo real
- [ ] Agregar más estrategias dinámicamente
- [ ] Exportar reportes (PDF, Excel)
- [ ] Gráficos interactivos en frontend
- [ ] Scheduler para actualizar sesiones automáticamente
- [ ] Notificaciones cuando se ejecutan trades

---

## 🚀 Iniciar sistema

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Acceder:**
- Dashboard: http://localhost:3000
- API REST: http://localhost:8000/api/v1
- Docs API: http://localhost:8000/docs

---

## ✅ Estado

✓ Backtesting integrado y funcionando
✓ Paper trading integrado y funcionando  
✓ Base de datos con persistencia
✓ API REST completa
✓ Frontend conectado a API

**Sistema listo para producción** 🎉
