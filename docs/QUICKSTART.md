# 🚀 Guía Rápida - Crypto Trading Bot Full Stack

## Resumen

He creado una arquitectura completa con:
- ✅ **Backend API REST** con FastAPI + SQLAlchemy
- ✅ **Frontend Dashboard** con React + Vite
- ✅ **Base de datos** con modelos ORM completos
- ✅ **Documentación** de arquitectura y guías

## 📁 Estructura creada

```
crypto-trading-bot/
├── backend/                          # 🔧 API REST
│   ├── app/
│   │   ├── models/                  # 7 tablas ORM
│   │   │   ├── user.py
│   │   │   ├── strategy.py
│   │   │   ├── backtest_run.py
│   │   │   ├── backtest_trade.py
│   │   │   ├── paper_trading_session.py
│   │   │   └── paper_trade.py
│   │   ├── schemas/                 # Pydantic validation
│   │   ├── crud/                    # CRUD operations (extensible)
│   │   ├── api/
│   │   │   └── routes/              # Endpoints
│   │   │       ├── strategies.py
│   │   │       ├── backtests.py
│   │   │       └── paper_trading.py
│   │   ├── services/                # Lógica de negocio
│   │   ├── config.py                # Settings
│   │   ├── database.py              # Conexión BD
│   │   └── main.py                  # Aplicación FastAPI
│   ├── requirements.txt
│   ├── README.md
│   └── main.py                      # Entry point
│
├── frontend/                         # 🎨 Dashboard React
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx           # Layout + navbar
│   │   │   └── Sidebar.jsx          # Barra lateral
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Inicio (stats, KPIs)
│   │   │   ├── Strategies.jsx       # Gestión de estrategias
│   │   │   ├── Backtests.jsx        # Historial backtests
│   │   │   └── PaperTrading.jsx     # Sesiones trading
│   │   ├── services/
│   │   │   └── api.js               # Cliente API
│   │   ├── App.jsx                  # Router
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── README.md
│
├── ARCHITECTURE.md                   # 📋 Documentación completa
└── QUICKSTART.md                     # Este archivo
```

## 🎯 Base de datos

Se crean automáticamente 6 tablas:

| Tabla | Propósito | Campos principales |
|-------|-----------|-------------------|
| **users** | Usuarios sistema | username, email, is_active |
| **strategies** | Definiciones | name, strategy_type, config |
| **backtest_runs** | Ejecuciones | pair, timeframe, results |
| **backtest_trades** | Trades en BT | entry/exit prices, pnl |
| **paper_trading_sessions** | Simulaciones | pair, capital, trades |
| **paper_trades** | Trades en PT | entry/exit, pnl (real-time) |

## ⚡ Inicio rápido

### Opción 1: Con SQLite (más simple)

#### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- DB: `trading_bot.db` (se crea automáticamente)

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
- Dashboard: http://localhost:3000

### Opción 2: Con PostgreSQL (producción)

#### Crear base de datos
```bash
psql -U postgres
CREATE DATABASE trading_bot;
```

#### Backend con PostgreSQL
```bash
cd backend
pip install -r requirements.txt

# Crear .env
echo "DATABASE_URL=postgresql://user:password@localhost/trading_bot" > .env

python -m uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 API Endpoints

### Health
```
GET  /api/v1/health
```

### Estrategias
```
GET    /api/v1/strategies              # Listar todas
POST   /api/v1/strategies              # Crear nueva
GET    /api/v1/strategies/{id}         # Obtener detalle
PUT    /api/v1/strategies/{id}         # Actualizar
DELETE /api/v1/strategies/{id}         # Eliminar
```

### Backtests
```
GET  /api/v1/backtests                 # Listar
POST /api/v1/backtests                 # Ejecutar nuevo
GET  /api/v1/backtests/{id}            # Obtener resultados
```

### Paper Trading
```
GET  /api/v1/paper-trading             # Listar sesiones
POST /api/v1/paper-trading             # Crear sesión
GET  /api/v1/paper-trading/{id}        # Obtener sesión
GET  /api/v1/paper-trading/{id}/trades # Obtener trades
```

## 🎨 Páginas Frontend

1. **Dashboard** - KPIs, estadísticas, estado de la API
2. **Estrategias** - Crear, listar, editar estrategias
3. **Backtests** - Tabla de resultados de backtests
4. **Paper Trading** - Monitoreo de sesiones activas

## 🔗 Integración con código existente

Tu código existente (backtesting, optimización, trading) puede integrarse:

```python
# backend/app/services/backtest_service.py

from backtesting.engine import Backtester
from optimization.optimize_ma_rsi import optimize_ma_rsi

async def run_backtest(strategy_id: int, pair: str):
    # Obtener configuración de BD
    strategy = db.query(Strategy).get(strategy_id)
    
    # Usar código existente
    backtester = Backtester(config)
    results = backtester.backtest(df)
    
    # Guardar resultados en BD
    backtest_run = BacktestRun(
        strategy_id=strategy_id,
        pair=pair,
        total_return_pct=results.return,
        # ... más campos
    )
    db.add(backtest_run)
    db.commit()
    
    return backtest_run
```

## 📝 Próximas mejoras (TODO)

- [ ] Conectar lógica de backtesting real
- [ ] Conectar paper trading en tiempo real
- [ ] Autenticación JWT
- [ ] WebSockets para updates en tiempo real
- [ ] Gráficos interactivos (candlestick, equity curve)
- [ ] Exportar reportes (PDF, Excel)
- [ ] Tests unitarios e integración
- [ ] Docker + Docker Compose
- [ ] CI/CD pipeline

## 🐛 Troubleshooting

### Error: "Cannot find module react"
```bash
cd frontend
npm install
```

### Error: "ModuleNotFoundError: No module named 'fastapi'"
```bash
cd backend
pip install -r requirements.txt
```

### Error: "Port already in use"
```bash
# Backend en puerto diferente
uvicorn app.main:app --reload --port 8001

# Frontend en puerto diferente
npm run dev -- --port 3001
```

### Database no se crea
- SQLite se crea automáticamente en `backend/trading_bot.db`
- PostgreSQL: verificar `DATABASE_URL` en `.env`

## 📚 Documentación

- [ARCHITECTURE.md](ARCHITECTURE.md) - Diseño completo
- [backend/README.md](backend/README.md) - Guía backend
- [frontend/README.md](frontend/README.md) - Guía frontend

## 💡 Tips

1. **Desarrollo**: Mantener backend y frontend en terminales separadas
2. **Hot reload**: Ambos tienen hot reload automático
3. **API docs**: Visita http://localhost:8000/docs mientras desarrollas
4. **Browser DevTools**: Usa para debugging del frontend
5. **SQLite Studio**: Tool gratuito para explorar la BD

## 🎯 Siguientes pasos

1. **Probar el sistema**:
   - Iniciar backend
   - Iniciar frontend
   - Navegar por el dashboard
   - Ver en http://localhost:8000/docs

2. **Integrar lógica existente**:
   - Crear servicio para backtesting
   - Crear servicio para optimización
   - Crear servicio para paper trading

3. **Agregar autenticación**:
   - Implementar JWT en backend
   - Agregar login en frontend

4. **Deploy**:
   - Containerizar con Docker
   - Desplegar en servidor

---

¡El sistema está listo para empezar a desarrollar! 🚀
