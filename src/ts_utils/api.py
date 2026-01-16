"""
Public API for ts_utils package.
"""

from typing import List, Optional
import polars as pl
from dash import Dash

from .core.config import ColumnConfig
from .core.data_manager import TimeseriesDataManager
from .visualization.components import create_layout
from .visualization.callbacks import register_callbacks


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

    # Create layout
    app.layout = create_layout(ts_ids, display_count, ranking_df=ranking_df, ts_id_col=ts_id_col)

    # Register callbacks
    register_callbacks(app, data_manager, display_count, ranking_df=ranking_df)

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
