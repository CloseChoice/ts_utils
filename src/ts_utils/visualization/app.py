"""
Dash app creation and figure generation.
"""

import polars as pl
import plotly.graph_objs as go

from ..core.config import ColumnConfig


def create_figure(df: pl.DataFrame, config: ColumnConfig) -> go.Figure:
    """
    Create Plotly figure with solid lines for actual and dotted lines for forecast.

    Auto-adjusts axes based on data ranges with added margins for visibility.

    Args:
        df: Polars DataFrame containing timeseries data
        config: Column configuration specifying column names

    Returns:
        Plotly Figure object with configured traces and layout
    """
    fig = go.Figure()

    # If dataframe is empty, return empty figure
    if df.shape[0] == 0:
        fig.update_layout(
            title="No data selected",
            xaxis_title="Time",
            yaxis_title="Value"
        )
        return fig

    # Get unique timeseries IDs
    unique_ids = df[config.ts_id].unique().sort().to_list()

    # Add traces for each timeseries
    for ts_id in unique_ids:
        # Filter data for this timeseries
        ts_data = df.filter(pl.col(config.ts_id) == ts_id).sort(config.timestamp)

        # Add solid line for actual values
        fig.add_trace(go.Scatter(
            x=ts_data[config.timestamp].to_list(),
            y=ts_data[config.actual].to_list(),
            mode='lines',
            name=f'{ts_id} (actual)',
            line=dict(width=2),
            showlegend=True
        ))

        # Add dotted line for forecast values
        fig.add_trace(go.Scatter(
            x=ts_data[config.timestamp].to_list(),
            y=ts_data[config.forecast].to_list(),
            mode='lines',
            name=f'{ts_id} (forecast)',
            line=dict(width=2, dash='dot'),
            showlegend=True
        ))

    # Auto-adjust axes with margins
    x_range = [df[config.timestamp].min(), df[config.timestamp].max()]

    # Get all y values for range calculation
    actual_values = df[config.actual]
    forecast_values = df[config.forecast]

    y_min = min(actual_values.min(), forecast_values.min())
    y_max = max(actual_values.max(), forecast_values.max())

    # Add 10% margin to y-axis for better visibility
    y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1.0

    # Update layout with auto-adjusted axes
    fig.update_layout(
        title="Timeseries Visualization",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        xaxis=dict(range=x_range),
        yaxis=dict(range=[y_min - y_margin, y_max + y_margin]),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )

    return fig
