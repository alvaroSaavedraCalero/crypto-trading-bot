#!/bin/bash

# Script para iniciar el sistema completo
# Uso: ./start_system.sh

echo "🚀 Iniciando Crypto Trading Bot Full Stack"
echo "=========================================="

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    exit 1
fi

# Verificar si Node está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado"
    exit 1
fi

# Backend
echo -e "${BLUE}📦 Instalando dependencias del backend...${NC}"
cd backend
pip install -r requirements.txt > /dev/null 2>&1

echo -e "${GREEN}✅ Backend listo${NC}"
echo -e "${BLUE}Iniciando backend en puerto 8000...${NC}"
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
echo -e "${BLUE}📦 Instalando dependencias del frontend...${NC}"
cd ../frontend
npm install > /dev/null 2>&1

echo -e "${GREEN}✅ Frontend listo${NC}"
echo -e "${BLUE}Iniciando frontend en puerto 3000...${NC}"
npm run dev &
FRONTEND_PID=$!

cd ..

# Mostrar información
sleep 2
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Sistema iniciado correctamente!${NC}"
echo "=========================================="
echo ""
echo "📍 URLs disponibles:"
echo "   🎨 Frontend:  http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "⌨️  Presiona Ctrl+C para detener el sistema"
echo ""

# Esperar a que se terminen los procesos
wait $BACKEND_PID $FRONTEND_PID
