"""
Data manager for lazy loading of timeseries data.
"""

from datetime import datetime
from typing import List, Optional
import polars as pl

from .config import ColumnConfig


def _parse_time_string(time_str: str) -> datetime:
    """
    Parse a time string to datetime.

    Args:
        time_str: Time string in format 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'

    Returns:
        Parsed datetime object
    """
    try:
        return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return datetime.strptime(time_str, '%Y-%m-%d')


class TimeseriesDataManager:
    """
    Manages lazy loading and filtering of timeseries data using Polars LazyFrame.

    This class provides efficient data access by converting the input DataFrame
    to a LazyFrame and only materializing data when specifically requested.
    """

    def __init__(self, df: pl.DataFrame, config: ColumnConfig):
        """
        Initialize the data manager with a Polars DataFrame.

        Args:
            df: Polars DataFrame containing timeseries data
            config: Column configuration specifying column names
        """
        self._df = df.lazy()  # Convert to LazyFrame for efficiency
        self.config = config
        self._ts_ids: Optional[List[str]] = None  # Cache for ts_ids

    def get_all_ts_ids(self) -> List[str]:
        """
        Get list of all unique timeseries IDs.

        The result is cached to avoid repeated computation.

        Returns:
            List of unique timeseries IDs sorted alphabetically
        """
        if self._ts_ids is None:
            self._ts_ids = (
                self._df
                .select(pl.col(self.config.ts_id))
                .unique()
                .sort(self.config.ts_id)
                .collect()[self.config.ts_id]
                .to_list()
            )
        return self._ts_ids

    def get_ts_data(self, ts_ids: List[str]) -> pl.DataFrame:
        """
        Lazily extract data for specific timeseries IDs.

        Uses Polars filter pushdown for efficient querying.

        Args:
            ts_ids: List of timeseries IDs to extract

        Returns:
            Polars DataFrame containing only the requested timeseries
        """
        if not ts_ids:
            # Return empty dataframe with correct schema
            return self._df.limit(0).collect()

        return (
            self._df
            .filter(pl.col(self.config.ts_id).is_in(ts_ids))
            .collect()
        )

    def get_paginated_ids(self, offset: int, limit: int) -> List[str]:
        """
        Get a page of timeseries IDs for pagination.

        Args:
            offset: Starting index (0-based)
            limit: Maximum number of IDs to return

        Returns:
            List of timeseries IDs for the requested page
        """
        all_ids = self.get_all_ts_ids()

        # Handle edge cases
        if offset < 0:
            offset = 0
        if offset >= len(all_ids):
            return []

        end_idx = min(offset + limit, len(all_ids))
        return all_ids[offset:end_idx]

    def get_total_count(self) -> int:
        """
        Get the total number of unique timeseries.

        Returns:
            Total count of unique timeseries IDs
        """
        return len(self.get_all_ts_ids())


class ExceptionDataManager:
    """Manages lazy filtering and aggregation of exception data."""

    def __init__(
        self,
        df_exceptions: pl.DataFrame | pl.LazyFrame,
        ts_id_col: str,
        timestamp_col: str,
        exception_count_col: str
    ):
        """
        Initialize the exception data manager.

        Args:
            df_exceptions: DataFrame or LazyFrame with exception data
            ts_id_col: Name of the timeseries ID column
            timestamp_col: Name of the timestamp column
            exception_count_col: Name of the exception count column
        """
        # Store as LazyFrame
        self._df = df_exceptions.lazy() if isinstance(df_exceptions, pl.DataFrame) else df_exceptions
        self.ts_id_col = ts_id_col
        self.timestamp_col = timestamp_col
        self.exception_count_col = exception_count_col

    def get_aggregated_exceptions(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Aggregate exceptions within timeframe. Only collects here.

        Args:
            start_time: Optional start time filter (inclusive), format: 'YYYY-MM-DD HH:MM:SS'
            end_time: Optional end time filter (inclusive), format: 'YYYY-MM-DD HH:MM:SS'

        Returns:
            DataFrame with ts_id and exception_sum columns
        """
        query = self._df

        if start_time:
            start_dt = _parse_time_string(start_time)
            query = query.filter(pl.col(self.timestamp_col) >= start_dt)
        if end_time:
            end_dt = _parse_time_string(end_time)
            query = query.filter(pl.col(self.timestamp_col) <= end_dt)

        return (
            query
            .group_by(self.ts_id_col)
            .agg(pl.col(self.exception_count_col).sum().alias("exception_sum"))
            .collect()  # Only execution point
        )

    def get_timeseries_data(
        self,
        ts_ids: List[str],
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> pl.DataFrame:
        """
        Get exception data for specific timeseries IDs within timeframe.

        Args:
            ts_ids: List of timeseries IDs to retrieve
            start_time: Optional start time filter (inclusive), format: 'YYYY-MM-DD HH:MM:SS'
            end_time: Optional end time filter (inclusive), format: 'YYYY-MM-DD HH:MM:SS'

        Returns:
            DataFrame with exception data for the specified IDs and timeframe
        """
        if not ts_ids:
            return self._df.limit(0).collect()

        query = self._df.filter(pl.col(self.ts_id_col).is_in(ts_ids))

        if start_time:
            start_dt = _parse_time_string(start_time)
            query = query.filter(pl.col(self.timestamp_col) >= start_dt)
        if end_time:
            end_dt = _parse_time_string(end_time)
            query = query.filter(pl.col(self.timestamp_col) <= end_dt)

        return query.collect()
