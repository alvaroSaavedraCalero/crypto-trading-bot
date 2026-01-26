#!/usr/bin/env python3
"""
Forex Paper Trading System
Simulates trading with optimized parameters on EURUSD and USDJPY
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional
import time

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategies.registry import STRATEGY_REGISTRY
from backtesting.engine import Backtester, BacktestConfig
from utils.risk import RiskManagementConfig
from utils.logger import get_logger
from data.yfinance_downloader import get_yfinance_data

logger = get_logger(__name__)
console = Console()

# ============================================================================
# OPTIMIZED PARAMETERS (from optimization results)
# ============================================================================

OPTIMIZED_CONFIGS = {
    "MA_RSI": {
        "fast_window": 10,
        "slow_window": 20,
        "rsi_window": 14,
        "rsi_overbought": 70.0,
        "rsi_oversold": 30.0,
        "use_rsi_filter": False,
    },
    "KELTNER": {
        "kc_window": 25,
        "kc_mult": 2.5,
        "atr_window": 20,
        "atr_min_percentile": 0.4,
    },
    "BOLLINGER_MR": {
        "bb_window": 15,
        "bb_std": 2.0,
        "rsi_window": 14,
        "rsi_oversold": 25.0,
        "rsi_overbought": 70.0,
    },
}

# Configuration
PAIR = "USDJPY"  # Focus on USDJPY (showed best signals)
TIMEFRAME = "15m"
INITIAL_CAPITAL = 10000.0
RISK_PCT = 0.01
SL_PCT = 0.02
TP_RR = 2.0

# Backtest config for paper trading
BACKTEST_CONFIG = BacktestConfig(
    initial_capital=INITIAL_CAPITAL,
    sl_pct=SL_PCT,
    tp_rr=TP_RR,
    fee_pct=0.0005,
    allow_short=True,
)

RISK_CONFIG = RiskManagementConfig(risk_pct=RISK_PCT)


class PaperTrader:
    """Simulates paper trading with optimized strategies"""
    
    def __init__(self, pair: str, timeframe: str):
        self.pair = pair
        self.timeframe = timeframe
        self.capital = INITIAL_CAPITAL
        self.trades: List[Dict] = []
        self.portfolio_value = INITIAL_CAPITAL
        self.equity_history = [INITIAL_CAPITAL]
        self.timestamp_history = []
        
    def load_data(self, limit: int = 2500, period: str = "60d") -> Optional[pd.DataFrame]:
        """Load historical data for the pair"""
        try:
            df = get_yfinance_data(
                symbol=self.pair,
                timeframe=self.timeframe,
                limit=limit,
                period=period
            )
            
            if df is not None and not df.empty:
                console.print(f"[green]✓ Loaded {len(df)} candles for {self.pair}[/green]")
                return df
            else:
                console.print(f"[red]✗ No data returned for {self.pair}[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]✗ Error loading data: {e}[/red]")
            return None
    
    def test_strategy(self, strategy_name: str, df: pd.DataFrame) -> Dict:
        """Test a strategy and return results"""
        
        try:
            if df is None or df.empty:
                return {"status": "failed", "error": "No data"}
            
            # Get strategy
            strategy_class, config_class = STRATEGY_REGISTRY[strategy_name]
            params = OPTIMIZED_CONFIGS.get(strategy_name)
            
            if not params:
                return {"status": "failed", "error": "No optimized params"}
            
            # Create strategy
            config = config_class(**params)
            strategy = strategy_class(config)
            
            # Generate signals
            df_signals = strategy.generate_signals(df.copy())
            
            # Run backtest
            backtester = Backtester(BACKTEST_CONFIG, RISK_CONFIG)
            results = backtester.run(df_signals)
            
            # Store trades
            if results.trades:
                self.trades.extend(results.trades)
            
            return {
                "status": "success",
                "strategy": strategy_name,
                "return": round(results.total_return_pct, 2),
                "winrate": round(results.winrate_pct, 1),
                "trades": results.num_trades,
                "pf": round(results.profit_factor, 2),
                "dd": round(results.max_drawdown_pct, 2),
            }
            
        except Exception as e:
            logger.error(f"Error in test_strategy: {e}")
            return {"status": "error", "error": str(e)[:50]}
    
    def get_summary(self) -> Dict:
        """Get trading summary"""
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "winrate": 0.0,
                "total_return": 0.0,
                "profit_factor": 0.0,
            }
        
        total_pnl = sum(t.pnl for t in self.trades if hasattr(t, 'pnl'))
        winning = len([t for t in self.trades if hasattr(t, 'pnl') and t.pnl > 0])
        losing = len([t for t in self.trades if hasattr(t, 'pnl') and t.pnl < 0])
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": winning,
            "losing_trades": losing,
            "winrate": winning / len(self.trades) * 100 if self.trades else 0,
            "total_return": total_pnl,
            "total_return_pct": (total_pnl / INITIAL_CAPITAL) * 100,
        }


def main():
    """Main paper trading function"""
    
    console.print("\n")
    console.print(Panel(
        "[bold cyan]📊 PAPER TRADING - FOREX STRATEGIES[/bold cyan]\n"
        "[yellow]Simulación de Trading con Parámetros Optimizados[/yellow]",
        border_style="green"
    ))
    
    console.print(f"\n[bold]Configuración:[/bold]")
    console.print(f"  • Par: {PAIR}")
    console.print(f"  • Timeframe: {TIMEFRAME}")
    console.print(f"  • Capital Inicial: ${INITIAL_CAPITAL:,.2f}")
    console.print(f"  • Stop Loss: {SL_PCT*100}%")
    console.print(f"  • Take Profit Ratio: 1:{TP_RR}")
    console.print(f"  • Riesgo por Trade: {RISK_PCT*100}%\n")
    
    # Initialize trader
    trader = PaperTrader(PAIR, TIMEFRAME)
    
    # Load data
    console.print("[bold]Descargando datos históricos...[/bold]\n")
    df = trader.load_data(limit=2500, period="60d")
    
    if df is None or df.empty:
        console.print("[red]✗ No se pudieron cargar los datos[/red]")
        return
    
    # Test each optimized strategy
    console.print("[bold cyan]\n═══════════════════════════════════════════════════════════\n[/bold cyan]")
    console.print("[bold]Probando Estrategias Optimizadas...[/bold]\n")
    
    results = []
    
    for strategy_name in OPTIMIZED_CONFIGS.keys():
        console.print(f"[bold magenta]→ {strategy_name}[/bold magenta]")
        
        result = trader.test_strategy(strategy_name, df)
        results.append(result)
        
        if result["status"] == "success":
            console.print(f"  ✓ Retorno: {result['return']}% | Trades: {result['trades']} | WR: {result['winrate']}%\n")
        else:
            console.print(f"  ✗ Error: {result.get('error', 'Unknown')}\n")
    
    # Summary
    console.print("[bold cyan]═══════════════════════════════════════════════════════════\n[/bold cyan]")
    console.print("[bold cyan]RESUMEN DE PAPER TRADING[/bold cyan]\n")
    
    summary_table = Table(title="Resultados de Estrategias")
    summary_table.add_column("Estrategia", style="cyan")
    summary_table.add_column("Retorno %", justify="right")
    summary_table.add_column("Winrate %", justify="right")
    summary_table.add_column("Trades", justify="right")
    summary_table.add_column("Profit Factor", justify="right")
    summary_table.add_column("Max DD %", justify="right")
    
    successful_results = [r for r in results if r["status"] == "success"]
    
    for result in successful_results:
        return_color = "green" if result["return"] > 0 else "red"
        summary_table.add_row(
            result["strategy"],
            f"[{return_color}]{result['return']:.2f}[/{return_color}]",
            f"{result['winrate']:.1f}",
            str(result['trades']),
            f"{result['pf']:.2f}",
            f"{result['dd']:.2f}"
        )
    
    console.print(summary_table)
    
    # Best strategy
    if successful_results:
        best = max(successful_results, key=lambda x: x['return'])
        console.print(f"\n[bold green]🏆 Mejor Estrategia: {best['strategy']} ({best['return']:.2f}%)[/bold green]\n")
    
    # Statistics
    console.print("[bold cyan]ESTADÍSTICAS GENERALES[/bold cyan]\n")
    
    stats_table = Table()
    stats_table.add_column("Métrica", style="cyan")
    stats_table.add_column("Valor", style="green")
    
    total_trades = sum(r['trades'] for r in successful_results if 'trades' in r)
    avg_return = sum(r['return'] for r in successful_results) / len(successful_results) if successful_results else 0
    
    stats_table.add_row("Estrategias Probadas", str(len(OPTIMIZED_CONFIGS)))
    stats_table.add_row("Exitosas", str(len(successful_results)))
    stats_table.add_row("Total de Trades", str(total_trades))
    stats_table.add_row("Retorno Promedio", f"{avg_return:.2f}%")
    stats_table.add_row("Capital Inicial", f"${INITIAL_CAPITAL:,.2f}")
    
    console.print(stats_table)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save to CSV
    results_df = pd.DataFrame(successful_results)
    csv_file = f"paper_trading_results_{PAIR}_{timestamp}.csv"
    results_df.to_csv(csv_file, index=False)
    
    # Save to JSON with detailed config
    detailed_results = {
        "timestamp": timestamp,
        "pair": PAIR,
        "timeframe": TIMEFRAME,
        "capital": INITIAL_CAPITAL,
        "strategies_tested": len(OPTIMIZED_CONFIGS),
        "successful_tests": len(successful_results),
        "total_trades": total_trades,
        "results": successful_results,
        "configurations": OPTIMIZED_CONFIGS,
    }
    
    json_file = f"paper_trading_results_{PAIR}_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(detailed_results, f, indent=2)
    
    console.print(f"\n[green]✓ Resultados guardados:[/green]")
    console.print(f"  • {csv_file}")
    console.print(f"  • {json_file}\n")
    
    # Recommendations
    console.print("[bold cyan]═══════════════════════════════════════════════════════════\n[/bold cyan]")
    console.print("[bold yellow]📋 RECOMENDACIONES PARA PAPER TRADING[/bold yellow]\n")
    
    recommendations = [
        "✓ Monitorear los trades en tiempo real durante 2-4 semanas",
        "✓ Validar que los resultados sean consistentes con el backtest",
        "✓ Ajustar parámetros si el rendimiento diverge significativamente",
        "✓ Mantener un registro detallado de todas las operaciones",
        "✓ Evaluar el desempeño antes de implementar en trading real",
    ]
    
    for rec in recommendations:
        console.print(f"  {rec}")
    
    console.print("\n[bold green]Estado: ✅ PAPEL TRADING LISTO[/bold green]")
    console.print("[yellow]Próxima acción: Monitorear durante 2-4 semanas[/yellow]\n")


if __name__ == "__main__":
    main()
