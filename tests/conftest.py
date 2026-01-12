"""
Pytest fixtures for testing.
"""

from datetime import datetime, timedelta
import polars as pl
import pytest

from ts_utils.core.config import ColumnConfig


@pytest.fixture
def sample_ts_dataframe():
    """Create sample timeseries data for testing."""
    # Create dates for 10 days
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]

    # Create data for 3 timeseries
    data = {
        "timestamp": dates * 3,
        "ts_id": ["ts_1"] * 10 + ["ts_2"] * 10 + ["ts_3"] * 10,
        "actual_value": list(range(30)),
        "forecasted_value": [x + 0.5 for x in range(30)],
    }

    return pl.DataFrame(data)


@pytest.fixture
def large_ts_dataframe():
    """Create a larger sample dataframe with more timeseries."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(50)]

    # Create data for 10 timeseries
    ts_ids = [f"ts_{i}" for i in range(1, 11)]

    data = {
        "timestamp": dates * 10,
        "ts_id": [ts_id for ts_id in ts_ids for _ in range(50)],
        "actual_value": list(range(500)),
        "forecasted_value": [x + 1.0 for x in range(500)],
    }

    return pl.DataFrame(data)


@pytest.fixture
def column_config():
    """Standard column configuration."""
    return ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value"
    )


@pytest.fixture
def custom_column_config():
    """Custom column configuration for testing flexibility."""
    return ColumnConfig(
        timestamp="time",
        ts_id="series_id",
        actual="measured",
        forecast="predicted"
    )


@pytest.fixture
def custom_columns_dataframe():
    """Sample dataframe with custom column names."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]

    data = {
        "time": dates * 2,
        "series_id": ["series_1"] * 10 + ["series_2"] * 10,
        "measured": list(range(20)),
        "predicted": [x + 0.3 for x in range(20)],
    }

    return pl.DataFrame(data)
