"""
Standalone example for ts_utils visualization.

This example demonstrates how to use ts_utils in a standalone Python script
to create an interactive timeseries visualization.

To run this example:
1. Install ts_utils: pip install -e .
2. Run this script: python examples/standalone_example.py
3. Open your browser to http://localhost:8050
"""

import polars as pl
from datetime import datetime, timedelta
from ts_utils import visualize_timeseries


def create_sample_data():
    """Create sample timeseries data for demonstration."""
    # Create dates for 100 days
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]

    # Create 5 different timeseries
    ts_ids = ["ts_1", "ts_2", "ts_3", "ts_4", "ts_5"]

    # Generate data for each timeseries
    data = {
        "timestamp": dates * len(ts_ids),
        "ts_id": [ts_id for ts_id in ts_ids for _ in range(100)],
        "actual_value": [],
        "forecasted_value": []
    }

    # Generate actual and forecast values with different patterns
    for i, ts_id in enumerate(ts_ids):
        # Create different patterns for each timeseries
        offset = i * 10
        for day in range(100):
            if ts_id == "ts_1":
                # Linear trend
                actual = day + offset
                forecast = day + offset + 2
            elif ts_id == "ts_2":
                # Sinusoidal pattern
                import math
                actual = 50 + 30 * math.sin(day * 0.1) + offset
                forecast = 50 + 30 * math.sin(day * 0.1) + offset + 3
            elif ts_id == "ts_3":
                # Exponential growth
                actual = offset + day ** 1.2 / 5
                forecast = offset + day ** 1.2 / 5 + 5
            elif ts_id == "ts_4":
                # Step function
                actual = offset + (day // 20) * 10
                forecast = offset + (day // 20) * 10 + 4
            else:
                # Random walk
                import random
                actual = offset + day + random.uniform(-5, 5)
                forecast = actual + random.uniform(0, 3)

            data["actual_value"].append(actual)
            data["forecasted_value"].append(forecast)

    return pl.DataFrame(data)


def main():
    """Main function to run the visualization."""
    print("Creating sample timeseries data...")
    df = create_sample_data()

    print(f"Generated {len(df)} data points across {df['ts_id'].n_unique()} timeseries")
    print("\nStarting Dash server...")
    print("Open your browser to: http://localhost:8050")
    print("Press Ctrl+C to stop the server")

    # Create and run visualization
    app = visualize_timeseries(
        df=df,
        display_count=3,  # Show 3 timeseries at a time
        port=8050,
        jupyter_mode="standalone"  # Force standalone mode
    )

    # Run the server
    app.run_server(debug=True)


if __name__ == "__main__":
    main()
