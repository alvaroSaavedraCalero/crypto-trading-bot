#!/bin/bash

# Script para probar la funcionalidad del bot de trading
# Uso: ./test_bot.sh [opción]

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio del proyecto
PROJECT_DIR="/Users/elsavedrita/Desktop/crypto-trading-bot"
cd "$PROJECT_DIR"

# Activar entorno virtual
source .venv/bin/activate

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

echo -e "${BLUE}=== Crypto Trading Bot - Test Suite ===${NC}\n"

# Función para mostrar el menú
show_menu() {
    echo "Selecciona una opción:"
    echo "1) Backtest de todas las estrategias"
    echo "2) Paper trading (MA_RSI en BTC/USDT)"
    echo "3) Validación cruzada (Squeeze Momentum)"
    echo "4) Test rápido de componentes"
    echo "5) Ejecutar todos los tests"
    echo "0) Salir"
    echo ""
}

# Función para backtest
run_backtest() {
    echo -e "${GREEN}Ejecutando backtest de todas las estrategias...${NC}\n"
    python scripts/backtest_strategies.py
}

# Función para paper trading
run_paper() {
    echo -e "${GREEN}Ejecutando paper trading...${NC}\n"
    python scripts/paper_runner.py
}

# Función para validación cruzada
run_validation() {
    echo -e "${GREEN}Ejecutando validación cruzada...${NC}\n"
    python validation/validate_squezze_momentum.py
}

# Función para test rápido
run_quick_test() {
    echo -e "${GREEN}Ejecutando tests rápidos...${NC}\n"
    
    echo "1. Verificando versión de Python..."
    python --version
    
    echo -e "\n2. Verificando dependencias principales..."
    pip list | grep -E "(ccxt|pandas|numpy|matplotlib|ta)" | head -6
    
    echo -e "\n3. Test de registry de estrategias..."
    python -c "from strategies.registry import create_strategy; from config.settings import MA_RSI_BTC15M_CONFIG; s = create_strategy('MA_RSI', MA_RSI_BTC15M_CONFIG); print('✓ Strategy registry OK')"
    
    echo -e "\n4. Test de descarga de datos..."
    python -c "from data.downloader import get_datos_cripto_cached; df = get_datos_cripto_cached('BTC/USDT', '15m', 100, False); print(f'✓ Data downloader OK: {len(df)} filas cargadas')"
    
    echo -e "\n${GREEN}✅ Todos los tests rápidos completados${NC}"
}

# Función para ejecutar todos los tests
run_all() {
    echo -e "${BLUE}=== Ejecutando suite completa de tests ===${NC}\n"
    run_quick_test
    echo -e "\n${BLUE}========================================${NC}\n"
    run_backtest
    echo -e "\n${BLUE}========================================${NC}\n"
    run_paper
    echo -e "\n${BLUE}========================================${NC}\n"
    run_validation
    echo -e "\n${GREEN}✅ Suite completa de tests finalizada${NC}"
}

# Si se pasa un argumento, ejecutar directamente
if [ $# -eq 1 ]; then
    case $1 in
        1|backtest)
            run_backtest
            ;;
        2|paper)
            run_paper
            ;;
        3|validation)
            run_validation
            ;;
        4|quick)
            run_quick_test
            ;;
        5|all)
            run_all
            ;;
        *)
            echo -e "${RED}Opción no válida${NC}"
            show_menu
            ;;
    esac
else
    # Modo interactivo
    while true; do
        show_menu
        read -p "Opción: " option
        
        case $option in
            1)
                run_backtest
                ;;
            2)
                run_paper
                ;;
            3)
                run_validation
                ;;
            4)
                run_quick_test
                ;;
            5)
                run_all
                ;;
            0)
                echo -e "${BLUE}Saliendo...${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opción no válida${NC}"
                ;;
        esac
        
        echo -e "\n${BLUE}========================================${NC}\n"
    done
fi
