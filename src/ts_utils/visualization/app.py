"""
Dash app creation and figure generation.
"""

from typing import List

import polars as pl
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from ..core.config import ColumnConfig


# Distinct color palette for features (20 colors)
FEATURE_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
]


def _minmax_scale(df: pl.DataFrame, columns: List[str]) -> pl.DataFrame:
    """
    Scale specified columns to 0-1 range.

    Args:
        df: Input DataFrame
        columns: List of column names to scale

    Returns:
        DataFrame with additional scaled columns (named "{col}_scaled")
    """
    scaled_exprs = []
    for col in columns:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_max != col_min:
            scaled_exprs.append(
                ((pl.col(col) - col_min) / (col_max - col_min)).alias(f"{col}_scaled")
            )
        else:
            scaled_exprs.append(pl.lit(0.5).alias(f"{col}_scaled"))
    return df.with_columns(scaled_exprs)


def _add_feature_traces(
    fig: go.Figure,
    df: pl.DataFrame,
    config: ColumnConfig,
    row: int = 2
) -> None:
    """
    Add scaled feature traces to subplot.

    Args:
        fig: Plotly Figure with subplots
        df: DataFrame containing feature data
        config: Column configuration with features list
        row: Subplot row number for features (default: 2)
    """
    if not config.features:
        return

    # Scale features
    scaled_df = _minmax_scale(df, config.features)

    # Get timestamps (use first timeseries for x-axis)
    timestamps = df.sort(config.timestamp)[config.timestamp].unique().sort().to_list()

    # Aggregate feature values across all timeseries (mean)
    agg_exprs = [pl.col(f"{col}_scaled").mean().alias(f"{col}_scaled") for col in config.features]
    feature_data = scaled_df.group_by(config.timestamp).agg(agg_exprs).sort(config.timestamp)

    for idx, feature_col in enumerate(config.features):
        scaled_col = f"{feature_col}_scaled"
        color = FEATURE_COLORS[idx % len(FEATURE_COLORS)]

        # First 5 features visible, rest legendonly
        visible = True if idx < 5 else 'legendonly'

        fig.add_trace(
            go.Scatter(
                x=feature_data[config.timestamp].to_list(),
                y=feature_data[scaled_col].to_list(),
                mode='lines',
                name=f'{feature_col}',
                line=dict(width=2, color=color),
                showlegend=True,
                visible=visible,
            ),
            row=row,
            col=1
        )


def _create_figure_with_features(df: pl.DataFrame, config: ColumnConfig) -> go.Figure:
    """
    Create Plotly figure with features subplot.

    Creates a 2-row subplot layout with main timeseries on top and
    scaled features below with a shared x-axis.

    Args:
        df: Polars DataFrame containing timeseries data
        config: Column configuration specifying column names (must have features)

    Returns:
        Plotly Figure object with subplots
    """
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.08,
        subplot_titles=("Timeseries", "Features (scaled 0-1)")
    )

    # Get unique timeseries IDs
    unique_ids = df[config.ts_id].unique().sort().to_list()

    # Add traces for each timeseries to row 1
    for ts_id in unique_ids:
        ts_data = df.filter(pl.col(config.ts_id) == ts_id).sort(config.timestamp)

        # Add solid line for actual values
        fig.add_trace(
            go.Scatter(
                x=ts_data[config.timestamp].to_list(),
                y=ts_data[config.actual].to_list(),
                mode='lines',
                name=f'{ts_id} (actual)',
                line=dict(width=2),
                showlegend=True
            ),
            row=1, col=1
        )

        # Add dotted line for forecast values
        fig.add_trace(
            go.Scatter(
                x=ts_data[config.timestamp].to_list(),
                y=ts_data[config.forecast].to_list(),
                mode='lines',
                name=f'{ts_id} (forecast)',
                line=dict(width=2, dash='dot'),
                showlegend=True
            ),
            row=1, col=1
        )

        # Add scatter plot for extrema points if configured
        if config.extrema is not None:
            extrema_data = ts_data.filter(pl.col(config.extrema).is_not_null())
            if extrema_data.shape[0] > 0:
                fig.add_trace(
                    go.Scatter(
                        x=extrema_data[config.timestamp].to_list(),
                        y=extrema_data[config.extrema].to_list(),
                        mode='markers',
                        name=f'{ts_id} (extrema)',
                        marker=dict(size=8, symbol='circle'),
                        showlegend=True
                    ),
                    row=1, col=1
                )

    # Add feature traces to row 2
    _add_feature_traces(fig, df, config, row=2)

    # Calculate y-axis range for main plot
    actual_values = df[config.actual]
    forecast_values = df[config.forecast]
    y_min = min(actual_values.min(), forecast_values.min())
    y_max = max(actual_values.max(), forecast_values.max())

    if config.extrema is not None:
        extrema_values = df[config.extrema].drop_nulls()
        if len(extrema_values) > 0:
            y_min = min(y_min, extrema_values.min())
            y_max = max(y_max, extrema_values.max())

    y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1.0

    # Update layout
    fig.update_layout(
        title="Timeseries Visualization",
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )
    fig.update_yaxes(title_text="Value", range=[y_min - y_margin, y_max + y_margin], row=1, col=1)
    fig.update_yaxes(title_text="Scaled Value", range=[-0.05, 1.05], row=2, col=1)
    fig.update_xaxes(title_text="Timestamp", row=2, col=1)

    return fig


def create_figure(df: pl.DataFrame, config: ColumnConfig) -> go.Figure:
    """
    Create Plotly figure with solid lines for actual and dotted lines for forecast.

    When features are configured, creates a subplot layout with the main timeseries
    plot on top and scaled features below with a shared x-axis.

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

    # Delegate to features implementation if features are configured
    if config.features:
        return _create_figure_with_features(df, config)

    # Standard figure without features subplot
    unique_ids = df[config.ts_id].unique().sort().to_list()

    for ts_id in unique_ids:
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

        # Add scatter plot for extrema points if configured
        if config.extrema is not None:
            extrema_data = ts_data.filter(pl.col(config.extrema).is_not_null())
            if extrema_data.shape[0] > 0:
                fig.add_trace(go.Scatter(
                    x=extrema_data[config.timestamp].to_list(),
                    y=extrema_data[config.extrema].to_list(),
                    mode='markers',
                    name=f'{ts_id} (extrema)',
                    marker=dict(size=8, symbol='circle'),
                    showlegend=True
                ))

    # Auto-adjust axes with margins
    x_range = [df[config.timestamp].min(), df[config.timestamp].max()]

    actual_values = df[config.actual]
    forecast_values = df[config.forecast]
    y_min = min(actual_values.min(), forecast_values.min())
    y_max = max(actual_values.max(), forecast_values.max())

    if config.extrema is not None:
        extrema_values = df[config.extrema].drop_nulls()
        if len(extrema_values) > 0:
            y_min = min(y_min, extrema_values.min())
            y_max = max(y_max, extrema_values.max())

    y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1.0

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
