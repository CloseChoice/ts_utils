"""
Data manager for lazy loading of timeseries data.
"""

from typing import List, Optional
import polars as pl

from .config import ColumnConfig


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
