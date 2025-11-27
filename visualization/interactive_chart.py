import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional
from backtesting.engine import Trade

def plot_interactive_candles(
    df: pd.DataFrame,
    trades: List[Trade] = None,
    title: str = "Interactive Chart",
    indicators: Optional[pd.DataFrame] = None
) -> go.Figure:
    """
    Creates an interactive candlestick chart using Plotly.
    
    Args:
        df: DataFrame with columns 'timestamp', 'open', 'high', 'low', 'close', 'volume'.
        trades: List of Trade objects to overlay on the chart.
        title: Chart title.
        indicators: Optional DataFrame with indicator columns to plot (e.g., 'sma_fast', 'rsi').
                    Should have same index/length as df.
    """
    # Ensure timestamp is datetime and set as index if not already
    data = df.copy()
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.set_index("timestamp")
    
    # Create subplots: Row 1 for Price/Volume, Row 2 for RSI (if present)
    # We'll check if 'rsi' is in indicators to decide on subplots
    has_rsi = indicators is not None and "rsi" in indicators.columns
    
    if has_rsi:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            row_heights=[0.7, 0.3],
            subplot_titles=(title, "RSI")
        )
    else:
        fig = make_subplots(rows=1, cols=1, subplot_titles=(title,))

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name="OHLC"
        ),
        row=1, col=1
    )

    # Indicators (MA, etc.) on Price Chart
    if indicators is not None:
        for col in indicators.columns:
            if col == "rsi": continue # Handle RSI separately
            
            # Simple heuristic to distinguish overlays from oscillators could be added here
            # For now, we assume everything else goes on the main chart
            fig.add_trace(
                go.Scatter(
                    x=data.index, 
                    y=indicators[col], 
                    mode='lines', 
                    name=col,
                    line=dict(width=1)
                ),
                row=1, col=1
            )

    # RSI on Subplot 2
    if has_rsi:
        fig.add_trace(
            go.Scatter(
                x=data.index, 
                y=indicators["rsi"], 
                mode='lines', 
                name="RSI",
                line=dict(color='purple')
            ),
            row=2, col=1
        )
        # Add 70/30 lines
        fig.add_hline(y=70, line_dash="dash", line_color="gray", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="gray", row=2, col=1)

    # Trades
    if trades:
        # Separate entries and exits
        long_entries_x = []
        long_entries_y = []
        short_entries_x = []
        short_entries_y = []
        exits_x = []
        exits_y = []
        
        for t in trades:
            if t.direction == "long":
                long_entries_x.append(t.entry_time)
                long_entries_y.append(t.entry_price)
            else:
                short_entries_x.append(t.entry_time)
                short_entries_y.append(t.entry_price)
            
            if t.exit_time:
                exits_x.append(t.exit_time)
                exits_y.append(t.exit_price)

        # Add markers
        if long_entries_x:
            fig.add_trace(
                go.Scatter(
                    x=long_entries_x, y=long_entries_y,
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=12, color='green'),
                    name='Long Entry'
                ),
                row=1, col=1
            )
        
        if short_entries_x:
            fig.add_trace(
                go.Scatter(
                    x=short_entries_x, y=short_entries_y,
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=12, color='red'),
                    name='Short Entry'
                ),
                row=1, col=1
            )
            
        if exits_x:
            fig.add_trace(
                go.Scatter(
                    x=exits_x, y=exits_y,
                    mode='markers',
                    marker=dict(symbol='circle', size=10, color='blue'),
                    name='Exit'
                ),
                row=1, col=1
            )

    # Layout updates
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig
