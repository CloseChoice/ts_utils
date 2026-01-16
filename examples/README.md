# ts_utils Examples

This directory contains examples demonstrating how to use ts_utils for interactive timeseries visualization.

## Examples

### 1. Standalone Example (`standalone_example.py`)

A complete standalone Python script that creates sample data and launches an interactive visualization.

**To run:**
```bash
python examples/standalone_example.py
```

Then open your browser to http://localhost:8050

The example demonstrates:
- Creating sample timeseries data with Polars
- Different data patterns (linear, sinusoidal, exponential, etc.)
- Launching a Dash app in standalone mode
- Using the Next button to navigate through timeseries

### 2. Jupyter Notebook Example (`jupyter_example.ipynb`)

An interactive Jupyter notebook showing various use cases.

**To run:**
```bash
jupyter notebook examples/jupyter_example.ipynb
```

The notebook demonstrates:
- Basic visualization with default settings
- Custom column name mappings
- Different display modes (inline, external)
- Working with multiple timeseries
- Interactive features (dropdown, Next button, legend)

### 3. Ranking Panel Example (`demo_ranking.py`)

Demonstrates using the ranking panel to quickly navigate to timeseries sorted by a custom metric.

**To run:**
```bash
python examples/demo_ranking.py
```

Then open your browser to http://localhost:8050

The example demonstrates:
- Creating a ranking DataFrame with custom metrics (e.g., extrema per day)
- Displaying a clickable ranking sidebar
- Using the Desc/Asc toggle to change sort order
- Clicking rows to jump directly to that timeseries

## Features Demonstrated

The examples showcase:
- **Configurable column names**: Map your dataframe columns to the visualization
- **Multi-select dropdown**: Choose which timeseries to display
- **Next button**: Paginate through available timeseries
- **Solid vs dotted lines**: Actual values shown solid, forecasts dotted
- **Auto-adjusting axes**: Axes adapt to selected data ranges
- **Lazy loading**: Efficient data handling with Polars LazyFrame
- **Ranking panel**: Sort and navigate to timeseries by custom metrics

## Requirements

Make sure ts_utils is installed:
```bash
pip install -e .
```

Or with development dependencies:
```bash
pip install -e ".[dev]"
```

## Creating Your Own Visualizations

Basic usage:
```python
import polars as pl
from ts_utils import visualize_timeseries

# Create or load your dataframe
df = pl.DataFrame({
    "timestamp": [...],
    "ts_id": [...],
    "actual_value": [...],
    "forecasted_value": [...]
})

# Create visualization
app = visualize_timeseries(df, display_count=5)

# For standalone scripts
app.run_server(debug=True)

# For Jupyter - it will run automatically
```

See the examples for more detailed usage patterns.
