"""
Dash callbacks for interactive timeseries visualization.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import polars as pl

from ..core.data_manager import TimeseriesDataManager, ExceptionDataManager
from .app import create_figure
from .components import (
    create_map_figure,
    create_main_page_content,
    create_exception_page_content
)


def parse_time_input(time_str: Optional[str], default: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a time input string.

    Args:
        time_str: Input string in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MI:SS'
        default: Default value to use if time_str is empty

    Returns:
        Tuple of (parsed_time_str, error_msg)
        If parsing fails, returns (None, error_message)
        If input is empty, returns (default, None)
    """
    if not time_str or time_str.strip() == '':
        return default, None

    time_str = time_str.strip()

    # Try full format first
    try:
        datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        return time_str, None
    except ValueError:
        pass

    # Try date-only format, append 00:00:00
    try:
        datetime.strptime(time_str, '%Y-%m-%d')
        return f"{time_str} 00:00:00", None
    except ValueError:
        return None, f"Invalid format: '{time_str}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"


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


def register_routing_callbacks(
    app,
    data_manager: TimeseriesDataManager,
    exception_manager: ExceptionDataManager,
    display_count: int,
    ranking_df: Optional[pl.DataFrame] = None,
    geo_df: Optional[pl.DataFrame] = None,
    ts_ids: Optional[List[str]] = None,
    has_features: bool = False,
    full_time_range: Optional[dict] = None
):
    """
    Register callbacks for multi-page routing with exception analysis.

    Args:
        app: Dash application instance
        data_manager: TimeseriesDataManager for main data access
        exception_manager: ExceptionDataManager for exception data
        display_count: Number of timeseries to show per page
        ranking_df: Optional DataFrame with ranking data
        geo_df: Optional DataFrame with geographic data for map
        ts_ids: List of all timeseries IDs
        has_features: Whether feature columns are configured
        full_time_range: Dict with 'min' and 'max' timestamp strings
    """
    ts_id_col = data_manager.config.ts_id

    # Callback 0: URL Routing - render appropriate page based on pathname
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname'),
        State('ts-ids-store', 'data'),
    )
    def display_page(pathname, ts_ids_store):
        """Render appropriate page based on URL."""
        if pathname == '/exceptions':
            return create_exception_page_content(ts_ids=ts_ids_store)
        # Default: main page
        return create_main_page_content(
            ts_ids=ts_ids_store,
            display_count=display_count,
            ranking_df=ranking_df,
            ts_id_col=ts_id_col,
            has_features=has_features,
            geo_df=geo_df,
            full_time_range=full_time_range,
            has_exceptions=True
        )

    # =========================================================================
    # Main Page Callbacks (same as register_callbacks but with allow_duplicate)
    # =========================================================================

    if has_features:
        @app.callback(
            Output('timeseries-graph', 'figure'),
            [Input('ts-selector', 'value'),
             Input('features-toggle', 'value')],
            prevent_initial_call=True
        )
        def update_graph_with_features(selected_ids: Optional[List[str]], features_toggle: Optional[List[str]]) -> go.Figure:
            """Update graph when timeseries selection or features toggle changes."""
            if not selected_ids:
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="No timeseries selected",
                    xaxis_title="Time",
                    yaxis_title="Value"
                )
                return empty_fig

            df = data_manager.get_ts_data(selected_ids)
            show_features = features_toggle and 'show' in features_toggle
            if show_features:
                return create_figure(df, data_manager.config)
            else:
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
            prevent_initial_call=True
        )
        def update_graph(selected_ids: Optional[List[str]]) -> go.Figure:
            """Update graph when timeseries selection changes."""
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
        """Handle 'Next' button clicks for pagination."""
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate

        new_offset = current_offset + display_count_state
        new_ids = data_manager.get_paginated_ids(new_offset, display_count_state)

        if not new_ids:
            new_offset = 0
            new_ids = data_manager.get_paginated_ids(new_offset, display_count_state)

        return new_ids, new_offset

    # Time range callback for main page
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
        """Update time range based on user inputs or reset button."""
        triggered_id = ctx.triggered_id

        if triggered_id == 'time-reset-button':
            return None, '', '', ''

        default_start = full_range.get('min') if full_range else None
        default_end = full_range.get('max') if full_range else None

        start_time, start_error = parse_time_input(start_input, default_start)
        end_time, end_error = parse_time_input(end_input, default_end)

        if start_error:
            return no_update, start_error, no_update, no_update
        if end_error:
            return no_update, end_error, no_update, no_update

        if start_time and end_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                if start_dt >= end_dt:
                    return no_update, 'Start time must be before end time', no_update, no_update
            except ValueError:
                pass

        time_range = {'start': start_time, 'end': end_time}
        return time_range, '', no_update, no_update

    # Apply time range to main graph
    @app.callback(
        Output('timeseries-graph', 'figure', allow_duplicate=True),
        Input('time-range-store', 'data'),
        State('timeseries-graph', 'figure'),
        prevent_initial_call=True
    )
    def apply_time_range_to_graph(time_range: Optional[dict], current_fig: Optional[dict]):
        """Apply time range filter to the main graph x-axis."""
        if current_fig is None:
            raise PreventUpdate

        fig = go.Figure(current_fig)

        if time_range is None:
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

    # Register ranking callbacks if ranking_df is provided
    if ranking_df is not None:
        @app.callback(
            Output('ranking-table', 'data'),
            Input('ranking-sort-order', 'value'),
            State('ranking-store', 'data'),
        )
        def handle_sort_order_change(sort_order: str, ranking_data: List[dict]) -> List[dict]:
            """Re-sort ranking table when sort order changes."""
            df = pl.DataFrame(ranking_data)
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
            """Update visualization when user clicks on ranked item."""
            if not selected_rows:
                raise PreventUpdate

            row_idx = selected_rows[0]
            ts_id = table_data[row_idx][ts_id_col]
            return [ts_id]

    # Register map callbacks if geo_df is provided
    if geo_df is not None:
        @app.callback(
            Output('map-graph', 'figure'),
            Input('ts-selector', 'value'),
            State('geo-store', 'data'),
            State('ts-id-col', 'data'),
            prevent_initial_call=True
        )
        def update_map_highlight(selected_ids: Optional[List[str]], geo_data: List[dict], ts_id_col_state: str) -> go.Figure:
            """Update map highlighting when dropdown selection changes."""
            geo_df_local = pl.DataFrame(geo_data)
            return create_map_figure(geo_df_local, selected_ids, ts_id_col_state)

        @app.callback(
            Output('ts-selector', 'value', allow_duplicate=True),
            Input('map-graph', 'clickData'),
            prevent_initial_call=True
        )
        def handle_map_click(click_data) -> List[str]:
            """Update dropdown selection when map point is clicked."""
            if click_data is None:
                raise PreventUpdate

            point = click_data['points'][0]
            ts_id = point.get('customdata')

            if ts_id is None:
                raise PreventUpdate

            return [ts_id]

    # =========================================================================
    # Exception Page Callbacks
    # =========================================================================

    @app.callback(
        [Output('exception-map', 'figure'),
         Output('exception-time-error', 'children'),
         Output('exception-time-start', 'value'),
         Output('exception-time-end', 'value')],
        [Input('exception-time-start', 'value'),
         Input('exception-time-end', 'value'),
         Input('exception-ts-selector', 'value'),
         Input('exception-ts-graph', 'relayoutData')],
        [State('geo-store', 'data'),
         State('ts-id-col', 'data'),
         State('full-time-range', 'data')],
        prevent_initial_call=True
    )
    def update_exception_map(
        start_input: Optional[str],
        end_input: Optional[str],
        selected_ts_ids: Optional[List[str]],
        relayout_data: Optional[dict],
        geo_data: List[dict],
        ts_id_col_state: str,
        full_range: Optional[dict]
    ):
        """Recalculate exception colors when timeframe changes or graph is zoomed."""
        triggered_id = ctx.triggered_id

        # If triggered by graph relayout, extract time range from it
        if triggered_id == 'exception-ts-graph' and relayout_data:
            # Extract x-axis range from relayout data
            xaxis_start = relayout_data.get('xaxis.range[0]')
            xaxis_end = relayout_data.get('xaxis.range[1]')

            # Handle autorange reset
            if relayout_data.get('xaxis.autorange'):
                start_input = ''
                end_input = ''
            elif xaxis_start and xaxis_end:
                # Use the selected range (truncate to datetime string format)
                start_input = xaxis_start[:19] if len(str(xaxis_start)) > 19 else str(xaxis_start)
                end_input = xaxis_end[:19] if len(str(xaxis_end)) > 19 else str(xaxis_end)

        # Parse time inputs
        default_start = full_range.get('min') if full_range else None
        default_end = full_range.get('max') if full_range else None

        start_time, start_error = parse_time_input(start_input, default_start)
        end_time, end_error = parse_time_input(end_input, default_end)

        if start_error:
            return no_update, start_error, no_update, no_update
        if end_error:
            return no_update, end_error, no_update, no_update

        # Validate start < end
        if start_time and end_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                if start_dt >= end_dt:
                    return no_update, 'Start time must be before end time', no_update, no_update
            except ValueError:
                pass

        # Get aggregated exceptions for timeframe (triggers LazyFrame collect)
        exception_sums = exception_manager.get_aggregated_exceptions(start_time, end_time)

        # Join with geo_df to get color values
        geo_df_local = pl.DataFrame(geo_data)

        # Join exception sums with geo data
        geo_with_exceptions = geo_df_local.join(
            exception_sums,
            on=ts_id_col_state,
            how='left'
        ).with_columns(
            pl.col('exception_sum').fill_null(0).alias('color_value')
        ).drop('exception_sum')

        # Create map figure with updated colors
        selected_ids = selected_ts_ids if selected_ts_ids else []
        fig = create_map_figure(geo_with_exceptions, selected_ids, ts_id_col_state)

        # Return updated time inputs if triggered by graph relayout
        if triggered_id == 'exception-ts-graph':
            return fig, '', start_input or '', end_input or ''
        return fig, '', no_update, no_update

    @app.callback(
        Output('exception-ts-graph', 'figure'),
        [Input('exception-ts-selector', 'value'),
         Input('exception-time-start', 'value'),
         Input('exception-time-end', 'value')],
        State('full-time-range', 'data'),
        prevent_initial_call=True
    )
    def update_exception_graph(
        selected_ts_ids: Optional[List[str]],
        start_input: Optional[str],
        end_input: Optional[str],
        full_range: Optional[dict]
    ):
        """Update timeseries graph on exception page with synced time range."""
        if not selected_ts_ids:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="No timeseries selected",
                xaxis_title="Time",
                yaxis_title="Value"
            )
            return empty_fig

        # Get data for selected timeseries
        df = data_manager.get_ts_data(selected_ts_ids)

        # Create figure without features (cleaner view for exception analysis)
        from ..core.config import ColumnConfig
        config_without_features = ColumnConfig(
            timestamp=data_manager.config.timestamp,
            ts_id=data_manager.config.ts_id,
            actual=data_manager.config.actual,
            forecast=data_manager.config.forecast,
            extrema=data_manager.config.extrema,
            features=None
        )
        fig = create_figure(df, config_without_features)

        # Parse time inputs and apply to x-axis
        default_start = full_range.get('min') if full_range else None
        default_end = full_range.get('max') if full_range else None

        start_time, _ = parse_time_input(start_input, default_start)
        end_time, _ = parse_time_input(end_input, default_end)

        if start_time and end_time:
            fig.update_xaxes(range=[start_time, end_time])
        elif start_time:
            fig.update_xaxes(range=[start_time, None])
        elif end_time:
            fig.update_xaxes(range=[None, end_time])

        return fig

    @app.callback(
        Output('exception-ts-selector', 'value'),
        Input('exception-map', 'clickData'),
        prevent_initial_call=True
    )
    def exception_map_click_handler(click_data) -> List[str]:
        """Update dropdown when map point clicked."""
        if click_data is None:
            raise PreventUpdate

        point = click_data['points'][0]
        ts_id = point.get('customdata')

        if ts_id is None:
            raise PreventUpdate

        return [ts_id]
