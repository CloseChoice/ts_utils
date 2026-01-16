# ts_utils

THIS IS MOSTLY FOR MY INTERNAL USE AND IS COMPLETELY VIBE-CODED AND NOT YET HUMAN VERIFIED.

Interactive timeseries visualization for Polars DataFrames using Dash and Plotly.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Interactive web-based visualization** using Dash and Plotly
- **Lazy loading** with Polars LazyFrame for efficient memory usage
- **Configurable column names** to match your dataframe structure
- **Multi-select dropdown** for choosing which timeseries to display
- **Next button** for quick pagination through available timeseries
- **Visual distinction**: Solid lines for actual values, dotted lines for forecasts
- **Extrema marking**: Optional scatter plot overlay for highlighting specific points (peaks, troughs, etc.)
- **Ranking panel**: Optional sidebar for sorting and quickly navigating to timeseries by custom metrics
- **Auto-adjusting axes** that adapt to selected data ranges
- **Dual environment support**: Works in both Jupyter notebooks and standalone applications

## Installation

### From source (recommended for development)

```bash
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

## Quick Start

### Standalone Application

```python
import polars as pl
from datetime import datetime, timedelta
from ts_utils import visualize_timeseries

# Create sample data
dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
df = pl.DataFrame({
    "timestamp": dates * 3,
    "ts_id": ["ts_1"] * 100 + ["ts_2"] * 100 + ["ts_3"] * 100,
    "actual_value": list(range(300)),
    "forecasted_value": [x + 2 for x in range(300)],
})

# Create and run visualization
app = visualize_timeseries(df, display_count=2)
app.run(debug=True)
```

Open your browser to http://localhost:8050 to see the visualization.

### Jupyter Notebook

```python
import polars as pl
from datetime import datetime, timedelta
from ts_utils import visualize_timeseries

# Create your dataframe
df = pl.DataFrame({...})

# Visualize (will display inline automatically)
app = visualize_timeseries(
    df,
    display_count=3,
    mode="inline",
    height="600px"
)
```

## API Reference

### `visualize_timeseries()`

Main function for creating interactive timeseries visualizations.

```python
def visualize_timeseries(
    df: pl.DataFrame,
    timestamp_col: str = "timestamp",
    ts_id_col: str = "ts_id",
    actual_col: str = "actual_value",
    forecast_col: str = "forecasted_value",
    extrema_col: Optional[str] = None,
    ranking_df: Optional[pl.DataFrame] = None,
    display_count: int = 5,
    mode: str = "inline",
    port: int = 8050,
    height: str = "650px",
    width: str = "100%",
    debug: bool = False,
    jupyter_mode: Optional[str] = None
) -> Dash:
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | `pl.DataFrame` | **required** | Polars DataFrame containing timeseries data |
| `timestamp_col` | `str` | `"timestamp"` | Name of the timestamp column |
| `ts_id_col` | `str` | `"ts_id"` | Name of the timeseries ID column |
| `actual_col` | `str` | `"actual_value"` | Name of the actual values column |
| `forecast_col` | `str` | `"forecasted_value"` | Name of the forecasted values column |
| `extrema_col` | `Optional[str]` | `None` | Name of column containing extrema values to plot as dots (use `None` in rows without extrema) |
| `ranking_df` | `Optional[pl.DataFrame]` | `None` | DataFrame with `ts_id` column and any additional columns to display in a ranking sidebar. Click rows to visualize that timeseries. |
| `display_count` | `int` | `5` | Number of timeseries to display at once |
| `mode` | `str` | `"inline"` | Display mode for Jupyter: `"inline"`, `"external"`, or `"browser"` |
| `port` | `int` | `8050` | Port for the Dash server |
| `height` | `str` | `"650px"` | Height of visualization in Jupyter |
| `width` | `str` | `"100%"` | Width of visualization in Jupyter |
| `debug` | `bool` | `False` | Enable Dash debug mode |
| `jupyter_mode` | `Optional[str]` | `None` | Force mode: `"jupyter"`, `"standalone"`, or `None` for auto-detect |

#### Returns

- `Dash`: Dash application instance

#### Raises

- `ValueError`: If required columns are missing from the dataframe

### Custom Column Names

If your dataframe uses different column names, simply map them when calling the function:

```python
# Your dataframe has custom columns
df = pl.DataFrame({
    "time": [...],
    "series_id": [...],
    "measured": [...],
    "predicted": [...]
})

# Map them to the visualization
app = visualize_timeseries(
    df,
    timestamp_col="time",
    ts_id_col="series_id",
    actual_col="measured",
    forecast_col="predicted"
)
```

## Usage Examples

### Example 1: Basic Usage

```python
from ts_utils import visualize_timeseries
import polars as pl
from datetime import datetime, timedelta

# Create simple timeseries data
dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(50)]
df = pl.DataFrame({
    "timestamp": dates * 2,
    "ts_id": ["product_A"] * 50 + ["product_B"] * 50,
    "actual_value": list(range(100)),
    "forecasted_value": [x + 1.5 for x in range(100)]
})

# Visualize
app = visualize_timeseries(df)
app.run()
```

### Example 2: Custom Display Count

```python
# Show 10 timeseries at once
app = visualize_timeseries(df, display_count=10)
```

### Example 3: Different Port

```python
# Run on port 9000
app = visualize_timeseries(df, port=9000)
app.run()
```

### Example 4: Jupyter with External Browser

```python
# Open in external browser instead of inline
app = visualize_timeseries(
    df,
    mode="external",
    display_count=3
)
```

### Example 5: Marking Extrema Points

```python
import polars as pl
from datetime import datetime, timedelta
from ts_utils import visualize_timeseries

# Create data with peaks and troughs
dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(50)]
df = pl.DataFrame({
    "timestamp": dates * 2,
    "ts_id": ["product_A"] * 50 + ["product_B"] * 50,
    "actual_value": list(range(100)),
    "forecasted_value": [x + 1.5 for x in range(100)],
    # Mark specific points as extrema (None for non-extrema points)
    "peaks": [None] * 10 + [12.0] + [None] * 19 + [35.0] + [None] * 19 +
             [None] * 15 + [68.0] + [None] * 34
})

# Visualize with extrema points marked
app = visualize_timeseries(df, extrema_col="peaks")
app.run()
```

### Example 6: Ranking Panel for Quick Navigation

```python
import polars as pl
from ts_utils import visualize_timeseries

# Your main timeseries data
df = pl.DataFrame({...})

# Compute a ranking (any metric you want)
# The DataFrame needs a ts_id column + any additional columns to display
ranking = (
    df.group_by("ts_id")
    .agg(
        (pl.col("extrema").is_not_null().sum() / pl.col("timestamp").n_unique())
        .alias("extrema_per_day")
    )
    .sort("extrema_per_day", descending=True)
)

# Visualize with ranking panel
# - Click rows to jump to that timeseries
# - Use Desc/Asc toggle to change sort order
app = visualize_timeseries(df, ranking_df=ranking)
app.run()
```

See `examples/demo_ranking.py` for a complete runnable example.

## Interactive Features

Once the visualization is running, you can:

1. **Select Timeseries**: Use the dropdown to select which timeseries to display
2. **Navigate**: Click the "Next" button to show the next batch of timeseries
3. **Zoom**: Click and drag to zoom into specific time ranges
4. **Pan**: Double-click to reset zoom, or use the toolbar to pan
5. **Toggle Traces**: Click legend items to show/hide specific traces
6. **Hover**: Hover over lines to see detailed values

## Architecture

ts_utils is built with:

- **Polars**: Fast dataframe library with lazy evaluation
- **Dash**: Modern web framework by Plotly
- **Plotly**: Interactive graphing library

Key components:

- **Lazy Loading**: Uses Polars LazyFrame to only load requested timeseries into memory
- **Efficient Filtering**: Filter pushdown optimization for large datasets
- **Reactive UI**: Dash callbacks handle all interactivity
- **Caching**: Timeseries IDs are cached to avoid repeated queries

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=ts_utils

# Run specific test file
pytest tests/unit/test_api.py -v
```

### Project Structure

```
ts_utils/
├── src/ts_utils/
│   ├── api.py              # Public API
│   ├── core/
│   │   ├── config.py       # Column configuration
│   │   └── data_manager.py # Lazy data loading
│   └── visualization/
│       ├── app.py          # Figure creation
│       ├── components.py   # UI components
│       └── callbacks.py    # Interactive callbacks
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
└── examples/
    ├── standalone_example.py
    └── jupyter_example.ipynb
```

## Examples

See the [examples/](examples/) directory for complete, runnable examples:

- **standalone_example.py**: Complete standalone application
- **jupyter_example.ipynb**: Jupyter notebook with multiple use cases
- **demo_ranking.py**: Ranking panel for quick navigation to problematic timeseries
- **examples/README.md**: Detailed instructions for running examples

## Requirements

- Python 3.9+
- polars >= 0.20.0
- dash >= 2.11.0
- plotly >= 5.18.0

## Performance

ts_utils uses Polars LazyFrame with filter pushdown optimization:

- **Large datasets**: Only requested timeseries are loaded into memory
- **Fast queries**: Filter operations are pushed down to the scan level
- **Caching**: Unique timeseries IDs are cached after first access

This makes it efficient even with dataframes containing millions of rows.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### Version 0.3.0

- **New feature**: Optional `ranking_df` parameter for displaying a ranking sidebar
  - Shows any DataFrame with ts_id + additional columns
  - Click rows to visualize that timeseries
  - Desc/Asc toggle for sort order
- Added 5 new tests for ranking functionality (76 total tests)
- Updated documentation with ranking examples

### Version 0.2.0

- **New feature**: Optional `extrema_col` parameter for marking specific points with scatter plot dots
- Updated y-axis range calculation to include extrema values
- Added 6 new tests for extrema functionality (67 total tests)
- Updated documentation with extrema examples

### Version 0.1.0 (Initial Release)

- Interactive timeseries visualization with Dash
- Lazy loading with Polars LazyFrame
- Configurable column names
- Multi-select dropdown and Next button navigation
- Solid/dotted line styles for actual/forecast values
- Auto-adjusting axes
- Jupyter and standalone support
- Comprehensive test suite (61 tests)

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.
