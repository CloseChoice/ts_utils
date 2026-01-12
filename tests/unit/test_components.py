"""
Unit tests for Dash UI components.
"""

import pytest
from dash import dcc, html

from ts_utils.visualization.components import (
    create_ts_selector,
    create_graph_component,
    create_next_button,
    create_layout
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
