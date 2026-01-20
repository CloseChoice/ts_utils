"""
Dash UI components for timeseries visualization.
"""

from typing import List, Optional
import polars as pl
from dash import dcc, html, dash_table
import plotly.graph_objects as go


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


def create_time_range_inputs() -> html.Div:
    """
    Create time range input fields for filtering the chart timeframe.

    Returns:
        Dash Div component with start/end time inputs and reset button
    """
    input_style = {
        'width': '200px',
        'padding': '8px',
        'marginRight': '10px',
        'border': '1px solid #ccc',
        'borderRadius': '4px',
    }

    return html.Div([
        html.Div([
            html.Label('Time Range:', style={'fontWeight': 'bold', 'marginRight': '15px'}),
            dcc.Input(
                id='time-start-input',
                type='text',
                placeholder='YYYY-MM-DD HH:MI:SS',
                debounce=True,
                style=input_style
            ),
            html.Span('to', style={'marginRight': '10px'}),
            dcc.Input(
                id='time-end-input',
                type='text',
                placeholder='YYYY-MM-DD HH:MI:SS',
                debounce=True,
                style=input_style
            ),
            html.Button(
                'Reset',
                id='time-reset-button',
                n_clicks=0,
                style={
                    'padding': '8px 16px',
                    'cursor': 'pointer',
                    'backgroundColor': '#f0f0f0',
                    'border': '1px solid #ccc',
                    'borderRadius': '4px',
                }
            ),
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div(
            id='time-range-error',
            style={'color': 'red', 'marginTop': '5px', 'minHeight': '20px'}
        ),
    ], style={'margin': '10px 20px'})


def create_map_component() -> dcc.Graph:
    """
    Create the map graph component for displaying geographic locations.

    Returns:
        Dash Graph component for the map
    """
    return dcc.Graph(
        id='map-graph',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
        },
        style={'height': '400px'}
    )


def create_map_figure(
    geo_df: pl.DataFrame,
    selected_ts_ids: Optional[List[str]] = None,
    ts_id_col: str = 'ts_id'
) -> go.Figure:
    """
    Create the map figure with timeseries locations.

    Args:
        geo_df: DataFrame with ts_id, latitude, longitude, and optionally color_value
        selected_ts_ids: List of currently selected timeseries IDs (for highlighting)
        ts_id_col: Name of the timeseries ID column

    Returns:
        Plotly Figure with scattermapbox
    """
    if selected_ts_ids is None:
        selected_ts_ids = []

    # Determine marker sizes based on selection
    ts_ids = geo_df[ts_id_col].to_list()
    sizes = [18 if ts_id in selected_ts_ids else 10 for ts_id in ts_ids]

    # Check if we have color values
    has_color = "color_value" in geo_df.columns

    if has_color:
        color_values = geo_df["color_value"].to_list()
        marker_dict = {
            'size': sizes,
            'color': color_values,
            'colorscale': 'RdYlGn_r',  # Reversed: green (low) to red (high)
            'showscale': True,
            'colorbar': {
                'title': 'Exceptions',
                'thickness': 15,
                'len': 0.7,
            }
        }
    else:
        marker_dict = {
            'size': sizes,
            'color': '#1f77b4',  # Default blue
        }

    fig = go.Figure(go.Scattermapbox(
        lat=geo_df["latitude"].to_list(),
        lon=geo_df["longitude"].to_list(),
        mode='markers',
        marker=marker_dict,
        text=ts_ids,
        customdata=ts_ids,
        hovertemplate='<b>%{text}</b><extra></extra>',
    ))

    # Calculate center from data bounds
    lat_center = (geo_df["latitude"].min() + geo_df["latitude"].max()) / 2
    lon_center = (geo_df["longitude"].min() + geo_df["longitude"].max()) / 2

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=lat_center, lon=lon_center),
            zoom=8,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    return fig


def create_layout(
    ts_ids: List[str],
    display_count: int,
    ranking_df: Optional[pl.DataFrame] = None,
    ts_id_col: str = 'ts_id',
    has_features: bool = False,
    geo_df: Optional[pl.DataFrame] = None,
    extrema_summary: Optional[pl.DataFrame] = None,
    full_time_range: Optional[dict] = None
) -> html.Div:
    """
    Create the complete Dash layout with all components.

    Args:
        ts_ids: List of all available timeseries IDs
        display_count: Number of timeseries to display at once
        ranking_df: Optional DataFrame with ts_id and ranking columns for sidebar
        ts_id_col: Name of the timeseries ID column
        has_features: Whether feature columns are configured (shows toggle if True)
        geo_df: Optional DataFrame with ts_id, latitude, longitude for map display
        extrema_summary: Optional DataFrame with ts_id, timestamp, has_extrema for recalculation
        full_time_range: Optional dict with 'min' and 'max' timestamp strings for the full data range

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

    # Add time range inputs
    main_components.append(create_time_range_inputs())

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
        dcc.Store(id='time-range-store', data=None),
        dcc.Store(id='full-time-range', data=full_time_range),
    ]

    if ranking_df is not None:
        # Add ranking store for re-sorting
        stores.append(dcc.Store(id='ranking-store', data=ranking_df.to_dicts()))

    # Add geo store if geo data provided
    if geo_df is not None:
        stores.append(dcc.Store(id='geo-store', data=geo_df.to_dicts()))
        stores.append(dcc.Store(id='ts-id-col', data=ts_id_col))

    # Add extrema summary store if provided (for time-filtered exception recalculation)
    if extrema_summary is not None:
        stores.append(dcc.Store(id='extrema-summary-store', data=extrema_summary.to_dicts()))
    else:
        stores.append(dcc.Store(id='extrema-summary-store', data=None))

    has_sidebar = ranking_df is not None or geo_df is not None

    if has_sidebar:
        # Build sidebar components
        sidebar_components = []

        if ranking_df is not None:
            sidebar_components.extend([
                html.H3('Ranking', style={'marginBottom': '15px'}),
                create_sort_order_toggle(),
                create_ranking_table(ranking_df, ts_id_col),
            ])

        if geo_df is not None:
            # Add map section
            if ranking_df is not None:
                # Add separator if we already have ranking
                sidebar_components.append(html.Hr(style={'margin': '20px 0'}))
            sidebar_components.extend([
                html.H3('Map', style={'marginBottom': '15px'}),
                create_map_component(),
            ])

        # Layout with sidebar
        sidebar = html.Div(
            sidebar_components,
            style={
                'width': '25%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'padding': '20px',
                'borderRight': '1px solid #ddd',
            }
        )

        main_content_styled = html.Div([main_content], style={
            'width': '75%',
            'display': 'inline-block',
            'verticalAlign': 'top',
        })

        content_area = html.Div([
            sidebar,
            main_content_styled,
        ], style={'display': 'flex'})
    else:
        # Original layout without sidebar
        content_area = main_content

    return html.Div([
        html.H1(
            'Interactive Timeseries Visualization',
            style={'textAlign': 'center', 'marginBottom': '20px'}
        ),
        content_area,
        *stores,
    ])
