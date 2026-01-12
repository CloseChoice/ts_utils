"""
Unit tests for figure creation.
"""

import polars as pl
import pytest
from datetime import datetime, timedelta
import plotly.graph_objs as go

from ts_utils.visualization.app import create_figure
from ts_utils.core.config import ColumnConfig


def test_create_figure_with_sample_data(sample_ts_dataframe, column_config):
    """Test creating a figure with sample data."""
    fig = create_figure(sample_ts_dataframe, column_config)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 6  # 3 timeseries * 2 traces each (actual + forecast)


def test_create_figure_empty_dataframe(column_config):
    """Test creating a figure with empty dataframe."""
    empty_df = pl.DataFrame({
        "timestamp": [],
        "ts_id": [],
        "actual_value": [],
        "forecasted_value": []
    })

    fig = create_figure(empty_df, column_config)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0
    assert "No data selected" in fig.layout.title.text


def test_create_figure_trace_names(sample_ts_dataframe, column_config):
    """Test that traces have correct names."""
    fig = create_figure(sample_ts_dataframe, column_config)

    trace_names = [trace.name for trace in fig.data]

    # Should have actual and forecast for each timeseries
    assert "ts_1 (actual)" in trace_names
    assert "ts_1 (forecast)" in trace_names
    assert "ts_2 (actual)" in trace_names
    assert "ts_2 (forecast)" in trace_names
    assert "ts_3 (actual)" in trace_names
    assert "ts_3 (forecast)" in trace_names


def test_create_figure_line_styles(sample_ts_dataframe, column_config):
    """Test that actual uses solid lines and forecast uses dotted lines."""
    fig = create_figure(sample_ts_dataframe, column_config)

    for trace in fig.data:
        if "(actual)" in trace.name:
            # Actual should have solid line (no dash property or dash=None)
            assert trace.line.dash is None or trace.line.dash == 'solid'
        elif "(forecast)" in trace.name:
            # Forecast should have dotted line
            assert trace.line.dash == 'dot'


def test_create_figure_axes_range(sample_ts_dataframe, column_config):
    """Test that axes are auto-adjusted correctly."""
    fig = create_figure(sample_ts_dataframe, column_config)

    # Check that x-axis range is set
    assert fig.layout.xaxis.range is not None
    assert len(fig.layout.xaxis.range) == 2

    # Check that y-axis range is set with margins
    assert fig.layout.yaxis.range is not None
    assert len(fig.layout.yaxis.range) == 2

    # Y-axis should include all values with margin
    y_min, y_max = fig.layout.yaxis.range
    actual_min = sample_ts_dataframe["actual_value"].min()
    actual_max = sample_ts_dataframe["actual_value"].max()
    forecast_min = sample_ts_dataframe["forecasted_value"].min()
    forecast_max = sample_ts_dataframe["forecasted_value"].max()

    data_min = min(actual_min, forecast_min)
    data_max = max(actual_max, forecast_max)

    # Y range should extend beyond data range (due to margin)
    assert y_min < data_min
    assert y_max > data_max


def test_create_figure_single_timeseries(column_config):
    """Test figure creation with a single timeseries."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(5)]
    df = pl.DataFrame({
        "timestamp": dates,
        "ts_id": ["ts_1"] * 5,
        "actual_value": [1, 2, 3, 4, 5],
        "forecasted_value": [1.1, 2.1, 3.1, 4.1, 5.1]
    })

    fig = create_figure(df, column_config)

    assert len(fig.data) == 2  # 1 actual + 1 forecast
    assert fig.data[0].name == "ts_1 (actual)"
    assert fig.data[1].name == "ts_1 (forecast)"


def test_create_figure_with_custom_columns(custom_columns_dataframe, custom_column_config):
    """Test figure creation with custom column names."""
    fig = create_figure(custom_columns_dataframe, custom_column_config)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4  # 2 timeseries * 2 traces each

    trace_names = [trace.name for trace in fig.data]
    assert "series_1 (actual)" in trace_names
    assert "series_1 (forecast)" in trace_names
    assert "series_2 (actual)" in trace_names
    assert "series_2 (forecast)" in trace_names


def test_create_figure_sorted_timestamps(column_config):
    """Test that data is sorted by timestamp within each timeseries."""
    # Create unsorted data
    dates = [datetime(2024, 1, 3), datetime(2024, 1, 1), datetime(2024, 1, 2)]
    df = pl.DataFrame({
        "timestamp": dates,
        "ts_id": ["ts_1"] * 3,
        "actual_value": [3, 1, 2],
        "forecasted_value": [3.5, 1.5, 2.5]
    })

    fig = create_figure(df, column_config)

    # Check that x values are sorted
    actual_trace = fig.data[0]
    x_values = list(actual_trace.x)

    # Convert to timestamps for comparison
    assert x_values == sorted(x_values)


def test_create_figure_layout_properties(sample_ts_dataframe, column_config):
    """Test that figure has proper layout properties."""
    fig = create_figure(sample_ts_dataframe, column_config)

    assert "Timeseries Visualization" in fig.layout.title.text
    assert fig.layout.xaxis.title.text == "Timestamp"
    assert fig.layout.yaxis.title.text == "Value"
    assert fig.layout.hovermode == 'x unified'


def test_create_figure_line_width(sample_ts_dataframe, column_config):
    """Test that all traces have correct line width."""
    fig = create_figure(sample_ts_dataframe, column_config)

    for trace in fig.data:
        assert trace.line.width == 2
