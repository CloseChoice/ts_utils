"""
Dash UI components for timeseries visualization.
"""

from typing import List
from dash import dcc, html


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


def create_graph_component() -> dcc.Graph:
    """
    Create the main graph component for displaying timeseries.

    Returns:
        Dash Graph component
    """
    return dcc.Graph(
        id='timeseries-graph',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
        },
        style={'height': '600px'}
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


def create_layout(ts_ids: List[str], display_count: int) -> html.Div:
    """
    Create the complete Dash layout with all components.

    Args:
        ts_ids: List of all available timeseries IDs
        display_count: Number of timeseries to display at once

    Returns:
        Dash Div component containing the complete layout
    """
    return html.Div([
        html.H1(
            'Interactive Timeseries Visualization',
            style={'textAlign': 'center', 'marginBottom': '20px'}
        ),

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

        html.Div([
            create_graph_component()
        ], style={'margin': '20px'}),

        # Hidden stores for state management
        dcc.Store(id='current-offset', data=0),
        dcc.Store(id='display-count', data=display_count),
    ])
