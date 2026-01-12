# Implementation Plan: ts_utils Interactive Timeseries Visualization Package

## Overview

Building a Python package for interactive timeseries visualization using:
- **Dash** (Plotly) for web-based visualization (works in Jupyter + standalone)
- **Polars** for efficient lazy data loading
- Support for configurable column names
- Multi-select dropdown + "Next" button for navigation
- Solid lines for actual values, dotted lines for forecasts

## Project Structure

```
ts_utils/
├── pyproject.toml                   # Package config with dependencies
├── README.md                        # Documentation
├── LICENSE                          # MIT license
├── .gitignore                       # Git ignore patterns
├── src/
│   └── ts_utils/
│       ├── __init__.py              # Public API exports
│       ├── api.py                   # Main visualize_timeseries() function
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py            # ColumnConfig dataclass
│       │   └── data_manager.py      # Lazy loading with Polars
│       └── visualization/
│           ├── __init__.py
│           ├── components.py        # UI components (dropdown, graph, buttons)
│           ├── callbacks.py         # Dash callback functions
│           └── app.py               # Dash app creation
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_data_manager.py
│   │   └── test_components.py
│   └── integration/
│       └── test_visualization.py
└── examples/
    ├── standalone_example.py
    └── jupyter_example.ipynb
```

## Key Architecture Decisions

### 1. Lazy Loading with Polars
- Convert input DataFrame to LazyFrame on initialization
- Use `.filter()` with `.is_in()` for efficient filtering
- Only call `.collect()` when data is actually needed
- Cache list of unique ts_ids to avoid repeated computation

### 2. Dash for Both Jupyter and Standalone
- Use Dash >= 2.11 with built-in Jupyter support
- Detect environment and auto-configure display mode
- Same codebase works in both contexts

### 3. Public API Design
```python
def visualize_timeseries(
    df: pl.DataFrame,
    timestamp_col: str = "timestamp",
    ts_id_col: str = "ts_id",
    actual_col: str = "actual_value",
    forecast_col: str = "forecasted_value",
    display_count: int = 5,
    mode: str = "inline",  # "inline", "external", "browser"
    port: int = 8050,
    height: str = "650px",
    width: str = "100%"
) -> Dash
```

## Implementation Sequence

### Phase 1: Project Foundation (Commit 1)
**Task**: Initialize project structure

**Files to create**:
- `/home/tobias/programming/github/timeseries/ts_utils/pyproject.toml`
- `/home/tobias/programming/github/timeseries/ts_utils/src/ts_utils/__init__.py`
- `/home/tobias/programming/github/timeseries/ts_utils/README.md`
- `/home/tobias/programming/github/timeseries/ts_utils/LICENSE`
- `/home/tobias/programming/github/timeseries/ts_utils/.gitignore`
- Empty directories for tests/, examples/

**Dependencies** (in pyproject.toml):
```toml
dependencies = [
    "polars>=0.20.0",
    "dash>=2.11.0",
    "plotly>=5.18.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
```

**Verification**: Check directory structure exists, pyproject.toml is valid

**Commit**: "feat: initialize project structure with pyproject.toml"

---

### Phase 2: Column Configuration (Commit 2)
**Task**: Add configuration for column name mapping

**Files to create**:
- `src/ts_utils/core/__init__.py`
- `src/ts_utils/core/config.py` - ColumnConfig dataclass with validation
- `tests/unit/test_config.py` - Test config validation

**Key features**:
- `ColumnConfig` dataclass with timestamp, ts_id, actual, forecast fields
- `validate()` method to ensure columns exist in dataframe
- Default column names

**Verification**: Run `pytest tests/unit/test_config.py -v`

**Commit**: "feat: add column configuration with validation"

---

### Phase 3: Data Manager with Lazy Loading (Commit 3)
**Task**: Implement lazy data loading with Polars

**Files to create**:
- `src/ts_utils/core/data_manager.py` - TimeseriesDataManager class
- `tests/unit/test_data_manager.py` - Test lazy loading and filtering
- `tests/conftest.py` - Shared fixtures (sample dataframes)

**Key features**:
- Convert DataFrame to LazyFrame
- `get_all_ts_ids()` - cached list of unique IDs
- `get_ts_data(ts_ids)` - lazy filter and collect specific timeseries
- `get_paginated_ids(offset, limit)` - support for "Next" button

**Implementation details**:
```python
class TimeseriesDataManager:
    def __init__(self, df: pl.DataFrame, config: ColumnConfig):
        self._df = df.lazy()  # LazyFrame for efficiency
        self.config = config
        self._ts_ids = None  # Cache

    def get_ts_data(self, ts_ids: list[str]) -> pl.DataFrame:
        return (
            self._df
            .filter(pl.col(self.config.ts_id).is_in(ts_ids))
            .collect()
        )
```

**Verification**: Run `pytest tests/unit/test_data_manager.py -v`

**Commit**: "feat: add lazy data manager with Polars LazyFrame"

---

### Phase 4: UI Components (Commit 4)
**Task**: Create reusable Dash UI components

**Files to create**:
- `src/ts_utils/visualization/__init__.py`
- `src/ts_utils/visualization/components.py` - Component functions
- `tests/unit/test_components.py` - Test component creation

**Key features**:
- `create_ts_selector()` - Multi-select dropdown
- `create_graph_component()` - Main graph area
- `create_next_button()` - Pagination button
- `create_layout()` - Assemble complete layout with dcc.Store for state

**Verification**: Run `pytest tests/unit/test_components.py -v`

**Commit**: "feat: add UI components (dropdown, graph, next button)"

---

### Phase 5: Figure Creation (Commit 5)
**Task**: Create Plotly figures with solid/dotted lines

**Files to create**:
- `src/ts_utils/visualization/app.py` - Figure creation logic

**Key features**:
- Iterate through selected timeseries IDs
- Add solid lines (`mode='lines'`) for actual values
- Add dotted lines (`line=dict(dash='dot')`) for forecasts
- Auto-adjust x and y axes based on data ranges
- Add margins for better visibility

**Implementation details**:
```python
def create_figure(df: pl.DataFrame, config: ColumnConfig) -> go.Figure:
    fig = go.Figure()

    for ts_id in df[config.ts_id].unique():
        ts_data = df.filter(pl.col(config.ts_id) == ts_id)

        # Solid line for actual
        fig.add_trace(go.Scatter(
            x=ts_data[config.timestamp],
            y=ts_data[config.actual],
            mode='lines',
            name=f'{ts_id} (actual)',
            line=dict(width=2)
        ))

        # Dotted line for forecast
        fig.add_trace(go.Scatter(
            x=ts_data[config.timestamp],
            y=ts_data[config.forecast],
            mode='lines',
            name=f'{ts_id} (forecast)',
            line=dict(width=2, dash='dot')
        ))

    # Auto-adjust axes
    x_range = [df[config.timestamp].min(), df[config.timestamp].max()]
    y_values = pl.concat([df[config.actual], df[config.forecast]])
    y_min, y_max = y_values.min(), y_values.max()
    y_margin = (y_max - y_min) * 0.1

    fig.update_xaxes(range=x_range)
    fig.update_yaxes(range=[y_min - y_margin, y_max + y_margin])

    return fig
```

**Verification**: Run `pytest tests/ -v`

**Commit**: "feat: add figure creation with solid/dotted line styles"

---

### Phase 6: Interactive Callbacks (Commit 6)
**Task**: Add Dash callbacks for interactivity

**Files to create**:
- `src/ts_utils/visualization/callbacks.py` - Callback registration
- `tests/integration/test_visualization.py` - Integration tests

**Key features**:
- Callback to update graph when dropdown selection changes
- Callback for "Next" button to load next batch of timeseries
- State management using dcc.Store

**Implementation details**:
```python
def register_callbacks(app, data_manager, display_count):
    @app.callback(
        Output('timeseries-graph', 'figure'),
        Input('ts-selector', 'value')
    )
    def update_graph(selected_ids):
        if not selected_ids:
            return go.Figure()

        df = data_manager.get_ts_data(selected_ids)
        return create_figure(df, data_manager.config)

    @app.callback(
        Output('ts-selector', 'value'),
        Output('current-offset', 'data'),
        Input('next-button', 'n_clicks'),
        State('current-offset', 'data')
    )
    def handle_next_button(n_clicks, current_offset):
        if n_clicks is None:
            return dash.no_update, dash.no_update

        new_offset = current_offset + display_count
        new_ids = data_manager.get_paginated_ids(new_offset, display_count)
        return new_ids, new_offset
```

**Verification**: Run `pytest tests/ -v`

**Commit**: "feat: add Dash callbacks for interactive selection and pagination"

---

### Phase 7: Public API (Commit 7)
**Task**: Implement user-facing API function

**Files to create**:
- `src/ts_utils/api.py` - Main visualize_timeseries() function
- Update `src/ts_utils/__init__.py` - Export public API

**Key features**:
- Create DataManager with config
- Build Dash app with components and callbacks
- Detect Jupyter environment
- Auto-run server in Jupyter mode, return app otherwise

**Implementation details**:
```python
def visualize_timeseries(
    df: pl.DataFrame,
    timestamp_col: str = "timestamp",
    ts_id_col: str = "ts_id",
    actual_col: str = "actual_value",
    forecast_col: str = "forecasted_value",
    display_count: int = 5,
    mode: str = "inline",
    port: int = 8050,
    height: str = "650px",
    width: str = "100%"
) -> Dash:
    # Create config and data manager
    config = ColumnConfig(timestamp_col, ts_id_col, actual_col, forecast_col)
    config.validate(df.columns)
    data_manager = TimeseriesDataManager(df, config)

    # Create app
    app = create_dash_app(data_manager, display_count, mode, height, width)

    # Auto-run in Jupyter
    if _is_jupyter_environment():
        app.run_server(mode=mode, height=height, width=width, port=port)

    return app
```

**Verification**: Run `pytest tests/ -v`

**Commit**: "feat: add public API with visualize_timeseries function"

---

### Phase 8: Examples (Commit 8)
**Task**: Create usage examples

**Files to create**:
- `examples/standalone_example.py` - Standalone script
- `examples/jupyter_example.ipynb` - Jupyter notebook

**Example content**:
```python
# standalone_example.py
import polars as pl
from datetime import datetime, timedelta
from ts_utils import visualize_timeseries

# Create sample data
dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
df = pl.DataFrame({
    "timestamp": dates * 5,
    "ts_id": ["ts_1"] * 100 + ["ts_2"] * 100 + ["ts_3"] * 100 + ["ts_4"] * 100 + ["ts_5"] * 100,
    "actual_value": list(range(500)),
    "forecasted_value": [x + 2 for x in range(500)],
})

# Visualize
app = visualize_timeseries(df, display_count=3)
app.run_server(debug=True)
```

**Verification**: Run examples manually, test in Jupyter and standalone

**Commit**: "docs: add usage examples for standalone and Jupyter"

---

### Phase 9: Documentation (Commit 9)
**Task**: Add comprehensive documentation

**Files to update**:
- `README.md` - Add installation, quick start, API reference
- Add docstrings to all public functions

**README sections**:
1. Installation: `pip install -e .`
2. Quick start with code example
3. Features list
4. API reference
5. Configuration options
6. Examples link

**Verification**: Run full test suite with coverage: `pytest tests/ -v --cov=ts_utils`

**Commit**: "docs: add comprehensive documentation and docstrings"

---

## Critical Files

1. **pyproject.toml** - Package configuration with Dash >=2.11, Polars >=0.20, Plotly
2. **src/ts_utils/core/data_manager.py** - Lazy loading logic with Polars LazyFrame
3. **src/ts_utils/visualization/callbacks.py** - Interactive callback logic
4. **src/ts_utils/visualization/app.py** - Figure creation with line styles
5. **src/ts_utils/api.py** - Public API function
6. **tests/conftest.py** - Test fixtures and sample data

## Verification Strategy

After each commit:
1. Run relevant tests: `pytest tests/unit/<test_file>.py -v`
2. Verify tests pass before committing
3. After commit 7 (Public API), test end-to-end workflow

Final verification (after commit 9):
1. Run full test suite: `pytest tests/ -v --cov=ts_utils`
2. Install package: `pip install -e .`
3. Run standalone example: `python examples/standalone_example.py`
4. Open Jupyter notebook and run: `examples/jupyter_example.ipynb`
5. Verify features:
   - Multi-select dropdown shows all ts_ids
   - Graph displays solid lines for actual values
   - Graph displays dotted lines for forecast values
   - Axes auto-adjust when selection changes
   - "Next" button loads next batch of timeseries
   - Works in both Jupyter inline mode and standalone browser

## Dependencies Summary

**Core**:
- polars >= 0.20.0 (LazyFrame support)
- dash >= 2.11.0 (built-in Jupyter support)
- plotly >= 5.18.0

**Development**:
- pytest >= 7.4.0
- pytest-cov >= 4.1.0

## Notes

- Each commit includes both implementation and tests
- Tests must pass before committing
- Lazy loading ensures efficient memory usage for large datasets
- Dash 2.11+ eliminates need for separate JupyterDash package
- Column names are fully configurable via function parameters
