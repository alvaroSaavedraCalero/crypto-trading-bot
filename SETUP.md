# 🚀 Setup - Crypto Trading Bot

Guía paso a paso para configurar el proyecto correctamente.

---

## 📋 Prerequisitos

- Python 3.10 o superior
- Node.js 16 o superior (para el frontend)
- Git
- Terminal/CMD

---

## 🔧 Setup Inicial

### 1. Clonar el Repositorio

```bash
git clone <tu-repo-url>
cd crypto-trading-bot
```

### 2. Crear Virtual Environment (Python)

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

Deberías ver `(.venv)` al inicio de tu terminal.

### 3. Instalar Dependencias Backend

Con el `.venv` activado:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias que se instalan:**
- `fastapi` - Framework web moderno
- `uvicorn` - Servidor ASGI
- `sqlalchemy` - ORM para base de datos
- `pydantic` - Validación de datos
- `python-dotenv` - Variables de entorno
- `psutil` - Información del sistema
- `pandas` - Procesamiento de datos
- `yfinance` - Descarga de datos financieros
- `ta` - Indicadores técnicos
- `requests` - HTTP client

### 4. Instalar Dependencias Frontend

```bash
cd frontend
npm install
cd ..
```

---

## 🎯 Estructura del Proyecto

Después del setup, la estructura es limpia y organizada:

```
crypto-trading-bot/
├── .venv/                    ← Virtual environment (IGNORADO en git)
├── backend/                  ← API FastAPI
│   ├── app/
│   │   ├── main.py          ← Aplicación
│   │   ├── config.py        ← Configuración
│   │   ├── database.py      ← Base de datos
│   │   ├── models/          ← Modelos ORM (7)
│   │   ├── schemas/         ← Validación (Pydantic)
│   │   ├── services/        ← Lógica de negocio
│   │   ├── crud/            ← Operaciones BD
│   │   └── api/routes/      ← Endpoints (17)
│   └── requirements.txt      ← Dependencias
│
├── frontend/                 ← Aplicación React
│   ├── src/
│   │   ├── components/      ← Componentes reutilizables
│   │   ├── pages/           ← Páginas principales
│   │   └── services/        ← Cliente API
│   ├── package.json
│   └── vite.config.js
│
├── docs/                     ← Documentación
│   ├── PROYECTO_COMPLETO.txt
│   ├── ARCHITECTURE.md
│   ├── INTEGRATION_GUIDE.md
│   └── ...
│
├── .gitignore               ← Archivos a ignorar
├── .venv/                   ← (NO SUBIR A GIT)
├── pyproject.toml
├── README.md
├── SETUP.md                 ← Este archivo
├── STATUS_REPORT.py         ← Verificar estado
├── examples_usage.py        ← Ejemplos de uso
├── test_integration.py      ← Tests
└── start_system.sh          ← Script de inicio
```

---

## 🚀 Ejecutar el Proyecto

### Opción 1: Script Automático (Recomendado)

```bash
chmod +x start_system.sh
./start_system.sh
```

Este script:
- ✓ Activa `.venv`
- ✓ Inicia backend (puerto 8000)
- ✓ Inicia frontend (puerto 3000)

### Opción 2: Manual (2 Terminales)

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate    # macOS/Linux
# o: .venv\Scripts\activate  # Windows

cd backend
python -m uvicorn app.main:app --reload
```

Deberías ver: `Uvicorn running on http://127.0.0.1:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Deberías ver: `Local: http://localhost:5173` o `3000`

---

## 🌐 Acceso a la Aplicación

Una vez corriendo:

| Componente | URL |
|-----------|-----|
| Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Health Check | http://localhost:8000/health |
| API Base | http://localhost:8000/api/v1 |

---

## ✅ Verificar Setup

### 1. Verificar Backend

```bash
source .venv/bin/activate
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
```

Debería imprimirse: `FastAPI 0.104.1`

### 2. Verificar Base de Datos

```bash
source .venv/bin/activate
python -c "from backend.app.database import init_db; init_db(); print('✓ DB initialized')"
```

### 3. Verificar Frontend

```bash
cd frontend && npm list react
```

Debería mostrar React instalado.

### 4. Ver Status Completo

```bash
python STATUS_REPORT.py
```

Mostrará el estado de todos los componentes.

---

## 🧪 Ejecutar Tests

```bash
source .venv/bin/activate
python test_integration.py
```

Esto ejecuta tests end-to-end de:
- ✓ Backend API
- ✓ Base de datos
- ✓ Servicios
- ✓ Integración

---

## 📚 Ver Ejemplos de Uso

```bash
source .venv/bin/activate
python examples_usage.py
```

Esto ejecuta 4 ejemplos completos de cómo usar la API.

---

## 🔐 Configuración

### Backend (.env)

Crea `.env` en la carpeta `backend/` con:

```env
# Base de datos
DATABASE_URL=sqlite:///./trading_bot.db
# O para PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/trading_bot

# Debug
DEBUG=True

# API
SECRET_KEY=your-secret-key-here
API_PREFIX=/api/v1
```

### Frontend (.env)

Crea `.env` en la carpeta `frontend/` con:

```env
VITE_API_URL=http://localhost:8000
```

---

## 🧹 Mantener .venv Limpio

### ¿Por qué no subir .venv a git?

El `.venv/` está en `.gitignore` porque:
- ✓ Ocupa mucho espacio (~500MB+)
- ✓ Contiene binarios específicos del SO
- ✓ Cada usuario crea el suyo
- ✓ Solo `requirements.txt` es necesario

### Reproducir .venv en otra máquina

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Eso es todo. No necesitas copiar el `.venv` original.

---

## ❌ Problemas Comunes

### "No module named fastapi"

**Solución:**
```bash
# Verifica que .venv está activado
which python  # macOS/Linux
# o: where python  # Windows

# Deberían mostrar la ruta dentro de .venv/

# Si no, actívalo:
source .venv/bin/activate  # macOS/Linux
# o: .venv\Scripts\activate  # Windows

# Reinstala
pip install -r requirements.txt
```

### "Port 8000/3000 already in use"

**Solución:**
```bash
# Encuentra el proceso:
lsof -i :8000  # macOS/Linux
# o: netstat -ano | findstr :8000  # Windows

# Mata el proceso o usa otro puerto:
uvicorn app.main:app --port 8001
```

### Frontend no se conecta al backend

**Verificar:**
1. Backend está corriendo en `http://localhost:8000`
2. CORS está habilitado (debería estarlo)
3. `.env` del frontend tiene `VITE_API_URL=http://localhost:8000`
4. Revisa la consola del navegador (F12) para errores

---

## 📖 Documentación

Todos los archivos de documentación están en `/docs`:

- **[PROYECTO_COMPLETO.txt](../docs/PROYECTO_COMPLETO.txt)** - Resumen completo
- **[ARCHITECTURE.md](../docs/ARCHITECTURE.md)** - Diseño del sistema
- **[INTEGRATION_GUIDE.md](../docs/INTEGRATION_GUIDE.md)** - Detalles técnicos
- **[INDICE.md](../docs/INDICE.md)** - Índice de recursos

---

## 🎯 Próximos Pasos

1. ✅ Completar setup (tú estás aquí)
2. ✅ Ejecutar `STATUS_REPORT.py` para verificar
3. ✅ Ejecutar `test_integration.py` para probar
4. ✅ Acceder a http://localhost:3000
5. 🚀 ¡Comenzar a usar el bot!

---

## 💡 Tips

### Actualizar dependencias (seguro)

```bash
pip install --upgrade -r requirements.txt
```

### Ver qué se instaló

```bash
pip list
```

### Usar venv en VSCode

1. Abre VSCode
2. `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows)
3. Busca "Python: Select Interpreter"
4. Elige `./.venv/bin/python`

Ahora VSCode usará automáticamente el venv.

### Desactivar venv

```bash
deactivate
```

---

## ❓ ¿Necesitas ayuda?

1. Revisa `/docs/INDICE.md`
2. Ejecuta `STATUS_REPORT.py` para diagnosticar
3. Revisa los logs en el terminal
4. Abre un issue en GitHub

---

**Última actualización**: 26 de enero de 2026

¡El sistema está listo para desarrollar! 🎉
