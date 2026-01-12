"""
Dash callbacks for interactive timeseries visualization.
"""

from typing import List, Optional
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go

from ..core.data_manager import TimeseriesDataManager
from .app import create_figure


def register_callbacks(app, data_manager: TimeseriesDataManager, display_count: int):
    """
    Register all Dash callbacks for the app.

    Args:
        app: Dash application instance
        data_manager: TimeseriesDataManager for data access
        display_count: Number of timeseries to show per page
    """

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
            # Return empty figure with message
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="No timeseries selected",
                xaxis_title="Time",
                yaxis_title="Value"
            )
            return empty_fig

        # Get data for selected timeseries
        df = data_manager.get_ts_data(selected_ids)

        # Create and return figure
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
