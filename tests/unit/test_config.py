"""
Unit tests for ColumnConfig.
"""

import pytest
from ts_utils.core.config import ColumnConfig


def test_column_config_creation():
    """Test that ColumnConfig can be created with valid parameters."""
    config = ColumnConfig(
        timestamp="time",
        ts_id="id",
        actual="actual_val",
        forecast="forecast_val"
    )

    assert config.timestamp == "time"
    assert config.ts_id == "id"
    assert config.actual == "actual_val"
    assert config.forecast == "forecast_val"


def test_column_config_validation_success():
    """Test validation passes when all columns exist in dataframe."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value"
    )

    df_columns = ["timestamp", "ts_id", "actual_value", "forecasted_value", "other_col"]

    # Should not raise any exception
    config.validate(df_columns)


def test_column_config_validation_missing_single_column():
    """Test validation raises ValueError when a single column is missing."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value"
    )

    df_columns = ["timestamp", "ts_id", "actual_value"]  # missing forecasted_value

    with pytest.raises(ValueError) as exc_info:
        config.validate(df_columns)

    assert "Missing columns in dataframe: forecasted_value" in str(exc_info.value)
    assert "Available columns:" in str(exc_info.value)


def test_column_config_validation_missing_multiple_columns():
    """Test validation raises ValueError when multiple columns are missing."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value"
    )

    df_columns = ["timestamp", "other_col"]  # missing ts_id, actual_value, forecasted_value

    with pytest.raises(ValueError) as exc_info:
        config.validate(df_columns)

    error_msg = str(exc_info.value)
    assert "Missing columns in dataframe:" in error_msg
    assert "ts_id" in error_msg
    assert "actual_value" in error_msg
    assert "forecasted_value" in error_msg


def test_column_config_validation_empty_dataframe():
    """Test validation raises ValueError when dataframe has no columns."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value"
    )

    df_columns = []

    with pytest.raises(ValueError) as exc_info:
        config.validate(df_columns)

    assert "Missing columns in dataframe:" in str(exc_info.value)


def test_column_config_with_custom_names():
    """Test ColumnConfig works with custom column names."""
    config = ColumnConfig(
        timestamp="custom_time",
        ts_id="series_identifier",
        actual="measured",
        forecast="predicted"
    )

    assert config.timestamp == "custom_time"
    assert config.ts_id == "series_identifier"
    assert config.actual == "measured"
    assert config.forecast == "predicted"

    # Validation with matching custom names should succeed
    df_columns = ["custom_time", "series_identifier", "measured", "predicted"]
    config.validate(df_columns)


def test_column_config_with_features():
    """Test ColumnConfig with features field."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value",
        features=["temp", "humidity", "pressure"]
    )

    assert config.features == ["temp", "humidity", "pressure"]

    # Validation should succeed when all columns exist
    df_columns = ["timestamp", "ts_id", "actual_value", "forecasted_value", "temp", "humidity", "pressure"]
    config.validate(df_columns)


def test_column_config_validation_missing_feature_column():
    """Test validation raises ValueError when a feature column is missing."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value",
        features=["temp", "humidity", "pressure"]
    )

    # Missing "pressure" column
    df_columns = ["timestamp", "ts_id", "actual_value", "forecasted_value", "temp", "humidity"]

    with pytest.raises(ValueError) as exc_info:
        config.validate(df_columns)

    assert "Missing columns in dataframe: pressure" in str(exc_info.value)


def test_column_config_validation_missing_multiple_feature_columns():
    """Test validation raises ValueError when multiple feature columns are missing."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value",
        features=["temp", "humidity", "pressure"]
    )

    # Missing all feature columns
    df_columns = ["timestamp", "ts_id", "actual_value", "forecasted_value"]

    with pytest.raises(ValueError) as exc_info:
        config.validate(df_columns)

    error_msg = str(exc_info.value)
    assert "temp" in error_msg
    assert "humidity" in error_msg
    assert "pressure" in error_msg


def test_column_config_with_features_none():
    """Test ColumnConfig with features set to None (default)."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value",
        features=None
    )

    assert config.features is None

    # Validation should succeed without feature columns
    df_columns = ["timestamp", "ts_id", "actual_value", "forecasted_value"]
    config.validate(df_columns)


def test_column_config_with_empty_features_list():
    """Test ColumnConfig with empty features list."""
    config = ColumnConfig(
        timestamp="timestamp",
        ts_id="ts_id",
        actual="actual_value",
        forecast="forecasted_value",
        features=[]
    )

    assert config.features == []

    # Validation should succeed with empty features list
    df_columns = ["timestamp", "ts_id", "actual_value", "forecasted_value"]
    config.validate(df_columns)
