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
    create_features_toggle,
    create_time_range_inputs,
    create_map_figure,
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
    """Test creating the graph component with loading spinner."""
    loading = create_graph_component()

    assert isinstance(loading, dcc.Loading)
    assert loading.id == 'graph-loading'

    # Get the graph inside the loading wrapper
    graph = loading.children
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

    assert len(stores) == 6

    # Check store IDs
    store_ids = {store.id for store in stores}
    assert 'current-offset' in store_ids
    assert 'display-count' in store_ids
    assert 'has-features' in store_ids
    assert 'time-range-store' in store_ids
    assert 'full-time-range' in store_ids
    assert 'extrema-summary-store' in store_ids


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

    # Find Store components - should have 7 (base 6 + ranking-store)
    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    assert len(stores) == 7

    store_ids = {store.id for store in stores}
    assert 'ranking-store' in store_ids
    assert 'has-features' in store_ids
    assert 'time-range-store' in store_ids
    assert 'full-time-range' in store_ids
    assert 'extrema-summary-store' in store_ids


def test_create_layout_without_ranking():
    """Test that layout does not include ranking panel when ranking_df is None."""
    ts_ids = ["ts_1", "ts_2"]
    display_count = 2

    layout = create_layout(ts_ids, display_count, ranking_df=None)

    # Should have 6 stores (no ranking-store, but has time-related stores)
    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    assert len(stores) == 6

    store_ids = {store.id for store in stores}
    assert 'ranking-store' not in store_ids
    assert 'has-features' in store_ids
    assert 'time-range-store' in store_ids
    assert 'full-time-range' in store_ids
    assert 'extrema-summary-store' in store_ids


def test_create_ranking_table_multiple_columns():
    """Test ranking table with multiple additional columns."""
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2'],
        'extrema_count': [10, 5],
        'error_rate': [0.15, 0.08],
        'label': ['high', 'low']
    })

    table = create_ranking_table(ranking_df, 'ts_id')

    assert len(table.columns) == 4
    column_ids = [c['id'] for c in table.columns]
    assert 'ts_id' in column_ids
    assert 'extrema_count' in column_ids
    assert 'error_rate' in column_ids
    assert 'label' in column_ids


def test_create_ranking_table_empty():
    """Test ranking table with empty DataFrame."""
    ranking_df = pl.DataFrame({
        'ts_id': [],
        'score': []
    }).cast({'ts_id': pl.Utf8, 'score': pl.Float64})

    table = create_ranking_table(ranking_df, 'ts_id')

    assert len(table.data) == 0
    assert len(table.columns) == 2


def test_create_ranking_table_single_row():
    """Test ranking table with single row."""
    ranking_df = pl.DataFrame({
        'ts_id': ['only_one'],
        'metric': [42.0]
    })

    table = create_ranking_table(ranking_df, 'ts_id')

    assert len(table.data) == 1
    assert table.data[0]['ts_id'] == 'only_one'
    assert table.selected_rows == [0]


def test_create_layout_with_ranking_stores_data():
    """Test that ranking store contains the correct data."""
    ranking_df = pl.DataFrame({
        'ts_id': ['ts_a', 'ts_b'],
        'value': [1.5, 2.5]
    })

    layout = create_layout(['ts_a', 'ts_b'], 2, ranking_df=ranking_df, ts_id_col='ts_id')

    # Find the ranking store
    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    ranking_store = next((s for s in stores if s.id == 'ranking-store'), None)

    assert ranking_store is not None
    assert ranking_store.data == [
        {'ts_id': 'ts_a', 'value': 1.5},
        {'ts_id': 'ts_b', 'value': 2.5}
    ]


def test_create_features_toggle():
    """Test features toggle component creation."""
    toggle = create_features_toggle()

    assert isinstance(toggle, html.Div)

    # Find the checklist inside (children is a list)
    children = toggle.children
    if not isinstance(children, list):
        children = [children]
    checklist = children[0]
    assert isinstance(checklist, dcc.Checklist)
    assert checklist.id == 'features-toggle'
    assert checklist.value == []  # Off by default
    assert len(checklist.options) == 1
    assert checklist.options[0]['value'] == 'show'


def test_create_layout_with_features_shows_toggle():
    """Test that layout includes features toggle when has_features=True."""
    layout = create_layout(['ts_1', 'ts_2'], 2, has_features=True)

    # Find checklist components recursively
    def find_checklists(component):
        results = []
        if isinstance(component, dcc.Checklist):
            results.append(component)
        if hasattr(component, 'children'):
            children = component.children
            if not isinstance(children, list):
                children = [children] if children is not None else []
            for child in children:
                if child is not None:
                    results.extend(find_checklists(child))
        return results

    checklists = find_checklists(layout)
    toggle = next((c for c in checklists if c.id == 'features-toggle'), None)

    assert toggle is not None
    assert toggle.value == []  # Off by default


def test_create_layout_without_features_no_toggle():
    """Test that layout does not include features toggle when has_features=False."""
    layout = create_layout(['ts_1', 'ts_2'], 2, has_features=False)

    # Find checklist components recursively
    def find_checklists(component):
        results = []
        if isinstance(component, dcc.Checklist):
            results.append(component)
        if hasattr(component, 'children'):
            children = component.children
            if not isinstance(children, list):
                children = [children] if children is not None else []
            for child in children:
                if child is not None:
                    results.extend(find_checklists(child))
        return results

    checklists = find_checklists(layout)
    toggle = next((c for c in checklists if c.id == 'features-toggle'), None)

    assert toggle is None


def test_create_layout_has_features_store_value():
    """Test that has-features store has correct value."""
    # Without features
    layout_no_features = create_layout(['ts_1'], 2, has_features=False)
    stores = [child for child in layout_no_features.children if isinstance(child, dcc.Store)]
    has_features_store = next((s for s in stores if s.id == 'has-features'), None)
    assert has_features_store is not None
    assert has_features_store.data is False

    # With features
    layout_with_features = create_layout(['ts_1'], 2, has_features=True)
    stores = [child for child in layout_with_features.children if isinstance(child, dcc.Store)]
    has_features_store = next((s for s in stores if s.id == 'has-features'), None)
    assert has_features_store is not None
    assert has_features_store.data is True


def test_create_time_range_inputs():
    """Test creating time range input fields."""
    inputs = create_time_range_inputs()

    assert isinstance(inputs, html.Div)

    # Find Input components recursively
    def find_inputs(component):
        results = []
        if isinstance(component, dcc.Input):
            results.append(component)
        if hasattr(component, 'children'):
            children = component.children
            if not isinstance(children, list):
                children = [children] if children is not None else []
            for child in children:
                if child is not None:
                    results.extend(find_inputs(child))
        return results

    inputs_list = find_inputs(inputs)
    assert len(inputs_list) == 2

    # Check input IDs
    input_ids = {inp.id for inp in inputs_list}
    assert 'time-start-input' in input_ids
    assert 'time-end-input' in input_ids


def test_create_time_range_inputs_has_reset_button():
    """Test that time range inputs include reset button."""
    inputs = create_time_range_inputs()

    # Find Button components recursively
    def find_buttons(component):
        results = []
        if isinstance(component, html.Button):
            results.append(component)
        if hasattr(component, 'children'):
            children = component.children
            if not isinstance(children, list):
                children = [children] if children is not None else []
            for child in children:
                if child is not None:
                    results.extend(find_buttons(child))
        return results

    buttons = find_buttons(inputs)
    reset_button = next((b for b in buttons if b.id == 'time-reset-button'), None)

    assert reset_button is not None
    assert reset_button.children == 'Reset'


def test_create_time_range_inputs_has_error_div():
    """Test that time range inputs include error display div."""
    inputs = create_time_range_inputs()

    # Find all divs recursively
    def find_divs(component):
        results = []
        if isinstance(component, html.Div) and hasattr(component, 'id') and component.id:
            results.append(component)
        if hasattr(component, 'children'):
            children = component.children
            if not isinstance(children, list):
                children = [children] if children is not None else []
            for child in children:
                if child is not None:
                    results.extend(find_divs(child))
        return results

    divs = find_divs(inputs)
    error_div = next((d for d in divs if d.id == 'time-range-error'), None)

    assert error_div is not None


def test_create_map_figure_basic():
    """Test creating a basic map figure."""
    geo_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'latitude': [48.0, 49.0, 50.0],
        'longitude': [10.0, 11.0, 12.0],
    })

    fig = create_map_figure(geo_df, ts_id_col='ts_id')

    assert fig is not None
    assert len(fig.data) == 1  # Single scattermapbox trace


def test_create_map_figure_dynamic_centering():
    """Test that map is centered based on data bounds."""
    geo_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2'],
        'latitude': [40.0, 50.0],
        'longitude': [5.0, 15.0],
    })

    fig = create_map_figure(geo_df, ts_id_col='ts_id')

    # Center should be midpoint: lat=(40+50)/2=45, lon=(5+15)/2=10
    center = fig.layout.mapbox.center
    assert center.lat == 45.0
    assert center.lon == 10.0


def test_create_map_figure_with_color_values():
    """Test map figure with color values for exceptions."""
    geo_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'latitude': [48.0, 49.0, 50.0],
        'longitude': [10.0, 11.0, 12.0],
        'color_value': [5, 10, 15],
    })

    fig = create_map_figure(geo_df, ts_id_col='ts_id')

    # Should have colorbar when color_value is present
    assert fig.data[0].marker.showscale is True


def test_create_map_figure_without_color_values():
    """Test map figure without color values uses default blue."""
    geo_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2'],
        'latitude': [48.0, 49.0],
        'longitude': [10.0, 11.0],
    })

    fig = create_map_figure(geo_df, ts_id_col='ts_id')

    # Should use default blue color
    assert fig.data[0].marker.color == '#1f77b4'


def test_create_map_figure_with_selection():
    """Test map figure highlights selected timeseries."""
    geo_df = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_2', 'ts_3'],
        'latitude': [48.0, 49.0, 50.0],
        'longitude': [10.0, 11.0, 12.0],
    })

    fig = create_map_figure(geo_df, selected_ts_ids=['ts_2'], ts_id_col='ts_id')

    # Selected marker should be larger (18) than unselected (10)
    sizes = fig.data[0].marker.size
    assert list(sizes) == [10, 18, 10]


def test_create_layout_with_time_range_stores():
    """Test that layout includes time range stores with correct data."""
    full_time_range = {'min': '2024-01-01 00:00:00', 'max': '2024-12-31 23:59:59'}

    layout = create_layout(['ts_1'], 2, full_time_range=full_time_range)

    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    full_range_store = next((s for s in stores if s.id == 'full-time-range'), None)
    time_range_store = next((s for s in stores if s.id == 'time-range-store'), None)

    assert full_range_store is not None
    assert full_range_store.data == full_time_range
    assert time_range_store is not None
    assert time_range_store.data is None  # Initially None


def test_create_layout_with_extrema_summary():
    """Test that layout includes extrema summary store when provided."""
    extrema_summary = pl.DataFrame({
        'ts_id': ['ts_1', 'ts_1', 'ts_2'],
        'timestamp': ['2024-01-01 00:00:00', '2024-01-02 00:00:00', '2024-01-01 00:00:00'],
        'has_extrema': [True, False, True],
    })

    layout = create_layout(['ts_1', 'ts_2'], 2, extrema_summary=extrema_summary)

    stores = [child for child in layout.children if isinstance(child, dcc.Store)]
    extrema_store = next((s for s in stores if s.id == 'extrema-summary-store'), None)

    assert extrema_store is not None
    assert extrema_store.data is not None
    assert len(extrema_store.data) == 3
