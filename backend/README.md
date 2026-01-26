# Crypto Trading Bot API

Backend API REST para el sistema de trading automático.

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones (cuando existan)
alembic upgrade head
```

## Ejecución

```bash
# Desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Acceso

- **API REST**: http://localhost:8000
- **Documentación interactiva (Swagger)**: http://localhost:8000/docs
- **Documentación alternativa (ReDoc)**: http://localhost:8000/redoc

## Estructura

```
backend/
├── app/
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # Esquemas Pydantic
│   ├── crud/            # Operaciones CRUD
│   ├── api/
│   │   └── routes/      # Endpoints API
│   ├── services/        # Lógica de negocio
│   ├── config.py        # Configuración
│   ├── database.py      # Conexión a BD
│   └── main.py          # Aplicación FastAPI
├── requirements.txt
└── main.py              # Punto de entrada
```

## Endpoints principales

### Salud
- `GET /api/v1/health` - Verificar estado de la API

### Estrategias
- `GET /api/v1/strategies` - Listar estrategias
- `POST /api/v1/strategies` - Crear estrategia
- `GET /api/v1/strategies/{id}` - Obtener estrategia
- `PUT /api/v1/strategies/{id}` - Actualizar estrategia
- `DELETE /api/v1/strategies/{id}` - Eliminar estrategia

### Backtests
- `GET /api/v1/backtests` - Listar backtests
- `POST /api/v1/backtests` - Ejecutar backtest
- `GET /api/v1/backtests/{id}` - Obtener resultados

### Paper Trading
- `GET /api/v1/paper-trading` - Listar sesiones
- `POST /api/v1/paper-trading` - Crear sesión
- `GET /api/v1/paper-trading/{id}` - Obtener sesión
- `GET /api/v1/paper-trading/{id}/trades` - Obtener trades

## Configuración

Variables de entorno (crear `.env`):

```env
DATABASE_URL=sqlite:///./trading_bot.db
# O para PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/trading_bot

DEBUG=False
SECRET_KEY=your-secret-key-here
API_PREFIX=/api/v1
```

## Base de datos

La aplicación usa SQLAlchemy y soporta:
- **SQLite** (por defecto, ideal para desarrollo)
- **PostgreSQL** (recomendado para producción)

Las tablas se crean automáticamente al iniciar la aplicación.
