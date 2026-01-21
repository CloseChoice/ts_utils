"""
Dash callbacks for interactive timeseries visualization.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import polars as pl

from ..core.data_manager import TimeseriesDataManager
from .app import create_figure
from .components import create_map_figure


def parse_time_input(time_str: Optional[str], default: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a time input string.

    Args:
        time_str: Input string in format 'YYYY-MM-DD HH:MI:SS'
        default: Default value to use if time_str is empty

    Returns:
        Tuple of (parsed_time_str, error_msg)
        If parsing fails, returns (None, error_message)
        If input is empty, returns (default, None)
    """
    if not time_str or time_str.strip() == '':
        return default, None

    time_str = time_str.strip()
    try:
        # Try parsing the format YYYY-MM-DD HH:MI:SS
        datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        return time_str, None
    except ValueError:
        return None, f"Invalid format: '{time_str}'. Use YYYY-MM-DD HH:MI:SS"


def register_callbacks(
    app,
    data_manager: TimeseriesDataManager,
    display_count: int,
    ranking_df: Optional[pl.DataFrame] = None,
    geo_df: Optional[pl.DataFrame] = None
):
    """
    Register all Dash callbacks for the app.

    Args:
        app: Dash application instance
        data_manager: TimeseriesDataManager for data access
        display_count: Number of timeseries to show per page
        ranking_df: Optional DataFrame with ranking data
        geo_df: Optional DataFrame with geographic data for map
    """
    has_features = data_manager.config.features is not None and len(data_manager.config.features) > 0

    if has_features:
        @app.callback(
            Output('timeseries-graph', 'figure'),
            [Input('ts-selector', 'value'),
             Input('features-toggle', 'value')],
            prevent_initial_call=False
        )
        def update_graph_with_features(selected_ids: Optional[List[str]], features_toggle: Optional[List[str]]) -> go.Figure:
            """
            Update graph when timeseries selection or features toggle changes.

            Args:
                selected_ids: List of selected timeseries IDs from dropdown
                features_toggle: List containing 'show' if features enabled, empty otherwise

            Returns:
                Updated Plotly figure
            """
            if not selected_ids:
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="No timeseries selected",
                    xaxis_title="Time",
                    yaxis_title="Value"
                )
                return empty_fig

            df = data_manager.get_ts_data(selected_ids)

            # Only use features if toggle is enabled
            show_features = features_toggle and 'show' in features_toggle
            if show_features:
                return create_figure(df, data_manager.config)
            else:
                # Create config without features for performance
                from ..core.config import ColumnConfig
                config_without_features = ColumnConfig(
                    timestamp=data_manager.config.timestamp,
                    ts_id=data_manager.config.ts_id,
                    actual=data_manager.config.actual,
                    forecast=data_manager.config.forecast,
                    extrema=data_manager.config.extrema,
                    features=None
                )
                return create_figure(df, config_without_features)
    else:
        @app.callback(
            Output('timeseries-graph', 'figure'),
            Input('ts-selector', 'value'),
            prevent_initial_call=False
        )
        def update_graph(selected_ids: Optional[List[str]]) -> go.Figure:
            """
            Update graph when timeseries selection changes.

            Args:
                selected_ids: List of selected timeseries IDs from dropdown

            Returns:
                Updated Plotly figure
            """
            if not selected_ids:
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="No timeseries selected",
                    xaxis_title="Time",
                    yaxis_title="Value"
                )
                return empty_fig

            df = data_manager.get_ts_data(selected_ids)
            return create_figure(df, data_manager.config)

    @app.callback(
        [Output('ts-selector', 'value'),
         Output('current-offset', 'data')],
        Input('next-button', 'n_clicks'),
        [State('current-offset', 'data'),
         State('display-count', 'data')],
        prevent_initial_call=True
    )
    def handle_next_button(n_clicks: Optional[int],
                          current_offset: int,
                          display_count_state: int) -> tuple:
        """
        Handle 'Next' button clicks for pagination.

        Args:
            n_clicks: Number of times button has been clicked
            current_offset: Current pagination offset
            display_count_state: Number of timeseries to display per page

        Returns:
            Tuple of (new_selected_ids, new_offset)
        """
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate

        # Calculate new offset
        new_offset = current_offset + display_count_state

        # Get next page of IDs
        new_ids = data_manager.get_paginated_ids(new_offset, display_count_state)

        # If no more IDs, loop back to start
        if not new_ids:
            new_offset = 0
            new_ids = data_manager.get_paginated_ids(new_offset, display_count_state)

        return new_ids, new_offset

    # Time range callback
    @app.callback(
        [Output('time-range-store', 'data'),
         Output('time-range-error', 'children'),
         Output('time-start-input', 'value'),
         Output('time-end-input', 'value')],
        [Input('time-start-input', 'value'),
         Input('time-end-input', 'value'),
         Input('time-reset-button', 'n_clicks')],
        [State('full-time-range', 'data'),
         State('time-range-store', 'data')],
        prevent_initial_call=True
    )
    def update_time_range(
        start_input: Optional[str],
        end_input: Optional[str],
        reset_clicks: Optional[int],
        full_range: Optional[dict],
        current_range: Optional[dict]
    ):
        """
        Update time range based on user inputs or reset button.

        Returns:
            Tuple of (time_range_store, error_message, start_value, end_value)
        """
        triggered_id = ctx.triggered_id

        # Handle reset button
        if triggered_id == 'time-reset-button':
            return None, '', '', ''

        # Get defaults from full range
        default_start = full_range.get('min') if full_range else None
        default_end = full_range.get('max') if full_range else None

        # Parse inputs
        start_time, start_error = parse_time_input(start_input, default_start)
        end_time, end_error = parse_time_input(end_input, default_end)

        # Check for parsing errors
        if start_error:
            return no_update, start_error, no_update, no_update
        if end_error:
            return no_update, end_error, no_update, no_update

        # Validate start < end (only if both are provided and not defaults)
        if start_time and end_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                if start_dt >= end_dt:
                    return no_update, 'Start time must be before end time', no_update, no_update
            except ValueError:
                pass  # Already validated in parse_time_input

        # Build time range
        time_range = {'start': start_time, 'end': end_time}

        return time_range, '', no_update, no_update

    # Callback to apply time range to graph
    @app.callback(
        Output('timeseries-graph', 'figure', allow_duplicate=True),
        Input('time-range-store', 'data'),
        State('timeseries-graph', 'figure'),
        prevent_initial_call=True
    )
    def apply_time_range_to_graph(time_range: Optional[dict], current_fig: Optional[dict]):
        """
        Apply time range filter to the graph x-axis.
        """
        if current_fig is None:
            raise PreventUpdate

        fig = go.Figure(current_fig)

        if time_range is None:
            # Reset to auto range
            fig.update_xaxes(autorange=True)
        else:
            start = time_range.get('start')
            end = time_range.get('end')
            if start and end:
                fig.update_xaxes(range=[start, end])
            elif start:
                fig.update_xaxes(range=[start, None])
            elif end:
                fig.update_xaxes(range=[None, end])
            else:
                fig.update_xaxes(autorange=True)

        return fig

    # Register ranking callbacks only if ranking_df is provided
    if ranking_df is not None:
        ts_id_col = data_manager.config.ts_id

        @app.callback(
            Output('ranking-table', 'data'),
            Input('ranking-sort-order', 'value'),
            State('ranking-store', 'data'),
        )
        def handle_sort_order_change(sort_order: str, ranking_data: List[dict]) -> List[dict]:
            """
            Re-sort ranking table when sort order changes.

            Args:
                sort_order: 'asc' or 'desc'
                ranking_data: Original ranking data from store

            Returns:
                Sorted ranking data as list of dicts
            """
            df = pl.DataFrame(ranking_data)
            # Find the ranking column (the one that's not ts_id)
            ranking_col = [c for c in df.columns if c != ts_id_col][0]
            sorted_df = df.sort(ranking_col, descending=(sort_order == 'desc'))
            return sorted_df.to_dicts()

        @app.callback(
            Output('ts-selector', 'value', allow_duplicate=True),
            Input('ranking-table', 'selected_rows'),
            State('ranking-table', 'data'),
            prevent_initial_call=True
        )
        def handle_ranking_selection(selected_rows: Optional[List[int]], table_data: List[dict]) -> List[str]:
            """
            Update visualization when user clicks on ranked item.

            Args:
                selected_rows: List of selected row indices
                table_data: Current table data

            Returns:
                List containing the selected timeseries ID
            """
            if not selected_rows:
                raise PreventUpdate

            row_idx = selected_rows[0]
            ts_id = table_data[row_idx][ts_id_col]
            return [ts_id]

    # Register map callbacks if geo_df is provided
    if geo_df is not None:
        ts_id_col = data_manager.config.ts_id

        @app.callback(
            Output('map-graph', 'figure'),
            Input('ts-selector', 'value'),
            State('geo-store', 'data'),
            State('ts-id-col', 'data'),
            prevent_initial_call=False
        )
        def update_map_highlight(selected_ids: Optional[List[str]], geo_data: List[dict], ts_id_col_state: str) -> go.Figure:
            """
            Update map highlighting when dropdown selection changes.

            Args:
                selected_ids: List of selected timeseries IDs
                geo_data: Geographic data from store
                ts_id_col_state: Name of the ts_id column

            Returns:
                Updated map figure with highlighted points
            """
            geo_df_local = pl.DataFrame(geo_data)
            return create_map_figure(geo_df_local, selected_ids, ts_id_col_state)

        @app.callback(
            Output('ts-selector', 'value', allow_duplicate=True),
            Input('map-graph', 'clickData'),
            prevent_initial_call=True
        )
        def handle_map_click(click_data) -> List[str]:
            """
            Update dropdown selection when map point is clicked.

            Args:
                click_data: Click event data from map

            Returns:
                List containing the clicked timeseries ID
            """
            if click_data is None:
                raise PreventUpdate

            # Extract ts_id from customdata
            point = click_data['points'][0]
            ts_id = point.get('customdata')

            if ts_id is None:
                raise PreventUpdate

            return [ts_id]
