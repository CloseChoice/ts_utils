"""
Configuration module for column name mappings.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ColumnConfig:
    """
    Configuration for column name mappings in timeseries DataFrame.

    Attributes:
        timestamp: Name of the timestamp column
        ts_id: Name of the timeseries ID column
        actual: Name of the actual values column
        forecast: Name of the forecasted values column
    """
    timestamp: str
    ts_id: str
    actual: str
    forecast: str

    def validate(self, df_columns: List[str]) -> None:
        """
        Validate that all configured columns exist in the dataframe.

        Args:
            df_columns: List of column names from the dataframe

        Raises:
            ValueError: If any configured column is missing from the dataframe
        """
        missing_columns = []

        for attr_name in ["timestamp", "ts_id", "actual", "forecast"]:
            col_name = getattr(self, attr_name)
            if col_name not in df_columns:
                missing_columns.append(col_name)

        if missing_columns:
            raise ValueError(
                f"Missing columns in dataframe: {', '.join(missing_columns)}. "
                f"Available columns: {', '.join(df_columns)}"
            )
