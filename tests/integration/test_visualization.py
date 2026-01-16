"""
Integration tests for complete visualization workflow.
"""

import pytest
import polars as pl
from dash import Dash
import plotly.graph_objs as go

from ts_utils.core.config import ColumnConfig
from ts_utils.core.data_manager import TimeseriesDataManager
from ts_utils.visualization.components import create_layout
from ts_utils.visualization.callbacks import register_callbacks
from ts_utils.visualization.app import create_figure


def test_complete_workflow_with_callbacks(sample_ts_dataframe, column_config):
    """Test complete integration of data manager, components, and callbacks."""
    # Create data manager
    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # Create Dash app
    app = Dash(__name__)
    display_count = 2

    # Create layout
    ts_ids = data_manager.get_all_ts_ids()
    app.layout = create_layout(ts_ids, display_count)

    # Register callbacks
    register_callbacks(app, data_manager, display_count)

    # Verify app was created successfully
    assert app is not None
    assert hasattr(app, 'callback_map')
    assert len(app.callback_map) > 0


def test_data_manager_with_figure_creation(sample_ts_dataframe, column_config):
    """Test that data manager integrates with figure creation."""
    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # Get some timeseries
    selected_ids = ["ts_1", "ts_2"]
    df = data_manager.get_ts_data(selected_ids)

    # Create figure
    fig = create_figure(df, column_config)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4  # 2 timeseries * 2 traces


def test_pagination_with_data_manager(large_ts_dataframe, column_config):
    """Test pagination workflow with data manager."""
    data_manager = TimeseriesDataManager(large_ts_dataframe, column_config)

    display_count = 3

    # Get first page
    page_1 = data_manager.get_paginated_ids(0, display_count)
    assert len(page_1) == 3

    # Get data for first page
    df_1 = data_manager.get_ts_data(page_1)
    assert df_1.shape[0] > 0

    # Get second page
    page_2 = data_manager.get_paginated_ids(display_count, display_count)
    assert len(page_2) == 3

    # Pages should be different
    assert set(page_1) != set(page_2)


def test_callback_update_graph_logic(sample_ts_dataframe, column_config):
    """Test the logic of the update_graph callback."""
    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # Simulate callback with selected IDs
    selected_ids = ["ts_1"]
    df = data_manager.get_ts_data(selected_ids)
    fig = create_figure(df, column_config)

    assert len(fig.data) == 2  # 1 timeseries * 2 traces
    assert "ts_1 (actual)" in [trace.name for trace in fig.data]

    # Simulate callback with no selection
    df_empty = data_manager.get_ts_data([])
    fig_empty = create_figure(df_empty, column_config)

    assert len(fig_empty.data) == 0


def test_callback_next_button_logic(large_ts_dataframe, column_config):
    """Test the logic of the handle_next_button callback."""
    data_manager = TimeseriesDataManager(large_ts_dataframe, column_config)
    display_count = 3

    # Simulate first click (offset 0 -> 3)
    current_offset = 0
    new_offset = current_offset + display_count
    new_ids = data_manager.get_paginated_ids(new_offset, display_count)

    assert len(new_ids) == 3
    assert new_offset == 3

    # Simulate second click (offset 3 -> 6)
    current_offset = new_offset
    new_offset = current_offset + display_count
    new_ids = data_manager.get_paginated_ids(new_offset, display_count)

    assert len(new_ids) == 3
    assert new_offset == 6


def test_callback_next_button_wraparound(sample_ts_dataframe, column_config):
    """Test that next button wraps around to start when reaching end."""
    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)
    display_count = 2

    # Go to end (offset beyond available data)
    current_offset = 10  # Beyond the 3 timeseries
    new_ids = data_manager.get_paginated_ids(current_offset, display_count)

    # Should return empty, indicating need to wrap around
    assert len(new_ids) == 0

    # Simulate wrap around to start
    new_offset = 0
    new_ids = data_manager.get_paginated_ids(new_offset, display_count)

    assert len(new_ids) == 2


def test_end_to_end_visualization_flow(sample_ts_dataframe, column_config):
    """Test complete end-to-end visualization flow."""
    # Step 1: Create data manager
    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # Step 2: Get available timeseries
    all_ids = data_manager.get_all_ts_ids()
    assert len(all_ids) == 3

    # Step 3: Select initial timeseries
    display_count = 2
    selected_ids = all_ids[:display_count]

    # Step 4: Get data for selected timeseries
    df = data_manager.get_ts_data(selected_ids)
    assert df.shape[0] == 20  # 2 timeseries * 10 rows

    # Step 5: Create figure
    fig = create_figure(df, column_config)
    assert len(fig.data) == 4  # 2 timeseries * 2 traces

    # Step 6: Simulate "Next" button - get next page
    next_offset = display_count
    next_ids = data_manager.get_paginated_ids(next_offset, display_count)
    assert len(next_ids) == 1  # Only 1 remaining

    # Step 7: Update selection
    df_next = data_manager.get_ts_data(next_ids)
    fig_next = create_figure(df_next, column_config)
    assert len(fig_next.data) == 2  # 1 timeseries * 2 traces


def test_workflow_with_ranking_panel(sample_ts_dataframe, column_config):
    """Test complete workflow with ranking panel enabled."""
    # Create ranking DataFrame
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_3', 'ts_1', 'ts_2'],
        'score': [10.0, 5.0, 2.0]
    })

    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    app = Dash(__name__)
    display_count = 2

    ts_ids = data_manager.get_all_ts_ids()
    app.layout = create_layout(ts_ids, display_count, ranking_df=ranking_df, ts_id_col='ts_id')

    register_callbacks(app, data_manager, display_count, ranking_df=ranking_df)

    # Verify callbacks were registered (should have more callbacks with ranking)
    assert app is not None
    assert len(app.callback_map) > 2  # More callbacks with ranking


def test_ranking_sort_order_change_logic():
    """Test the logic of sorting ranking data."""
    ranking_data = [
        {'ts_id': 'ts_1', 'score': 5.0},
        {'ts_id': 'ts_2', 'score': 10.0},
        {'ts_id': 'ts_3', 'score': 2.0},
    ]

    # Simulate descending sort
    df = pl.DataFrame(ranking_data)
    sorted_desc = df.sort('score', descending=True).to_dicts()

    assert sorted_desc[0]['ts_id'] == 'ts_2'
    assert sorted_desc[1]['ts_id'] == 'ts_1'
    assert sorted_desc[2]['ts_id'] == 'ts_3'

    # Simulate ascending sort
    sorted_asc = df.sort('score', descending=False).to_dicts()

    assert sorted_asc[0]['ts_id'] == 'ts_3'
    assert sorted_asc[1]['ts_id'] == 'ts_1'
    assert sorted_asc[2]['ts_id'] == 'ts_2'


def test_ranking_selection_logic(sample_ts_dataframe, column_config):
    """Test the logic of selecting a timeseries from ranking table."""
    data_manager = TimeseriesDataManager(sample_ts_dataframe, column_config)

    # Simulate ranking table data
    table_data = [
        {'ts_id': 'ts_3', 'score': 10.0},
        {'ts_id': 'ts_1', 'score': 5.0},
        {'ts_id': 'ts_2', 'score': 2.0},
    ]

    # Simulate clicking row 0
    selected_rows = [0]
    ts_id = table_data[selected_rows[0]]['ts_id']
    assert ts_id == 'ts_3'

    # Verify we can get data for that timeseries
    df = data_manager.get_ts_data([ts_id])
    assert df.shape[0] == 10
    assert df['ts_id'].unique().to_list() == ['ts_3']

    # Simulate clicking row 2
    selected_rows = [2]
    ts_id = table_data[selected_rows[0]]['ts_id']
    assert ts_id == 'ts_2'
