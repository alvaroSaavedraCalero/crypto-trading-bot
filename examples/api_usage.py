#!/usr/bin/env python3
"""
📖 Ejemplos de uso del sistema integrado
"""

import requests
import json
from typing import Dict, Any

# Configuración
API_URL = "http://localhost:8000/api/v1"
OWNER_ID = 1  # Por defecto


class TradingBotClient:
    """Cliente para interactuar con el Trading Bot API"""
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
    
    # ========== Estrategias ==========
    
    def create_strategy(self, name: str, strategy_type: str, config: Dict) -> Dict[str, Any]:
        """Crea una nueva estrategia"""
        response = requests.post(
            f"{self.base_url}/strategies",
            json={
                "name": name,
                "strategy_type": strategy_type,
                "config": config,
                "description": f"Estrategia {strategy_type}",
            }
        )
        return response.json()
    
    def list_strategies(self) -> list:
        """Lista todas las estrategias"""
        response = requests.get(f"{self.base_url}/strategies")
        return response.json()
    
    def get_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Obtiene una estrategia específica"""
        response = requests.get(f"{self.base_url}/strategies/{strategy_id}")
        return response.json()
    
    # ========== Backtests ==========
    
    def run_backtest(self, strategy_id: int, pair: str, timeframe: str = "15m") -> Dict[str, Any]:
        """Ejecuta un backtest"""
        response = requests.post(
            f"{self.base_url}/backtests",
            params={
                "strategy_id": strategy_id,
                "pair": pair,
                "timeframe": timeframe,
            }
        )
        return response.json()
    
    def get_backtest_results(self, backtest_id: int) -> Dict[str, Any]:
        """Obtiene resultados de un backtest"""
        response = requests.get(f"{self.base_url}/backtests/{backtest_id}")
        return response.json()
    
    # ========== Paper Trading ==========
    
    def create_paper_trading_session(
        self,
        strategy_id: int,
        pair: str,
        timeframe: str = "15m",
        name: str = None
    ) -> Dict[str, Any]:
        """Crea una sesión de paper trading"""
        response = requests.post(
            f"{self.base_url}/paper-trading",
            json={
                "strategy_id": strategy_id,
                "pair": pair,
                "timeframe": timeframe,
                "name": name or f"Session {pair}",
            }
        )
        return response.json()
    
    def run_paper_trading_session(self, session_id: int, pair: str) -> Dict[str, Any]:
        """Ejecuta una sesión de paper trading"""
        response = requests.post(
            f"{self.base_url}/paper-trading/{session_id}/run",
            params={"pair": pair}
        )
        return response.json()
    
    def get_paper_trading_session(self, session_id: int) -> Dict[str, Any]:
        """Obtiene detalles de una sesión"""
        response = requests.get(f"{self.base_url}/paper-trading/{session_id}")
        return response.json()
    
    def get_paper_trading_trades(self, session_id: int) -> list:
        """Obtiene todos los trades de una sesión"""
        response = requests.get(f"{self.base_url}/paper-trading/{session_id}/trades")
        return response.json()
    
    def close_paper_trading_session(self, session_id: int) -> Dict[str, Any]:
        """Cierra una sesión"""
        response = requests.post(f"{self.base_url}/paper-trading/{session_id}/close")
        return response.json()
    
    # ========== Dashboard ==========
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del dashboard"""
        response = requests.get(f"{self.base_url}/dashboard/stats")
        return response.json()
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del dashboard"""
        response = requests.get(f"{self.base_url}/dashboard/summary")
        return response.json()


def example_1_basic_backtest():
    """Ejemplo 1: Ejecutar un backtest simple"""
    print("\n" + "="*60)
    print("EJEMPLO 1: Backtest simple")
    print("="*60)
    
    client = TradingBotClient()
    
    # 1. Crear estrategia
    print("\n1️⃣ Creando estrategia MA_RSI...")
    strategy = client.create_strategy(
        name="MA_RSI Strategy",
        strategy_type="MA_RSI",
        config={
            "fast_window": 10,
            "slow_window": 20,
            "rsi_window": 14,
            "rsi_overbought": 70.0,
            "rsi_oversold": 30.0,
        }
    )
    strategy_id = strategy['id']
    print(f"   ✓ Estrategia creada con ID: {strategy_id}")
    
    # 2. Ejecutar backtest
    print(f"\n2️⃣ Ejecutando backtest en USDJPY...")
    backtest = client.run_backtest(strategy_id, "USDJPY", "15m")
    
    if "error" in backtest:
        print(f"   ❌ Error: {backtest['error']}")
    else:
        backtest_id = backtest['backtest_id']
        print(f"   ✓ Backtest ejecutado con ID: {backtest_id}")
        print(f"     Retorno: {backtest['total_return_pct']:.2f}%")
        print(f"     Trades: {backtest['num_trades']}")
        print(f"     Winrate: {backtest['winrate_pct']:.1f}%")
    
    # 3. Obtener resultados detallados
    print(f"\n3️⃣ Obteniendo resultados...")
    results = client.get_backtest_results(backtest_id)
    
    if "trades" in results:
        print(f"   Trades generados: {len(results['trades'])}")
        for i, trade in enumerate(results['trades'][:3], 1):
            print(f"     {i}. {trade['side'].upper()}: ${trade['entry_price']:.4f} "
                  f"→ ${trade['exit_price']:.4f} | "
                  f"P&L: {trade['pnl_pct']:.2f}%")


def example_2_paper_trading():
    """Ejemplo 2: Paper trading completo"""
    print("\n" + "="*60)
    print("EJEMPLO 2: Paper Trading")
    print("="*60)
    
    client = TradingBotClient()
    
    # 1. Obtener o crear estrategia
    print("\n1️⃣ Obteniendo estrategias...")
    strategies = client.list_strategies()
    
    if not strategies:
        print("   No hay estrategias, creando una...")
        strategy = client.create_strategy(
            name="KELTNER Strategy",
            strategy_type="KELTNER",
            config={
                "kc_window": 25,
                "kc_mult": 2.5,
                "atr_window": 20,
            }
        )
        strategy_id = strategy['id']
    else:
        strategy_id = strategies[0]['id']
        print(f"   ✓ Usando estrategia: {strategies[0]['name']}")
    
    # 2. Crear sesión
    print(f"\n2️⃣ Creando sesión de paper trading...")
    session = client.create_paper_trading_session(
        strategy_id=strategy_id,
        pair="USDJPY",
        name="My Trading Session"
    )
    
    if "error" in session:
        print(f"   ❌ Error: {session['error']}")
        return
    
    session_id = session['session_id']
    print(f"   ✓ Sesión creada con ID: {session_id}")
    print(f"     Capital: ${session['initial_capital']:,.2f}")
    
    # 3. Ejecutar sesión
    print(f"\n3️⃣ Ejecutando estrategia en sesión...")
    result = client.run_paper_trading_session(session_id, "USDJPY")
    
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✓ Estrategia ejecutada!")
        print(f"     Trades: {result['total_trades']}")
        print(f"     Ganadores: {result['winning_trades']}")
        print(f"     Perdedores: {result['losing_trades']}")
        print(f"     Retorno: {result['total_return_pct']:.2f}%")
        print(f"     Capital final: ${result['current_capital']:,.2f}")
    
    # 4. Obtener detalles
    print(f"\n4️⃣ Obteniendo detalles de la sesión...")
    details = client.get_paper_trading_session(session_id)
    
    print(f"   Detalles:")
    print(f"     Capital inicial: ${details['initial_capital']:,.2f}")
    print(f"     Capital actual: ${details['current_capital']:,.2f}")
    print(f"     Retorno: {details['total_return_pct']:.2f}%")
    print(f"     Max Drawdown: {details['max_drawdown_pct']:.2f}%")
    
    # 5. Ver trades
    if details['total_trades'] > 0:
        print(f"\n5️⃣ Trades ejecutados:")
        trades = client.get_paper_trading_trades(session_id)
        for i, trade in enumerate(trades[:5], 1):
            print(f"     {i}. {trade['side'].upper()}: "
                  f"${trade['entry_price']:.4f} → ${trade['exit_price']:.4f} | "
                  f"P&L: {trade['pnl_pct']:.2f}%")


def example_3_dashboard():
    """Ejemplo 3: Ver estadísticas del dashboard"""
    print("\n" + "="*60)
    print("EJEMPLO 3: Dashboard")
    print("="*60)
    
    client = TradingBotClient()
    
    # Obtener estadísticas
    print("\n📊 Estadísticas:")
    stats = client.get_dashboard_stats()
    
    print(f"  Estrategias: {stats['total_strategies']}")
    print(f"  Backtests: {stats['active_backtests']}")
    print(f"  Sesiones de paper trading: {stats['paper_trading_sessions']}")
    print(f"  Total trades: {stats['total_trades']}")
    print(f"  Portfolio: ${stats['portfolio_value']:,.2f}")
    print(f"  Retorno diario: {stats['daily_return']:.2f}%")
    
    # Obtener resumen
    print("\n📈 Resumen:")
    summary = client.get_dashboard_summary()
    
    # Backtests recientes
    if summary['recent_backtests']:
        print("\n  Últimos backtests:")
        for bt in summary['recent_backtests'][:3]:
            print(f"    • {bt['strategy']} ({bt['pair']}): {bt['return']:.2f}%")
    
    # Sesiones activas
    if summary['active_sessions']:
        print("\n  Sesiones activas:")
        for session in summary['active_sessions']:
            print(f"    • {session['name']}: ${session['capital']:,.2f} "
                  f"({session['return']:.2f}%)")
    
    # Mejores estrategias
    if summary['best_strategies']:
        print("\n  Mejores estrategias:")
        for strat in summary['best_strategies'][:3]:
            print(f"    • {strat['name']}: "
                  f"Winrate {strat['avg_winrate']:.1f}% "
                  f"({strat['backtests']} backtests)")


def example_4_workflow():
    """Ejemplo 4: Workflow completo"""
    print("\n" + "="*60)
    print("EJEMPLO 4: Workflow completo")
    print("="*60)
    
    client = TradingBotClient()
    
    print("\n🔄 Ejecutando workflow completo:\n")
    
    # Paso 1: Crear 2 estrategias
    print("1. Creando estrategias...")
    strategies_config = [
        {
            "name": "MA_RSI Conservative",
            "type": "MA_RSI",
            "config": {"fast_window": 10, "slow_window": 20, "rsi_window": 14}
        },
        {
            "name": "BOLLINGER Aggressive",
            "type": "BOLLINGER_MR",
            "config": {"bb_window": 20, "bb_std": 2.0, "rsi_window": 14}
        }
    ]
    
    strategy_ids = []
    for s in strategies_config:
        strategy = client.create_strategy(s["name"], s["type"], s["config"])
        strategy_ids.append(strategy['id'])
        print(f"   ✓ {s['name']} (ID: {strategy['id']})")
    
    # Paso 2: Ejecutar backtests
    print("\n2. Ejecutando backtests...")
    pairs = ["EURUSD", "USDJPY"]
    
    for strategy_id in strategy_ids:
        for pair in pairs:
            print(f"   Ejecutando backtest {strategy_id} en {pair}...")
            result = client.run_backtest(strategy_id, pair)
            if "error" not in result:
                print(f"   ✓ Retorno: {result['total_return_pct']:.2f}%")
    
    # Paso 3: Crear sesiones de paper trading
    print("\n3. Creando sesiones de paper trading...")
    for strategy_id in strategy_ids:
        session = client.create_paper_trading_session(
            strategy_id, "USDJPY",
            name=f"Session Strategy {strategy_id}"
        )
        if "error" not in session:
            print(f"   ✓ Sesión creada: {session['session_id']}")
            
            # Ejecutar inmediatamente
            result = client.run_paper_trading_session(
                session['session_id'], "USDJPY"
            )
            if "error" not in result:
                print(f"     Trades: {result['total_trades']}, "
                      f"Retorno: {result['total_return_pct']:.2f}%")
    
    # Paso 4: Resumen final
    print("\n4. Resumen final:")
    stats = client.get_dashboard_stats()
    print(f"   Estrategias totales: {stats['total_strategies']}")
    print(f"   Backtests ejecutados: {stats['active_backtests']}")
    print(f"   Trades totales: {stats['total_trades']}")
    print(f"   Retorno portfolio: {stats['daily_return']:.2f}%")


def main():
    """Función principal"""
    print("\n" + "🚀 " * 20)
    print("EJEMPLOS DE USO - Crypto Trading Bot API")
    print("🚀 " * 20)
    
    try:
        # Ejecutar ejemplos
        example_1_basic_backtest()
        example_2_paper_trading()
        example_3_dashboard()
        example_4_workflow()
        
        print("\n" + "="*60)
        print("✅ Ejemplos completados exitosamente!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar al backend.")
        print("   Asegúrate de ejecutar: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
