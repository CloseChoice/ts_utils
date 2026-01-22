"""
Public API for ts_utils package.
"""

from typing import List, Optional
import polars as pl
from dash import Dash

from .core.config import ColumnConfig
from .core.data_manager import TimeseriesDataManager, ExceptionDataManager
from .visualization.components import create_layout, create_routed_layout
from .visualization.callbacks import register_callbacks, register_routing_callbacks


def _build_geo_dataframe(
    ranking_df: pl.DataFrame,
    ts_id_col: str,
    latitude_col: str = "latitude",
    longitude_col: str = "longitude",
    map_color_col: Optional[str] = None
) -> pl.DataFrame:
    """
    Build a geographic dataframe from ranking_df.

    Args:
        ranking_df: DataFrame with ts_id, latitude, longitude, and ranking columns
        ts_id_col: Name of the timeseries ID column
        latitude_col: Name of the latitude column (default: "latitude")
        longitude_col: Name of the longitude column (default: "longitude")
        map_color_col: Column for coloring (defaults to first non-ts_id/lat/lon column)

    Returns:
        DataFrame with ts_id, latitude, longitude, and optionally color_value columns
    """
    # Start with ts_id, latitude, longitude
    geo_df = ranking_df.select([
        pl.col(ts_id_col),
        pl.col(latitude_col).alias("latitude"),
        pl.col(longitude_col).alias("longitude"),
    ])

    # Determine color column (exclude ts_id, lat, lon)
    if map_color_col is None:
        exclude_cols = {ts_id_col, latitude_col, longitude_col}
        color_cols = [c for c in ranking_df.columns if c not in exclude_cols]
        if color_cols:
            map_color_col = color_cols[0]

    # Add color value if available
    if map_color_col is not None and map_color_col in ranking_df.columns:
        geo_df = geo_df.with_columns(
            ranking_df[map_color_col].alias("color_value")
        )

    return geo_df


def _get_full_time_range(df: pl.DataFrame, timestamp_col: str) -> dict:
    """
    Get the full time range from the dataframe.

    Args:
        df: DataFrame with timeseries data
        timestamp_col: Name of the timestamp column

    Returns:
        Dict with 'min' and 'max' timestamp strings
    """
    # Use select() to be compatible with both DataFrame and LazyFrame
    result = df.select([
        pl.col(timestamp_col).min().alias('min_ts'),
        pl.col(timestamp_col).max().alias('max_ts'),
    ])

    # Collect if LazyFrame
    if hasattr(result, 'collect'):
        result = result.collect()

    row = result.row(0)
    min_ts, max_ts = row[0], row[1]

    # Format as strings
    return {
        'min': min_ts.strftime('%Y-%m-%d %H:%M:%S') if min_ts else None,
        'max': max_ts.strftime('%Y-%m-%d %H:%M:%S') if max_ts else None,
    }


def _is_jupyter_environment() -> bool:
    """
    Detect if code is running in a Jupyter environment.

    Returns:
        True if running in Jupyter, False otherwise
    """
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            return True
    except ImportError:
        pass
    return False


def visualize_timeseries(
    df: pl.DataFrame,
    timestamp_col: str = "timestamp",
    ts_id_col: str = "ts_id",
    actual_col: str = "actual_value",
    forecast_col: str = "forecasted_value",
    extrema_col: Optional[str] = None,
    features: Optional[List[str]] = None,
    ranking_df: Optional[pl.DataFrame] = None,
    map_color_col: Optional[str] = None,
    df_exceptions: Optional[pl.DataFrame | pl.LazyFrame] = None,
    exception_count_col: Optional[str] = None,
    display_count: int = 5,
    mode: str = "inline",
    port: int = 8050,
    height: str = "650px",
    width: str = "100%",
    debug: bool = False,
    jupyter_mode: Optional[str] = None
) -> Dash:
    """
    Create an interactive timeseries visualization.

    This function creates a Dash-based web application for visualizing multiple
    timeseries with interactive controls. It supports both Jupyter notebook
    environments and standalone execution.

    Args:
        df: Polars DataFrame containing timeseries data
        timestamp_col: Name of the timestamp column (default: "timestamp")
        ts_id_col: Name of the timeseries ID column (default: "ts_id")
        actual_col: Name of the actual values column (default: "actual_value")
        forecast_col: Name of the forecasted values column (default: "forecasted_value")
        extrema_col: Optional name of column containing extrema values to plot as dots (default: None)
        features: Optional list of feature column names to display in a subplot below the main plot.
            Features are MinMax scaled (0-1) for display. First 5 features are visible by default,
            others are accessible via legend clicks. (default: None)
        ranking_df: Optional DataFrame with ts_id and ranking columns to show a ranking sidebar.
            When provided, a clickable ranking panel appears that allows sorting and quick navigation.
            If ranking_df contains 'latitude' and 'longitude' columns, a geographic map is displayed.
        map_color_col: Optional column name from ranking_df to use for map point coloring.
            Defaults to the first non-ts_id/lat/lon column in ranking_df.
        df_exceptions: Optional DataFrame or LazyFrame with exception data containing ts_id,
            timestamp, and exception_count columns. When provided, enables a separate
            "/exceptions" route with dynamic map coloring based on exception counts.
        exception_count_col: Name of the exception count column in df_exceptions.
            Required if df_exceptions is provided.
        display_count: Number of timeseries to display at once (default: 5)
        mode: Display mode for Jupyter ("inline", "external", "browser") (default: "inline")
        port: Port for the Dash server (default: 8050)
        height: Height of the visualization in Jupyter (default: "650px")
        width: Width of the visualization in Jupyter (default: "100%")
        debug: Enable debug mode (default: False)
        jupyter_mode: Override Jupyter environment detection ("jupyter", "standalone", or None for auto-detect)

    Returns:
        Dash application instance. In Jupyter environments, the app will be
        automatically started. In standalone mode, call app.run() manually.

    Example:
        >>> import polars as pl
        >>> from datetime import datetime, timedelta
        >>> from ts_utils import visualize_timeseries
        >>>
        >>> # Create sample data
        >>> dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
        >>> df = pl.DataFrame({
        ...     "timestamp": dates * 3,
        ...     "ts_id": ["ts_1"] * 100 + ["ts_2"] * 100 + ["ts_3"] * 100,
        ...     "actual_value": list(range(300)),
        ...     "forecasted_value": [x + 2 for x in range(300)],
        ... })
        >>>
        >>> # Create visualization (standalone)
        >>> app = visualize_timeseries(df, display_count=2)
        >>> app.run(debug=True)
        >>>
        >>> # Or with custom column names
        >>> app = visualize_timeseries(
        ...     df,
        ...     timestamp_col="time",
        ...     ts_id_col="series_id",
        ...     actual_col="measured",
        ...     forecast_col="predicted"
        ... )

    Raises:
        ValueError: If required columns are missing from the dataframe
    """
    # Create column configuration
    config = ColumnConfig(
        timestamp=timestamp_col,
        ts_id=ts_id_col,
        actual=actual_col,
        forecast=forecast_col,
        extrema=extrema_col,
        features=features
    )

    # Validate columns exist
    config.validate(df.columns)

    # Create data manager with lazy loading
    data_manager = TimeseriesDataManager(df, config)

    # Get all timeseries IDs
    ts_ids = data_manager.get_all_ts_ids()

    # Create Dash app
    app = Dash(__name__)
    app.title = "Timeseries Visualization"

    # Build geo dataframe if ranking_df has latitude and longitude columns
    geo_df = None
    if ranking_df is not None and "latitude" in ranking_df.columns and "longitude" in ranking_df.columns:
        geo_df = _build_geo_dataframe(
            ranking_df, ts_id_col, map_color_col=map_color_col
        )

    # Get full time range for the data
    full_time_range = _get_full_time_range(df, timestamp_col)

    # Create exception data manager if df_exceptions is provided
    exception_manager = None
    has_exceptions = df_exceptions is not None
    if has_exceptions:
        if exception_count_col is None:
            raise ValueError("exception_count_col is required when df_exceptions is provided")
        if geo_df is None:
            raise ValueError("df_exceptions requires ranking_df with latitude/longitude columns for map display")
        exception_manager = ExceptionDataManager(
            df_exceptions,
            ts_id_col=ts_id_col,
            timestamp_col=timestamp_col,
            exception_count_col=exception_count_col
        )

    # Create layout
    has_features = features is not None and len(features) > 0

    if has_exceptions:
        # Use routed layout with main page and exception page
        app.layout = create_routed_layout(
            ts_ids=ts_ids,
            display_count=display_count,
            ranking_df=ranking_df,
            ts_id_col=ts_id_col,
            has_features=has_features,
            geo_df=geo_df,
            full_time_range=full_time_range
        )
        # Register routing callbacks for multi-page navigation
        register_routing_callbacks(
            app,
            data_manager=data_manager,
            exception_manager=exception_manager,
            display_count=display_count,
            ranking_df=ranking_df,
            geo_df=geo_df,
            ts_ids=ts_ids,
            has_features=has_features,
            full_time_range=full_time_range
        )
    else:
        app.layout = create_layout(
            ts_ids, display_count, ranking_df=ranking_df, ts_id_col=ts_id_col,
            has_features=has_features, geo_df=geo_df,
            full_time_range=full_time_range
        )
        # Register callbacks
        register_callbacks(app, data_manager, display_count, ranking_df=ranking_df, geo_df=geo_df)

    # Determine execution mode
    is_jupyter = False
    if jupyter_mode == "jupyter":
        is_jupyter = True
    elif jupyter_mode == "standalone":
        is_jupyter = False
    elif jupyter_mode is None:
        is_jupyter = _is_jupyter_environment()

    # Auto-run in Jupyter if detected
    if is_jupyter:
        app.run(
            mode=mode,
            height=height,
            width=width,
            port=port,
            debug=debug
        )

    return app
