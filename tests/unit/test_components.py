"""
Unit tests for Dash UI components.
"""

import pytest
from dash import dcc, html

import polars as pl
from dash import dash_table

from ts_utils.visualization.components import (
    create_ts_selector,
    create_graph_component,
    create_next_button,
    create_layout,
    create_sort_order_toggle,
    create_ranking_table,
)


def test_create_ts_selector_basic():
    """Test creating a basic timeseries selector dropdown."""
    ts_ids = ["ts_1", "ts_2", "ts_3", "ts_4", "ts_5"]
    display_count = 3

    selector = create_ts_selector(ts_ids, display_count)

    assert isinstance(selector, dcc.Dropdown)
    assert selector.id == 'ts-selector'
    assert selector.multi is True
    assert len(selector.options) == 5
    assert selector.value == ["ts_1", "ts_2", "ts_3"]  # First 3 by default


def test_create_ts_selector_empty_list():
    """Test selector with empty timeseries list."""
    selector = create_ts_selector([], 3)

    assert isinstance(selector, dcc.Dropdown)
    assert len(selector.options) == 0
    assert selector.value == []


def test_create_ts_selector_display_count_exceeds_available():
    """Test when display_count is larger than available timeseries."""
    ts_ids = ["ts_1", "ts_2"]
    display_count = 5

    selector = create_ts_selector(ts_ids, display_count)

    # Should select all available (only 2)
    assert selector.value == ["ts_1", "ts_2"]


def test_create_ts_selector_options_format():
    """Test that options are formatted correctly."""
    ts_ids = ["series_a", "series_b"]
    selector = create_ts_selector(ts_ids, 2)

    assert selector.options == [
        {'label': 'series_a', 'value': 'series_a'},
        {'label': 'series_b', 'value': 'series_b'}
    ]


def test_create_graph_component():
    """Test creating the graph component."""
    graph = create_graph_component()

    assert isinstance(graph, dcc.Graph)
    assert graph.id == 'timeseries-graph'
    assert 'displayModeBar' in graph.config
    assert graph.config['displayModeBar'] is True
    assert graph.config['displaylogo'] is False


def test_create_next_button():
    """Test creating the next button."""
    button = create_next_button()

    assert isinstance(button, html.Button)
    assert button.id == 'next-button'
    assert button.children == 'Next'
    assert button.n_clicks == 0


def test_create_layout_structure():
    """Test that layout has correct structure."""
    ts_ids = ["ts_1", "ts_2", "ts_3"]
    display_count = 2

    layout = create_layout(ts_ids, display_count)

    assert isinstance(layout, html.Div)
    assert len(layout.children) > 0

    # Check that layout contains expected components
    # This is a simplified check - full testing would require traversing the tree
    children_types = [type(child).__name__ for child in layout.children]

    assert 'H1' in children_types  # Title
    assert 'Div' in children_types  # Container divs
    assert 'Store' in children_types  # State stores


def test_create_layout_includes_stores():
    """Test that layout includes Store components for state management."""
    layout = create_layout(["ts_1"], 2)

    # Find Store components in layout
    stores = [child for child in layout.children if isinstance(child, dcc.Store)]

    assert len(stores) == 2

    # Check store IDs
    store_ids = {store.id for store in stores}
    assert 'current-offset' in store_ids
    assert 'display-count' in store_ids


def test_create_layout_with_many_timeseries():
    """Test layout creation with many timeseries."""
    ts_ids = [f"ts_{i}" for i in range(100)]
    display_count = 10

    layout = create_layout(ts_ids, display_count)

    assert isinstance(layout, html.Div)

    # Find the dropdown in the layout
    def find_components(component, component_type):
        """Recursively find all components of a given type."""
        results = []
        if isinstance(component, component_type):
            results.append(component)
        if hasattr(component, 'children'):
            children = component.children
            if not isinstance(children, list):
                children = [children]
            for child in children:
                if child is not None:
                    results.extend(find_components(child, component_type))
        return results

    dropdowns = find_components(layout, dcc.Dropdown)
    assert len(dropdowns) == 1

    dropdown = dropdowns[0]
    assert len(dropdown.options) == 100
    assert len(dropdown.value) == 10  # First 10 selected


def test_create_sort_order_toggle():
    """Test creating the sort order toggle."""
    toggle = create_sort_order_toggle()

    assert isinstance(toggle, html.Div)

    # Find RadioItems in children
    radio_items = None
    for child in toggle.children:
        if isinstance(child, dcc.RadioItems):
            radio_items = child
            break

    assert radio_items is not None
    assert radio_items.id == 'ranking-sort-order'
    assert radio_items.value == 'desc'  # Default to descending
    assert len(radio_items.options) == 2
    assert radio_items.options[0]['value'] == 'desc'
    assert radio_items.options[1]['value'] == 'asc'


def test_create_ranking_table_basic():
    """Test creating a basic ranking table."""
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'ranking': [2.5, 1.0, 3.2]
    })

    table = create_ranking_table(ranking_df, 'ts_id')

    assert isinstance(table, dash_table.DataTable)
    assert table.id == 'ranking-table'
    assert table.row_selectable == 'single'
    assert table.selected_rows == [0]
    assert len(table.columns) == 2
    assert len(table.data) == 3


def test_create_ranking_table_data_format():
    """Test that ranking table data is formatted correctly."""
    ranking_df = pl.DataFrame({
        'ts_id': ['series_a', 'series_b'],
        'score': [10.5, 5.2]
    })

    table = create_ranking_table(ranking_df, 'ts_id')

    assert table.data == [
        {'ts_id': 'series_a', 'score': 10.5},
        {'ts_id': 'series_b', 'score': 5.2}
    ]


def test_create_layout_with_ranking():
    """Test that layout includes ranking panel when ranking_df is provided."""
    ts_ids = ["ts_1", "ts_2", "ts_3"]
    display_count = 2
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'ranking': [3.0, 1.0, 2.0]
    })

    layout = create_layout(ts_ids, display_count, ranking_df=ranking_df, ts_id_col='ts_id')

    assert isinstance(layout, html.Div)

    # Find Store components - should have 3 (current-offset, display-count, ranking-store)
    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    assert len(stores) == 3

    store_ids = {store.id for store in stores}
    assert 'ranking-store' in store_ids


def test_create_layout_without_ranking():
    """Test that layout does not include ranking panel when ranking_df is None."""
    ts_ids = ["ts_1", "ts_2"]
    display_count = 2

    layout = create_layout(ts_ids, display_count, ranking_df=None)

    # Should only have 2 stores (no ranking-store)
    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    assert len(stores) == 2

    store_ids = {store.id for store in stores}
    assert 'ranking-store' not in store_ids
