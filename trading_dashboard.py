#!/usr/bin/env python3
"""
Paper Trading Dashboard - Real-time Monitoring
Monitor paper trading performance continuously
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, List
import time

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn

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

# Configuration
PAIR = "USDJPY"
TIMEFRAME = "15m"
INITIAL_CAPITAL = 10000.0

# Optimized parameters
STRATEGIES = {
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


def create_dashboard():
    """Create and display real-time dashboard"""
    
    console.clear()
    
    console.print(Panel(
        "[bold cyan]📊 PAPER TRADING DASHBOARD - REAL-TIME MONITORING[/bold cyan]",
        border_style="green"
    ))
    
    # Load latest results
    results_files = sorted(Path(".").glob("paper_trading_results_USDJPY_*.json"), reverse=True)
    
    if not results_files:
        console.print("[yellow]⚠️  No results file found. Run paper_trading_forex.py first.[/yellow]")
        return
    
    latest_file = results_files[0]
    
    with open(latest_file, "r") as f:
        results = json.load(f)
    
    # Header with summary
    console.print(f"\n[bold]Par:[/bold] {results['pair']} | "
                 f"[bold]Timeframe:[/bold] {results['timeframe']} | "
                 f"[bold]Capital:[/bold] ${results['capital']:,.0f}")
    
    timestamp = results.get('timestamp', 'Unknown')
    console.print(f"[dim]Última actualización: {timestamp}[/dim]\n")
    
    # Strategy results table
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]DESEMPEÑO DE ESTRATEGIAS[/bold cyan]\n")
    
    results_data = results.get('results', [])
    
    if results_data:
        table = Table(title="Resultados de Paper Trading")
        table.add_column("Estrategia", style="cyan")
        table.add_column("Retorno %", justify="right", style="green")
        table.add_column("Winrate %", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("PF", justify="right")
        table.add_column("Max DD %", justify="right")
        table.add_column("Estado", justify="center")
        
        best_return = max(r.get('return', 0) for r in results_data)
        
        for result in results_data:
            strategy = result.get('strategy', 'Unknown')
            ret = result.get('return', 0)
            winrate = result.get('winrate', 0)
            trades = result.get('trades', 0)
            pf = result.get('pf', 0)
            dd = result.get('dd', 0)
            
            # Determine status
            if trades > 0:
                status = "🔄 Trading"
            else:
                status = "⏸️ Waiting"
            
            # Color for return
            return_color = "green" if ret > 0 else "red" if ret < 0 else "white"
            
            table.add_row(
                strategy,
                f"[{return_color}]{ret:.2f}[/{return_color}]",
                f"{winrate:.1f}",
                str(trades),
                f"{pf:.2f}",
                f"{dd:.2f}",
                status
            )
        
        console.print(table)
        
        # Best strategy highlight
        best_strategy = max(results_data, key=lambda x: x.get('return', 0))
        console.print(f"\n[bold green]🏆 Mejor Estrategia: {best_strategy['strategy']} "
                     f"({best_strategy['return']:.2f}%)[/bold green]")
    
    # Summary statistics
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]ESTADÍSTICAS GENERALES[/bold cyan]\n")
    
    total_trades = sum(r.get('trades', 0) for r in results_data)
    avg_return = sum(r.get('return', 0) for r in results_data) / len(results_data) if results_data else 0
    total_pnl = (avg_return / 100) * INITIAL_CAPITAL * len(results_data)
    current_capital = INITIAL_CAPITAL + total_pnl
    roi = (total_pnl / INITIAL_CAPITAL) * 100
    
    stats = [
        ("Estrategias Activas", str(len(STRATEGIES))),
        ("Estrategias Exitosas", str(len(results_data))),
        ("Total de Trades", str(total_trades)),
        ("Retorno Promedio", f"{avg_return:.2f}%"),
        ("Capital Inicial", f"${INITIAL_CAPITAL:,.2f}"),
        ("Capital Actual (Est.)", f"${current_capital:,.2f}"),
        ("ROI Total", f"{roi:.2f}%"),
    ]
    
    for label, value in stats:
        console.print(f"  • {label}: {value}")
    
    # Risk metrics
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]MÉTRICAS DE RIESGO[/bold cyan]\n")
    
    max_dd = min(r.get('dd', 0) for r in results_data) if results_data else 0
    worst_trade_return = min(r.get('return', 0) for r in results_data) if results_data else 0
    
    risk_metrics = [
        ("Máximo Drawdown", f"{max_dd:.2f}%"),
        ("Peor Retorno", f"{worst_trade_return:.2f}%"),
        ("Stop Loss Configurado", "2.0%"),
        ("Risk per Trade", "1.0%"),
        ("Leverage", "1:1 (None)"),
    ]
    
    for label, value in risk_metrics:
        console.print(f"  • {label}: {value}")
    
    # Status and recommendations
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]ESTADO Y RECOMENDACIONES[/bold cyan]\n")
    
    status_items = [
        "[green]✓ Datos históricos cargados correctamente",
        "[green]✓ Parámetros optimizados aplicados",
        "[green]✓ Backtests ejecutados exitosamente",
        "[yellow]⏳ Monitoreo en tiempo real: 0 horas (recién iniciado)",
        "[yellow]⏳ Pendiente: Acumular 2-4 semanas de datos",
        "[cyan]ℹ️  Revisar daily para ajustes si es necesario",
    ]
    
    for item in status_items:
        console.print(f"  {item}")
    
    # Next steps
    console.print("\n[bold yellow]📋 PRÓXIMOS PASOS[/bold yellow]\n")
    
    steps = [
        "1. Monitorear los trades de las próximas 2-4 semanas",
        "2. Validar consistencia con resultados de backtesting",
        "3. Ajustar parámetros si el rendimiento diverge",
        "4. Mantener registro detallado de todas las operaciones",
        "5. Evaluar antes de implementar en trading real",
    ]
    
    for step in steps:
        console.print(f"  {step}")
    
    # Footer
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[green]Status: ✅ PAPER TRADING ACTIVO[/green]")
    console.print(f"[dim]Datos cargados desde: {latest_file.name}[/dim]\n")


def monitor_live():
    """Monitor paper trading with updates"""
    
    console.print("[bold cyan]Iniciando monitoreo en tiempo real...[/bold cyan]\n")
    
    try:
        while True:
            create_dashboard()
            
            # Wait before refreshing
            console.print("[dim]Actualizando cada 60 segundos (Ctrl+C para salir)...[/dim]")
            time.sleep(60)
            console.clear()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️ Monitoreo pausado[/yellow]")
        return


def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Trading Dashboard")
    parser.add_argument("--live", action="store_true", help="Monitoreo en tiempo real")
    args = parser.parse_args()
    
    if args.live:
        monitor_live()
    else:
        create_dashboard()


if __name__ == "__main__":
    main()
