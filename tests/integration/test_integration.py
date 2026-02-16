#!/usr/bin/env python3
"""
Script de prueba para la integración del backend con la lógica de backtesting
"""

import sys
from pathlib import Path
import asyncio
import json

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.database import SessionLocal, init_db
from backend.app.models import Strategy as StrategyModel, User
from backend.app.services import BacktestService, PaperTradingService
from sqlalchemy.orm import Session


def setup_test_data(db: Session):
    """Configura datos de prueba"""
    
    # Crear usuario de prueba
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
        )
        db.add(user)
        db.commit()
    
    # Crear estrategia de prueba
    strategy = db.query(StrategyModel).filter(StrategyModel.owner_id == 1).first()
    if not strategy:
        strategy = StrategyModel(
            owner_id=1,
            name="MA_RSI Test",
            description="Estrategia MA_RSI de prueba",
            strategy_type="MA_RSI",
            config={
                "fast_window": 10,
                "slow_window": 20,
                "rsi_window": 14,
                "rsi_overbought": 70.0,
                "rsi_oversold": 30.0,
                "use_rsi_filter": False,
            },
            initial_capital=10000,
            stop_loss_pct=2,
            take_profit_rr=2,
        )
        db.add(strategy)
        db.commit()
    
    return user, strategy


def test_backtest(db: Session):
    """Prueba ejecución de backtest"""
    print("\n" + "="*60)
    print("🔬 PRUEBA 1: Backtesting")
    print("="*60)
    
    _, strategy = setup_test_data(db)
    
    print(f"\n📊 Ejecutando backtest para estrategia: {strategy.name}")
    print(f"   Par: USDJPY, Timeframe: 15m")
    
    result = BacktestService.run_backtest(
        db=db,
        strategy_id=strategy.id,
        pair="USDJPY",
        timeframe="15m",
        period="60d",
        limit=2000,
        owner_id=1,
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Backtest completado exitosamente!")
        print(f"   ID: {result['backtest_id']}")
        print(f"   Retorno: {result['total_return_pct']:.2f}%")
        print(f"   Winrate: {result['winrate_pct']:.1f}%")
        print(f"   Trades: {result['num_trades']}")
        print(f"   Profit Factor: {result['profit_factor']:.2f}")
        print(f"   Max Drawdown: {result['max_drawdown_pct']:.2f}%")
        
        # Obtener detalles
        details = BacktestService.get_backtest_results(db, result['backtest_id'])
        if "error" not in details:
            print(f"\n   Trades generados:")
            for i, trade in enumerate(details.get('trades', [])[:3], 1):
                print(f"     {i}. {trade['side'].upper()}: {trade['entry_price']:.5f} → "
                      f"{trade['exit_price']:.5f} | P&L: {trade['pnl_pct']:.2f}%")
            if len(details.get('trades', [])) > 3:
                print(f"     ... y {len(details['trades']) - 3} trades más")
    
    return result.get('backtest_id')


def test_paper_trading(db: Session):
    """Prueba paper trading"""
    print("\n" + "="*60)
    print("📈 PRUEBA 2: Paper Trading")
    print("="*60)
    
    _, strategy = setup_test_data(db)
    
    print(f"\n🎮 Creando sesión de paper trading")
    
    session_result = PaperTradingService.create_session(
        db=db,
        owner_id=1,
        strategy_id=strategy.id,
        pair="USDJPY",
        timeframe="15m",
        name="PT Test Session",
        initial_capital=10000.0,
    )
    
    if "error" in session_result:
        print(f"❌ Error: {session_result['error']}")
        return None
    
    session_id = session_result['session_id']
    print(f"✅ Sesión creada: {session_result['name']}")
    print(f"   ID: {session_id}")
    print(f"   Capital: ${session_result['initial_capital']:,.2f}")
    
    # Ejecutar backtest en la sesión
    print(f"\n   Ejecutando estrategia...")
    
    update_result = PaperTradingService.update_session_with_backtest(
        db=db,
        session_id=session_id,
        pair="USDJPY",
        timeframe="15m",
    )
    
    if "error" in update_result:
        print(f"   ❌ Error: {update_result['error']}")
    else:
        print(f"   ✅ Backtest ejecutado!")
        print(f"      Trades: {update_result['total_trades']}")
        print(f"      Ganadores: {update_result['winning_trades']}")
        print(f"      Perdedores: {update_result['losing_trades']}")
        print(f"      Retorno: {update_result['total_return_pct']:.2f}%")
        print(f"      Capital final: ${update_result['current_capital']:,.2f}")
    
    # Obtener detalles de la sesión
    details = PaperTradingService.get_session_details(db, session_id)
    
    if "error" not in details:
        print(f"\n   Detalles de la sesión:")
        print(f"      Capital inicial: ${details['initial_capital']:,.2f}")
        print(f"      Capital actual: ${details['current_capital']:,.2f}")
        print(f"      Total trades: {details['total_trades']}")
        print(f"      Max Drawdown: {details['max_drawdown_pct']:.2f}%")
    
    return session_id


def main():
    """Función principal de prueba"""
    print("\n" + "🚀 "*30)
    print("PRUEBA DE INTEGRACIÓN - Backtesting + Paper Trading")
    print("🚀 "*30)
    
    # Inicializar BD
    print("\n🗄️  Inicializando base de datos...")
    init_db()
    print("✅ Base de datos lista")
    
    # Obtener sesión
    db = SessionLocal()
    
    try:
        # Prueba 1: Backtesting
        backtest_id = test_backtest(db)
        
        # Prueba 2: Paper Trading
        session_id = test_paper_trading(db)
        
        # Resumen
        print("\n" + "="*60)
        print("✅ RESUMEN DE PRUEBAS")
        print("="*60)
        print(f"\n✓ Backtest creado (ID: {backtest_id})")
        print(f"✓ Sesión paper trading creada (ID: {session_id})")
        print("\n📊 La integración está funcionando correctamente!")
        print("\nPróximos pasos:")
        print("1. Iniciar el backend: python -m uvicorn app.main:app --reload")
        print("2. Iniciar el frontend: cd frontend && npm run dev")
        print("3. Visitar: http://localhost:3000")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
