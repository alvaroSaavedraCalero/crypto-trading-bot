# reporting/summary.py

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from backtesting.engine import BacktestResult


def print_backtest_summary(result: BacktestResult) -> None:
    """
    Muestra por consola un resumen legible del backtest.
    """
    print("\n===== RESUMEN BACKTEST =====")
    print(f"Número de trades: {result.num_trades}")
    print(f"Retorno total: {result.total_return_pct:.2f} %")
    print(f"Max drawdown: {result.max_drawdown_pct:.2f} %")
    print(f"Winrate: {result.winrate_pct:.2f} %")
    print(f"Profit factor: {result.profit_factor:.2f}")


def trades_to_dataframe(result: BacktestResult) -> pd.DataFrame:
    """
    Convierte la lista de Trade en un DataFrame para inspección/export.
    """
    rows = []
    for t in result.trades:
        rows.append(
            {
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "size": t.size,
                "stop_price": t.stop_price,
                "tp_price": t.tp_price,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
            }
        )

    df_trades = pd.DataFrame(rows)
    return df_trades


def save_trades_to_csv(
    result: BacktestResult,
    file_path: str | Path = "backtest_trades.csv",
) -> Path:
    """
    Guarda los trades en un CSV para análisis posterior.
    """
    file_path = Path(file_path)
    df_trades = trades_to_dataframe(result)

    df_trades.to_csv(file_path, index=False)
    print(f"Trades guardados en {file_path}")

    return file_path


def plot_equity_curve(
    result: BacktestResult,
    title: str = "Equity curve",
    show: bool = True,
) -> None:
    """
    Dibuja la equity curve del backtest.
    """
    if result.equity_curve is None or result.equity_curve.empty:
        print("No hay equity curve disponible para graficar.")
        return

    plt.figure(figsize=(10, 4))
    result.equity_curve.plot()
    plt.title(title)
    plt.xlabel("Tiempo")
    plt.ylabel("Capital")
    plt.grid(True)
    if show:
        plt.tight_layout()
        plt.show()


def save_equity_plot(
    result: BacktestResult,
    title: str = "Equity Curve",
    output_path: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Guarda la equity curve con marcadores de trades en un archivo PNG.
    
    Args:
        result: Resultado del backtest
        title: Título del gráfico
        output_path: Ruta donde guardar el gráfico (opcional)
    
    Returns:
        Path del archivo guardado o None si no hay datos
    """
    if result.equity_curve is None or result.equity_curve.empty:
        print("No hay equity curve disponible para graficar.")
        return None
    
    # Crear directorio de plots si no existe
    if output_path is None:
        plots_dir = Path("backtest_plots")
        plots_dir.mkdir(exist_ok=True)
        # Nombre de archivo seguro
        safe_title = title.replace(" ", "_").replace("/", "_")
        output_path = plots_dir / f"{safe_title}.png"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Crear figura
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3, 1])
    
    # Plot 1: Equity curve con marcadores de trades
    ax1.plot(result.equity_curve.index, result.equity_curve.values, 
             label='Equity', linewidth=1.5, color='#2E86AB')
    
    # Añadir marcadores de trades
    if result.trades:
        wins = [t for t in result.trades if t.pnl > 0]
        losses = [t for t in result.trades if t.pnl <= 0]
        
        # Obtener equity en momento de cierre de cada trade
        for t in wins:
            if t.exit_time in result.equity_curve.index:
                equity_at_exit = result.equity_curve.loc[t.exit_time]
                ax1.scatter(t.exit_time, equity_at_exit, 
                           color='green', marker='^', s=100, alpha=0.7, zorder=5)
        
        for t in losses:
            if t.exit_time in result.equity_curve.index:
                equity_at_exit = result.equity_curve.loc[t.exit_time]
                ax1.scatter(t.exit_time, equity_at_exit, 
                           color='red', marker='v', s=100, alpha=0.7, zorder=5)
    
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.set_ylabel('Capital ($)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # Plot 2: Drawdown
    if not result.equity_curve.empty:
        running_max = result.equity_curve.cummax()
        drawdown = (result.equity_curve - running_max) / running_max * 100
        ax2.fill_between(drawdown.index, drawdown.values, 0, 
                         color='red', alpha=0.3, label='Drawdown')
        ax2.plot(drawdown.index, drawdown.values, color='darkred', linewidth=1)
        ax2.set_ylabel('Drawdown (%)', fontsize=11)
        ax2.set_xlabel('Tiempo', fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='lower left')
    
    # Añadir estadísticas en el gráfico
    stats_text = (
        f"Trades: {result.num_trades} | "
        f"Return: {result.total_return_pct:.2f}% | "
        f"Max DD: {result.max_drawdown_pct:.2f}% | "
        f"Winrate: {result.winrate_pct:.1f}% | "
        f"PF: {result.profit_factor:.2f}"
    )
    fig.text(0.5, 0.02, stats_text, ha='center', fontsize=10, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Gráfico guardado en: {output_path}")
    return output_path
