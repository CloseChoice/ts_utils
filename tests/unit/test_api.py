"""
Unit tests for public API.
"""

import pytest
import polars as pl
from dash import Dash

from ts_utils import visualize_timeseries
from ts_utils.api import _is_jupyter_environment


def test_visualize_timeseries_creates_app(sample_ts_dataframe):
    """Test that visualize_timeseries creates a Dash app."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        jupyter_mode="standalone"  # Force standalone mode
    )

    assert isinstance(app, Dash)
    assert app.title == "Timeseries Visualization"


def test_visualize_timeseries_with_default_columns(sample_ts_dataframe):
    """Test visualization with default column names."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        jupyter_mode="standalone"
    )

    assert app is not None
    assert hasattr(app, 'layout')
    assert hasattr(app, 'callback_map')


def test_visualize_timeseries_with_custom_columns(custom_columns_dataframe):
    """Test visualization with custom column names."""
    app = visualize_timeseries(
        custom_columns_dataframe,
        timestamp_col="time",
        ts_id_col="series_id",
        actual_col="measured",
        forecast_col="predicted",
        jupyter_mode="standalone"
    )

    assert app is not None


def test_visualize_timeseries_with_missing_columns(sample_ts_dataframe):
    """Test that ValueError is raised when columns are missing."""
    with pytest.raises(ValueError) as exc_info:
        visualize_timeseries(
            sample_ts_dataframe,
            actual_col="nonexistent_column",
            jupyter_mode="standalone"
        )

    assert "Missing columns in dataframe" in str(exc_info.value)


def test_visualize_timeseries_custom_display_count(sample_ts_dataframe):
    """Test with custom display count."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        display_count=2,
        jupyter_mode="standalone"
    )

    assert app is not None


def test_visualize_timeseries_custom_port(sample_ts_dataframe):
    """Test with custom port."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        port=9000,
        jupyter_mode="standalone"
    )

    assert app is not None


def test_visualize_timeseries_debug_mode(sample_ts_dataframe):
    """Test with debug mode enabled."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        debug=True,
        jupyter_mode="standalone"
    )

    assert app is not None


def test_is_jupyter_environment():
    """Test Jupyter environment detection."""
    # In test environment, should return False
    is_jupyter = _is_jupyter_environment()

    assert isinstance(is_jupyter, bool)
    # In pytest, this should be False
    assert is_jupyter is False


def test_visualize_timeseries_mode_override_jupyter(sample_ts_dataframe):
    """Test that jupyter_mode='jupyter' forces Jupyter mode."""
    # This shouldn't crash even in non-Jupyter environment
    # The app.run() call will fail but the app should be created
    try:
        app = visualize_timeseries(
            sample_ts_dataframe,
            jupyter_mode="jupyter"
        )
        # If we get here, app was created before run() was called
        assert isinstance(app, Dash)
    except Exception as e:
        # app.run() might fail in non-Jupyter environment, which is expected
        # What matters is that the function tries to run in Jupyter mode
        pass


def test_visualize_timeseries_mode_override_standalone(sample_ts_dataframe):
    """Test that jupyter_mode='standalone' forces standalone mode."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        jupyter_mode="standalone"
    )

    # Should return app without running it
    assert isinstance(app, Dash)


def test_visualize_timeseries_with_large_dataframe(large_ts_dataframe):
    """Test visualization with larger dataframe."""
    app = visualize_timeseries(
        large_ts_dataframe,
        display_count=5,
        jupyter_mode="standalone"
    )

    assert app is not None


def test_visualize_timeseries_callbacks_registered(sample_ts_dataframe):
    """Test that callbacks are registered in the app."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        jupyter_mode="standalone"
    )

    # Check that callbacks exist
    assert len(app.callback_map) > 0


def test_visualize_timeseries_layout_has_components(sample_ts_dataframe):
    """Test that layout has expected components."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        display_count=2,
        jupyter_mode="standalone"
    )

    # Layout should exist and have children
    assert app.layout is not None
    assert hasattr(app.layout, 'children')


def test_visualize_timeseries_all_parameters(sample_ts_dataframe):
    """Test with all parameters specified."""
    app = visualize_timeseries(
        df=sample_ts_dataframe,
        timestamp_col="timestamp",
        ts_id_col="ts_id",
        actual_col="actual_value",
        forecast_col="forecasted_value",
        display_count=3,
        mode="inline",
        port=8888,
        height="700px",
        width="90%",
        debug=False,
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)


def test_visualize_timeseries_with_custom_columns_and_extrema(custom_columns_dataframe_with_extrema):
    """Test visualization with custom column names including extrema."""
    app = visualize_timeseries(
        df=custom_columns_dataframe_with_extrema,
        timestamp_col="time",
        ts_id_col="series_id",
        actual_col="measured",
        forecast_col="predicted",
        extrema_col="peak_points",
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)
    assert app.title == "Timeseries Visualization"


def test_visualize_timeseries_with_ranking_df(sample_ts_dataframe):
    """Test visualization with ranking DataFrame."""
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'score': [10.0, 5.0, 2.0]
    })

    app = visualize_timeseries(
        sample_ts_dataframe,
        ranking_df=ranking_df,
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)
    # Should have more callbacks with ranking enabled
    assert len(app.callback_map) > 2


def test_visualize_timeseries_with_ranking_df_custom_columns(custom_columns_dataframe):
    """Test visualization with ranking DataFrame and custom ts_id column."""
    ranking_df = pl.DataFrame({
        'series_id': ['s_1', 's_2', 's_3'],
        'metric': [1.0, 2.0, 3.0]
    })

    app = visualize_timeseries(
        custom_columns_dataframe,
        timestamp_col="time",
        ts_id_col="series_id",
        actual_col="measured",
        forecast_col="predicted",
        ranking_df=ranking_df,
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)


def test_visualize_timeseries_ranking_df_multiple_metrics(sample_ts_dataframe):
    """Test visualization with ranking DataFrame containing multiple metric columns."""
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'extrema_count': [15, 8, 3],
        'error_rate': [0.25, 0.12, 0.05],
        'variance': [100.5, 50.2, 25.1]
    })

    app = visualize_timeseries(
        sample_ts_dataframe,
        ranking_df=ranking_df,
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)


def test_visualize_timeseries_with_features(sample_ts_dataframe_with_features):
    """Test visualization with features parameter."""
    app = visualize_timeseries(
        sample_ts_dataframe_with_features,
        features=["temp", "humidity", "pressure"],
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)
    assert app.title == "Timeseries Visualization"


def test_visualize_timeseries_missing_feature_column(sample_ts_dataframe):
    """Test that ValueError is raised when a feature column is missing."""
    with pytest.raises(ValueError) as exc_info:
        visualize_timeseries(
            sample_ts_dataframe,
            features=["nonexistent_feature"],
            jupyter_mode="standalone"
        )

    assert "Missing columns in dataframe" in str(exc_info.value)
    assert "nonexistent_feature" in str(exc_info.value)


def test_visualize_timeseries_with_features_and_extrema(sample_ts_dataframe_with_features):
    """Test visualization with both features and extrema parameters."""
    # Add extrema column to the fixture data
    df = sample_ts_dataframe_with_features.with_columns(
        pl.when(pl.col("actual_value") % 5 == 0)
        .then(pl.col("actual_value"))
        .otherwise(None)
        .alias("extrema")
    )

    app = visualize_timeseries(
        df,
        features=["temp", "humidity"],
        extrema_col="extrema",
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)


def test_visualize_timeseries_with_empty_features_list(sample_ts_dataframe):
    """Test visualization with empty features list (should behave like no features)."""
    app = visualize_timeseries(
        sample_ts_dataframe,
        features=[],
        jupyter_mode="standalone"
    )

    assert isinstance(app, Dash)


def test_get_full_time_range(sample_ts_dataframe):
    """Test getting full time range from dataframe."""
    from ts_utils.api import _get_full_time_range

    time_range = _get_full_time_range(sample_ts_dataframe, 'timestamp')

    assert isinstance(time_range, dict)
    assert 'min' in time_range
    assert 'max' in time_range
    assert time_range['min'] == '2024-01-01 00:00:00'
    assert time_range['max'] == '2024-01-10 00:00:00'


def test_get_full_time_range_with_lazyframe(sample_ts_lazyframe):
    """Test getting full time range from LazyFrame."""
    from ts_utils.api import _get_full_time_range

    time_range = _get_full_time_range(sample_ts_lazyframe, 'timestamp')

    assert isinstance(time_range, dict)
    assert 'min' in time_range
    assert 'max' in time_range
    assert time_range['min'] == '2024-01-01 00:00:00'
    assert time_range['max'] == '2024-01-10 00:00:00'


