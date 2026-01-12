# ts_utils

Interactive timeseries visualization for Polars DataFrames using Dash and Plotly.

## Features

- Interactive web-based visualization using Dash
- Support for Polars DataFrames with lazy loading
- Configurable column names
- Multi-select dropdown for timeseries selection
- "Next" button for pagination through timeseries
- Solid lines for actual values, dotted lines for forecasts
- Auto-adjusting axes
- Works in both Jupyter notebooks and standalone applications

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

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

# Visualize
app = visualize_timeseries(df, display_count=2)
app.run_server(debug=True)
```

## API Reference

Coming soon...

## Examples

See the `examples/` directory for more usage examples.

## License

MIT
