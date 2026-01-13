"""
Configuration module for column name mappings.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ColumnConfig:
    """
    Configuration for column name mappings in timeseries DataFrame.

    Attributes:
        timestamp: Name of the timestamp column
        ts_id: Name of the timeseries ID column
        actual: Name of the actual values column
        forecast: Name of the forecasted values column
        extrema: Optional name of the extrema column for marking specific points
    """
    timestamp: str
    ts_id: str
    actual: str
    forecast: str
    extrema: Optional[str] = None

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

        # Validate optional extrema column if specified
        if self.extrema is not None and self.extrema not in df_columns:
            missing_columns.append(self.extrema)

        if missing_columns:
            raise ValueError(
                f"Missing columns in dataframe: {', '.join(missing_columns)}. "
                f"Available columns: {', '.join(df_columns)}"
            )
