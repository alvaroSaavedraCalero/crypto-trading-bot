# 🤖 Crypto Trading Bot - Full Stack

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.104.1-green.svg)]()
[![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)]()

Sistema completo de trading algorítmico con:
- **Backend**: FastAPI con 17 endpoints REST
- **Frontend**: React + Vite con dashboard interactivo
- **Database**: SQLAlchemy ORM con 7 modelos
- **Backtesting**: Motor integrado con validación histórica
- **Paper Trading**: Simulación en tiempo real

---

## 📋 Tabla de Contenidos

- [🚀 Inicio Rápido](#-inicio-rápido)
- [🏗️ Arquitectura](#-arquitectura)
- [📁 Estructura](#-estructura)
- [🔧 Tecnologías](#-tecnologías)
- [📚 Documentación](#-documentación)
- [🧪 Testing](#-testing)
- [❓ Troubleshooting](#-troubleshooting)

---

## 🚀 Inicio Rápido

### Prerequisitos

- Python 3.10+
- Node.js 16+
- Git

### Setup (30 segundos)

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
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

> ⚠️ **Importante**: Lee [SETUP.md](SETUP.md) para instrucciones detalladas

---

## 🏗️ Arquitectura

```
Frontend (React)          Backend (FastAPI)         Database (SQLAlchemy)
─────────────────         ─────────────────         ──────────────────
  Dashboard          →      /api/v1/               →      SQLite/
  Strategies         →      - strategies           →      PostgreSQL
  Backtests          →      - backtests            →
  PaperTrading       →      - paper-trading   
                     →      - dashboard
                     →      (17 endpoints total)
```

### Flujo de Datos

1. **Frontend** → API (Axios)
2. **API** → Services (BacktestService, PaperTradingService)
3. **Services** → Existing Code (engine.py, strategies)
4. **Database** → Persistence (SQLAlchemy ORM)

---

## 📁 Estructura

```
crypto-trading-bot/
├── backend/                   # FastAPI Application
│   ├── app/
│   │   ├── main.py           # Entrada
│   │   ├── config.py         # Configuración
│   │   ├── database.py       # SQLAlchemy
│   │   ├── models/           # 7 Modelos ORM
│   │   ├── schemas/          # 5 Schemas Pydantic
│   │   ├── services/         # Lógica de negocio
│   │   ├── crud/             # Operaciones BD
│   │   └── api/routes/       # 17 Endpoints
│   └── requirements.txt       # Dependencias
│
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── components/       # Componentes
│   │   ├── pages/            # 4 Páginas
│   │   └── services/         # API Client
│   └── package.json
│
├── docs/                      # Documentación
│   ├── PROYECTO_COMPLETO.txt # Resumen
│   ├── ARCHITECTURE.md       # Diseño
│   ├── INTEGRATION_GUIDE.md  # Integración
│   └── ...
│
├── .venv/                     # (NO SUBIR A GIT)
├── .gitignore               # Configuración git
├── SETUP.md                 # Setup detallado
├── requirements.txt         # Dependencies
└── start_system.sh          # Script inicio
```

---

## 🔧 Tecnologías

### Backend
- **FastAPI** 0.104.1 - Framework web moderno
- **SQLAlchemy** 2.0.23 - ORM
- **Pydantic** 2.5.0 - Validación
- **Uvicorn** 0.24.0 - Servidor ASGI
- **yfinance** - Datos financieros

### Frontend
- **React** 18 - UI Library
- **Vite** 5 - Build tool
- **Axios** - HTTP Client
- **React Router** v6 - Routing

### Database
- **SQLite** (desarrollo)
- **PostgreSQL** (producción, opcional)

---

## 📚 Documentación

| Archivo | Contenido |
|---------|-----------|
| **[SETUP.md](SETUP.md)** | ⭐ Setup paso a paso |
| **[docs/PROYECTO_COMPLETO.txt](docs/PROYECTO_COMPLETO.txt)** | Resumen ejecutivo |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Diseño del sistema |
| **[docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** | Guía técnica |
| **[docs/INDICE.md](docs/INDICE.md)** | Índice de recursos |

---

## 🧪 Testing

### Ver Estado del Sistema

```bash
python STATUS_REPORT.py
```

Muestra:
- ✅/❌ Estado de componentes
- Endpoints disponibles
- Esquema de BD
- Próximos pasos

### Ejecutar Tests

```bash
source .venv/bin/activate
python test_integration.py
```

Tests:
- ✓ Backend API
- ✓ Database persistence
- ✓ Service integration

### Ver Ejemplos

```bash
python examples_usage.py
```

Ejemplos:
- Crear estrategia
- Ejecutar backtest
- Paper trading
- Ver estadísticas

---

## 🌐 API Endpoints (17)

### Health (3)
```
GET /health              Status del servidor
GET /health/ready        Readiness check
GET /health/live         Liveness check
```

### Strategies (5)
```
GET    /strategies       Listar todas
POST   /strategies       Crear nueva
GET    /strategies/{id}  Detalles
PUT    /strategies/{id}  Actualizar
DELETE /strategies/{id}  Eliminar
```

### Backtests (3)
```
GET    /backtests        Listar todos
POST   /backtests        Ejecutar nuevo
GET    /backtests/{id}   Ver resultados
```

### Paper Trading (4)
```
POST   /paper-trading           Crear sesión
GET    /paper-trading/{id}      Detalles
POST   /paper-trading/{id}/run  Ejecutar
GET    /paper-trading/{id}/trades
POST   /paper-trading/{id}/close
```

### Dashboard (2)
```
GET    /dashboard/stats   KPIs
GET    /dashboard/summary Resumen
```

**Documentación interactiva**: http://localhost:8000/docs

---

## 🔐 Configuración

### Backend (.env en backend/)

```env
DATABASE_URL=sqlite:///./trading_bot.db
DEBUG=True
SECRET_KEY=your-secret-key
API_PREFIX=/api/v1
```

### Frontend (.env en frontend/)

```env
VITE_API_URL=http://localhost:8000
```

---

## ❓ Troubleshooting

### "No module named fastapi"

```bash
# Verifica que .venv está activado
which python  # Debe estar en .venv/

# Si no, actívalo:
source .venv/bin/activate

# Reinstala:
pip install -r requirements.txt
```

### "Port 8000 already in use"

```bash
# Encuentra el proceso:
lsof -i :8000

# O usa otro puerto:
uvicorn app.main:app --port 8001
```

### Frontend no se conecta

1. Verifica backend en `http://localhost:8000`
2. Revisa `.env` del frontend
3. Abre DevTools (F12) en el navegador
4. Revisa Network tab para errores

---

## 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| Archivos | 50+ |
| LOC (Backend) | ~2000 |
| LOC (Frontend) | ~1500 |
| Endpoints | 17 |
| Modelos BD | 7 |
| Tests | 15+ |

---

## 📝 Notas Importantes

### Virtual Environment

❌ **NO subir** `.venv/` a Git (está en `.gitignore`)

Para reproducir en otra máquina:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Dependencias

Solo se necesita `requirements.txt` en la raíz. Contiene:
- Backend: FastAPI, SQLAlchemy, Pydantic, yfinance, pandas, etc.
- Frontend: Usa `npm install` en carpeta frontend/

---

## 🎯 Próximos Pasos

1. ✅ Leer [SETUP.md](SETUP.md)
2. ✅ Ejecutar `./start_system.sh`
3. ✅ Acceder a http://localhost:3000
4. ✅ Ver ejemplos: `python examples_usage.py`
5. 🚀 ¡Comenzar a usar!

---

## 📄 Licencia

MIT License - Ver LICENSE file

---

## 👤 Autor

Crypto Trading Bot - 2026

---

**Última actualización**: 26 de enero de 2026

¡El sistema está listo para producción! 🎉
