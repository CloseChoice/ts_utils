"""
Dash UI components for timeseries visualization.
"""

from typing import List, Optional
import polars as pl
from dash import dcc, html, dash_table


def create_ts_selector(ts_ids: List[str], display_count: int) -> dcc.Dropdown:
    """
    Create multi-select dropdown for timeseries selection.

    Args:
        ts_ids: List of all available timeseries IDs
        display_count: Number of timeseries to initially display

    Returns:
        Dash Dropdown component configured for multi-select
    """
    # Select first N timeseries by default
    initial_value = ts_ids[:display_count] if ts_ids else []

    return dcc.Dropdown(
        id='ts-selector',
        options=[{'label': ts_id, 'value': ts_id} for ts_id in ts_ids],
        value=initial_value,
        multi=True,
        placeholder='Select timeseries to display...',
        style={'width': '100%'}
    )


def create_graph_component() -> dcc.Loading:
    """
    Create the main graph component for displaying timeseries with loading spinner.

    Returns:
        Dash Loading component wrapping the Graph
    """
    return dcc.Loading(
        id='graph-loading',
        type='default',
        children=dcc.Graph(
            id='timeseries-graph',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
            },
            style={'height': '750px'}
        )
    )


def create_next_button() -> html.Button:
    """
    Create the 'Next' button for pagination through timeseries.

    Returns:
        Dash Button component
    """
    return html.Button(
        'Next',
        id='next-button',
        n_clicks=0,
        style={
            'margin': '10px',
            'padding': '10px 20px',
            'fontSize': '16px',
            'cursor': 'pointer'
        }
    )


def create_features_toggle() -> html.Div:
    """
    Create toggle for showing/hiding features subplot.

    Returns:
        Dash Div component with checkbox for features toggle
    """
    return html.Div([
        dcc.Checklist(
            id='features-toggle',
            options=[{'label': ' Show Features', 'value': 'show'}],
            value=[],  # Empty = unchecked (off by default)
            style={'display': 'inline-block'}
        )
    ], style={'margin': '10px 20px'})


def create_sort_order_toggle() -> html.Div:
    """
    Create sort order toggle (Desc/Asc) for ranking table.

    Returns:
        Dash Div component with radio items for sort order selection
    """
    return html.Div([
        html.Label('Sort: ', style={'marginRight': '8px', 'fontWeight': 'bold'}),
        dcc.RadioItems(
            id='ranking-sort-order',
            options=[
                {'label': '▼ Desc', 'value': 'desc'},
                {'label': '▲ Asc', 'value': 'asc'},
            ],
            value='desc',
            inline=True,
            style={'display': 'inline-block'}
        )
    ], style={'marginBottom': '10px'})


def create_ranking_table(ranking_df: pl.DataFrame, ts_id_col: str) -> dash_table.DataTable:
    """
    Create clickable ranking table.

    Args:
        ranking_df: DataFrame with ts_id and ranking columns
        ts_id_col: Name of the timeseries ID column

    Returns:
        Dash DataTable component with selectable rows
    """
    columns = [{'name': col, 'id': col} for col in ranking_df.columns]

    return dash_table.DataTable(
        id='ranking-table',
        columns=columns,
        data=ranking_df.to_dicts(),
        row_selectable='single',
        selected_rows=[0],
        style_table={'height': '500px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
        page_size=50,
    )


def create_layout(ts_ids: List[str], display_count: int, ranking_df: Optional[pl.DataFrame] = None, ts_id_col: str = 'ts_id', has_features: bool = False) -> html.Div:
    """
    Create the complete Dash layout with all components.

    Args:
        ts_ids: List of all available timeseries IDs
        display_count: Number of timeseries to display at once
        ranking_df: Optional DataFrame with ts_id and ranking columns for sidebar
        ts_id_col: Name of the timeseries ID column
        has_features: Whether feature columns are configured (shows toggle if True)

    Returns:
        Dash Div component containing the complete layout
    """
    # Build main content components
    main_components = [
        html.Div([
            html.Label(
                'Select Timeseries:',
                style={'fontWeight': 'bold', 'marginBottom': '5px'}
            ),
            create_ts_selector(ts_ids, display_count),
        ], style={'margin': '20px'}),

        html.Div([
            create_next_button(),
            html.Span(
                f'(Shows next {display_count} timeseries)',
                style={'marginLeft': '10px', 'color': '#666'}
            )
        ], style={'margin': '20px'}),
    ]

    # Add features toggle if features are configured
    if has_features:
        main_components.append(create_features_toggle())

    # Add graph component
    main_components.append(
        html.Div([
            create_graph_component()
        ], style={'margin': '20px'})
    )

    main_content = html.Div(main_components)

    # Hidden stores for state management
    stores = [
        dcc.Store(id='current-offset', data=0),
        dcc.Store(id='display-count', data=display_count),
        dcc.Store(id='has-features', data=has_features),
    ]

    if ranking_df is not None:
        # Add ranking store for re-sorting
        stores.append(dcc.Store(id='ranking-store', data=ranking_df.to_dicts()))

        # Layout with ranking sidebar
        ranking_sidebar = html.Div([
            html.H3('Ranking', style={'marginBottom': '15px'}),
            create_sort_order_toggle(),
            create_ranking_table(ranking_df, ts_id_col),
        ], style={
            'width': '25%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '20px',
            'borderRight': '1px solid #ddd',
        })

        main_content_styled = html.Div([main_content], style={
            'width': '75%',
            'display': 'inline-block',
            'verticalAlign': 'top',
        })

        content_area = html.Div([
            ranking_sidebar,
            main_content_styled,
        ], style={'display': 'flex'})
    else:
        # Original layout without ranking
        content_area = main_content

    return html.Div([
        html.H1(
            'Interactive Timeseries Visualization',
            style={'textAlign': 'center', 'marginBottom': '20px'}
        ),
        content_area,
        *stores,
    ])
