"""
Dash callbacks for interactive timeseries visualization.
"""

from typing import List, Optional
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import polars as pl

from ..core.data_manager import TimeseriesDataManager
from .app import create_figure


def register_callbacks(app, data_manager: TimeseriesDataManager, display_count: int, ranking_df: Optional[pl.DataFrame] = None):
    """
    Register all Dash callbacks for the app.

    Args:
        app: Dash application instance
        data_manager: TimeseriesDataManager for data access
        display_count: Number of timeseries to show per page
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
