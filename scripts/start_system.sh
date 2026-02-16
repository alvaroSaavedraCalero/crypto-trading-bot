#!/bin/bash

# Script para iniciar el sistema completo
# Uso: ./scripts/start_system.sh (from project root)

# Navigate to project root (parent of scripts/)
cd "$(dirname "$0")/.." || exit 1

echo "🚀 Iniciando Crypto Trading Bot Full Stack"
echo "=========================================="

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para manejar errores
handle_error() {
    echo -e "${RED}❌ Error: $1${NC}"
    exit 1
}

# 1. Configuración de Python
echo -e "${BLUE}🔍 Verificando entorno Python...${NC}"

# Buscar una versión compatible de Python (3.10 - 3.12)
PYTHON_CMD=""
for cmd in python3.10 python3.11 python3.12; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        echo -e "${GREEN}✅ Encontrado: $PYTHON_CMD${NC}"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    handle_error "No se encontró Python 3.10, 3.11 o 3.12. Por favor instala una versión compatible."
fi

# Configurar entorno virtual
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Creando entorno virtual con $PYTHON_CMD...${NC}"
    $PYTHON_CMD -m venv .venv || handle_error "Falló la creación del entorno virtual"
fi

# Activar entorno virtual
source .venv/bin/activate || handle_error "No se pudo activar el entorno virtual"
echo -e "${GREEN}✅ Entorno virtual activo${NC}"

# Verificar pip
if ! command -v pip &> /dev/null; then
    handle_error "pip no está disponible en el entorno virtual"
fi

# 2. Configuración Backend
echo "------------------------------------------"
echo -e "${BLUE}📦 Instalando dependencias del Backend...${NC}"
pip install -r backend/requirements.txt > /dev/null 2>&1 || handle_error "Falló la instalación de dependencias del backend"
echo -e "${GREEN}✅ Dependencias backend instaladas${NC}"

echo -e "${BLUE}🔥 Iniciando Backend en puerto 8000...${NC}"
# Asegurarnos de estar en la raíz para ejecutar el módulo correctamente
python -m uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0 > backend.log 2>&1 &
BACKEND_PID=$!

# Esperar un momento para ver si arranca
sleep 3
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}❌ El backend falló al iniciar. Revisa backend.log para más detalles.${NC}"
    head -n 20 backend.log
    exit 1
fi

# 3. Configuración Frontend
echo "------------------------------------------"
echo -e "${BLUE}📦 Instalando dependencias del Frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install > /dev/null 2>&1 || handle_error "Falló npm install"
fi

echo -e "${BLUE}🎨 Iniciando Frontend en puerto 3000...${NC}"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 4. Resumen
echo "=========================================="
echo -e "${GREEN}✅ Sistema iniciado correctamente!${NC}"
echo "=========================================="
echo ""
echo "📍 URLs disponibles:"
echo "   🎨 Frontend:  http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   - Backend:  cat backend.log"
echo "   - Frontend: cat frontend.log"
echo ""
echo "⌨️  Presiona Ctrl+C para detener el sistema"
echo ""

# Función de limpieza al salir
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Deteniendo servicios...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT

# Esperar a que se terminen los procesos
wait $BACKEND_PID $FRONTEND_PID
