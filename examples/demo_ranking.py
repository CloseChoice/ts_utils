"""
Demo script for testing the ranking panel functionality.

Run with: python demo_ranking.py
"""

import polars as pl
from datetime import datetime, timedelta
import random
import math

from ts_utils import visualize_timeseries


def generate_sample_data(num_timeseries: int = 20, days: int = 100) -> pl.DataFrame:
    """Generate sample timeseries data with varying numbers of extremas."""
    random.seed(42)

    records = []
    base_date = datetime(2024, 1, 1)

    for ts_idx in range(num_timeseries):
        ts_id = f"ts_{ts_idx:03d}"

        # Each timeseries has different characteristics
        amplitude = random.uniform(5, 20)
        frequency = random.uniform(0.05, 0.2)
        noise_level = random.uniform(1, 5)

        # Vary the number of extremas per timeseries (some have many, some have few)
        extrema_probability = random.uniform(0.02, 0.15)

        for day in range(days):
            timestamp = base_date + timedelta(days=day)

            # Generate actual value with sine wave + noise
            actual = 50 + amplitude * math.sin(frequency * day) + random.gauss(0, noise_level)

            # Forecast is actual + some error
            forecast_error = random.gauss(0, 3)
            forecast = actual + forecast_error

            # Extrema: randomly mark some points (more extremas = more "problematic")
            extrema = None
            if random.random() < extrema_probability:
                extrema = actual + random.uniform(-2, 2)

            records.append({
                "timestamp": timestamp,
                "ts_id": ts_id,
                "actual_value": actual,
                "forecasted_value": forecast,
                "extrema": extrema,
            })

    return pl.DataFrame(records)


def compute_ranking(df: pl.DataFrame) -> pl.DataFrame:
    """Compute ranking based on extrema count per day."""
    ranking = (
        df.group_by("ts_id")
        .agg([
            pl.col("extrema").is_not_null().sum().alias("extrema_count"),
            pl.col("timestamp").n_unique().alias("num_days"),
        ])
        .with_columns(
            (pl.col("extrema_count") / pl.col("num_days")).alias("extrema_per_day")
        )
        .select(["ts_id", "extrema_per_day"])
        .sort("extrema_per_day", descending=True)
    )
    return ranking


if __name__ == "__main__":
    print("Generating sample data...")
    df = generate_sample_data(num_timeseries=20, days=100)

    print(f"Generated {df.shape[0]} rows for {df['ts_id'].n_unique()} timeseries")

    print("\nComputing ranking by extrema per day...")
    ranking = compute_ranking(df)

    print("\nTop 5 timeseries by extrema per day:")
    print(ranking.head(5))

    print("\nStarting visualization with ranking panel...")
    print("- Click on rows in the ranking panel to visualize that timeseries")
    print("- Use the Desc/Asc toggle to change sort order")
    print("- The dropdown and Next button still work as before")
    print("\nOpen http://localhost:8050 in your browser")

    app = visualize_timeseries(
        df,
        extrema_col="extrema",
        ranking_df=ranking,
        display_count=3,
    )

    app.run(debug=True, port=8050)
