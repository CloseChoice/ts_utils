"""
Unit tests for TimeseriesDataManager.
"""

import polars as pl
import pytest
from datetime import datetime, timedelta

from ts_utils.core.data_manager import TimeseriesDataManager
from ts_utils.core.config import ColumnConfig


def test_data_manager_initialization(sample_ts_dataframe, column_config):
    """Test that DataManager initializes correctly."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    assert manager.config == column_config
    assert manager._ts_ids is None  # Should be None until requested


def test_get_all_ts_ids(sample_ts_dataframe, column_config):
    """Test getting all unique timeseries IDs."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    ts_ids = manager.get_all_ts_ids()

    assert isinstance(ts_ids, list)
    assert len(ts_ids) == 3
    assert set(ts_ids) == {"ts_1", "ts_2", "ts_3"}
    assert ts_ids == sorted(ts_ids)  # Should be sorted


def test_get_all_ts_ids_caching(sample_ts_dataframe, column_config):
    """Test that ts_ids are cached after first call."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # First call
    ts_ids_1 = manager.get_all_ts_ids()
    assert manager._ts_ids is not None

    # Second call should return cached value
    ts_ids_2 = manager.get_all_ts_ids()
    assert ts_ids_1 is ts_ids_2  # Should be the same object


def test_get_ts_data_single_timeseries(sample_ts_dataframe, column_config):
    """Test extracting data for a single timeseries."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    result = manager.get_ts_data(["ts_1"])

    assert isinstance(result, pl.DataFrame)
    assert result.shape[0] == 10  # 10 rows for ts_1
    assert result["ts_id"].unique().to_list() == ["ts_1"]


def test_get_ts_data_multiple_timeseries(sample_ts_dataframe, column_config):
    """Test extracting data for multiple timeseries."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    result = manager.get_ts_data(["ts_1", "ts_2"])

    assert result.shape[0] == 20  # 10 rows per ts_id
    assert set(result["ts_id"].unique().to_list()) == {"ts_1", "ts_2"}


def test_get_ts_data_empty_list(sample_ts_dataframe, column_config):
    """Test that empty list returns empty dataframe."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    result = manager.get_ts_data([])

    assert isinstance(result, pl.DataFrame)
    assert result.shape[0] == 0
    # Should have correct schema
    assert set(result.columns) == {"timestamp", "ts_id", "actual_value", "forecasted_value"}


def test_get_ts_data_nonexistent_id(sample_ts_dataframe, column_config):
    """Test requesting non-existent timeseries ID."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    result = manager.get_ts_data(["nonexistent"])

    assert result.shape[0] == 0


def test_get_paginated_ids_first_page(large_ts_dataframe, column_config):
    """Test pagination for first page."""
    manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    page = manager.get_paginated_ids(offset=0, limit=3)

    assert len(page) == 3
    # IDs are sorted alphabetically, so ts_10 comes between ts_1 and ts_2
    assert page == ["ts_1", "ts_10", "ts_2"]


def test_get_paginated_ids_middle_page(large_ts_dataframe, column_config):
    """Test pagination for middle page."""
    manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    page = manager.get_paginated_ids(offset=3, limit=3)

    assert len(page) == 3
    # Alphabetically sorted
    assert page == ["ts_3", "ts_4", "ts_5"]


def test_get_paginated_ids_last_page(large_ts_dataframe, column_config):
    """Test pagination for last incomplete page."""
    manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    page = manager.get_paginated_ids(offset=9, limit=3)

    assert len(page) == 1  # Only 1 remaining
    # ts_9 is the last ID alphabetically
    assert page == ["ts_9"]


def test_get_paginated_ids_beyond_end(large_ts_dataframe, column_config):
    """Test pagination beyond available data."""
    manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    page = manager.get_paginated_ids(offset=100, limit=3)

    assert len(page) == 0


def test_get_paginated_ids_negative_offset(large_ts_dataframe, column_config):
    """Test pagination with negative offset."""
    manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    page = manager.get_paginated_ids(offset=-5, limit=3)

    # Should treat negative as 0
    assert len(page) == 3
    # Alphabetically sorted
    assert page == ["ts_1", "ts_10", "ts_2"]


def test_get_total_count(large_ts_dataframe, column_config):
    """Test getting total count of timeseries."""
    manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    count = manager.get_total_count()

    assert count == 10


def test_lazy_evaluation(sample_ts_dataframe, column_config):
    """Test that LazyFrame is used internally."""
    manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # The internal _df should be a LazyFrame
    assert isinstance(manager._df, pl.LazyFrame)


def test_custom_column_names(custom_columns_dataframe, custom_column_config):
    """Test DataManager works with custom column names."""
    manager = TimeseriesDataManager(custom_columns_dataframe, custom_column_config)

    ts_ids = manager.get_all_ts_ids()
    assert set(ts_ids) == {"series_1", "series_2"}

    result = manager.get_ts_data(["series_1"])
    assert result.shape[0] == 10
    assert "series_id" in result.columns
    assert "measured" in result.columns
    assert "predicted" in result.columns
