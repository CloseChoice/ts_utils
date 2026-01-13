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


def test_create_figure_with_extrema(sample_ts_dataframe_with_extrema, column_config_with_extrema):
    """Test creating a figure with extrema column."""
    fig = create_figure(sample_ts_dataframe_with_extrema, column_config_with_extrema)

    assert isinstance(fig, go.Figure)
    # 3 timeseries * 3 traces each (actual + forecast + extrema)
    assert len(fig.data) == 9

    # Check that extrema traces exist
    trace_names = [trace.name for trace in fig.data]
    assert "ts_1 (extrema)" in trace_names
    assert "ts_2 (extrema)" in trace_names
    assert "ts_3 (extrema)" in trace_names


def test_create_figure_extrema_mode_markers(sample_ts_dataframe_with_extrema, column_config_with_extrema):
    """Test that extrema traces use markers mode."""
    fig = create_figure(sample_ts_dataframe_with_extrema, column_config_with_extrema)

    for trace in fig.data:
        if "(extrema)" in trace.name:
            assert trace.mode == 'markers'
            assert trace.marker.size == 8
            assert trace.marker.symbol == 'circle'


def test_create_figure_extrema_filters_nulls(sample_ts_dataframe_with_extrema, column_config_with_extrema):
    """Test that extrema traces only include non-null values."""
    fig = create_figure(sample_ts_dataframe_with_extrema, column_config_with_extrema)

    for trace in fig.data:
        if "(extrema)" in trace.name:
            # Each timeseries has 3 non-null extrema points
            assert len(trace.x) == 3
            assert len(trace.y) == 3
            # Verify no None values
            assert all(y is not None for y in trace.y)


def test_create_figure_without_extrema(sample_ts_dataframe, column_config):
    """Test that figure works without extrema column."""
    fig = create_figure(sample_ts_dataframe, column_config)

    assert isinstance(fig, go.Figure)
    # Should only have actual and forecast traces (no extrema)
    assert len(fig.data) == 6  # 3 timeseries * 2 traces each

    trace_names = [trace.name for trace in fig.data]
    assert not any("extrema" in name for name in trace_names)


def test_create_figure_extrema_in_axis_range(sample_ts_dataframe_with_extrema, column_config_with_extrema):
    """Test that extrema values are included in y-axis range calculation."""
    fig = create_figure(sample_ts_dataframe_with_extrema, column_config_with_extrema)

    # Get y-axis range
    y_min, y_max = fig.layout.yaxis.range

    # Get all extrema values
    extrema_values = sample_ts_dataframe_with_extrema["extrema"].drop_nulls()
    extrema_min = extrema_values.min()
    extrema_max = extrema_values.max()

    # Y range should include extrema values (with margin)
    assert y_min <= extrema_min
    assert y_max >= extrema_max


def test_create_figure_extrema_no_values(column_config_with_extrema):
    """Test figure creation when extrema column has only null values."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(5)]
    df = pl.DataFrame({
        "timestamp": dates,
        "ts_id": ["ts_1"] * 5,
        "actual_value": [1, 2, 3, 4, 5],
        "forecasted_value": [1.1, 2.1, 3.1, 4.1, 5.1],
        "extrema": [None, None, None, None, None]
    })

    fig = create_figure(df, column_config_with_extrema)

    # Should only have actual and forecast traces since all extrema are null
    assert len(fig.data) == 2
    trace_names = [trace.name for trace in fig.data]
    assert not any("extrema" in name for name in trace_names)


def test_create_figure_with_custom_columns_and_extrema(custom_columns_dataframe_with_extrema, custom_column_config_with_extrema):
    """Test creating a figure with custom column names including extrema."""
    fig = create_figure(custom_columns_dataframe_with_extrema, custom_column_config_with_extrema)

    assert isinstance(fig, go.Figure)
    # 2 timeseries * 3 traces each (actual + forecast + extrema)
    assert len(fig.data) == 6

    # Check that all traces exist with correct names
    trace_names = [trace.name for trace in fig.data]
    assert "series_1 (actual)" in trace_names
    assert "series_1 (forecast)" in trace_names
    assert "series_1 (extrema)" in trace_names
    assert "series_2 (actual)" in trace_names
    assert "series_2 (forecast)" in trace_names
    assert "series_2 (extrema)" in trace_names


def test_create_figure_custom_extrema_uses_correct_columns(custom_columns_dataframe_with_extrema, custom_column_config_with_extrema):
    """Test that custom extrema column name is used correctly."""
    fig = create_figure(custom_columns_dataframe_with_extrema, custom_column_config_with_extrema)

    # Find extrema traces
    extrema_traces = [trace for trace in fig.data if "(extrema)" in trace.name]

    # Each timeseries should have 2 extrema points (non-null values)
    for trace in extrema_traces:
        assert len(trace.x) == 2
        assert len(trace.y) == 2
        assert trace.mode == 'markers'


def test_create_figure_custom_columns_extrema_axis_range(custom_columns_dataframe_with_extrema, custom_column_config_with_extrema):
    """Test that y-axis includes custom extrema column values."""
    fig = create_figure(custom_columns_dataframe_with_extrema, custom_column_config_with_extrema)

    # Get y-axis range
    y_min, y_max = fig.layout.yaxis.range

    # Get extrema values from custom column
    extrema_values = custom_columns_dataframe_with_extrema["peak_points"].drop_nulls()
    extrema_min = extrema_values.min()
    extrema_max = extrema_values.max()

    # Y range should include extrema values (with margin)
    assert y_min <= extrema_min
    assert y_max >= extrema_max
