"""Page to view saved data."""

import dash
from dash import html, dcc, callback, Output, Input
from models import Roast, get_db

from utils.plot_utils import convert_object_to_dict, create_temperature_plot, convert_all_roasts_to_dicts

dash.register_page(__name__)

# Constants for plotting (can be moved to utils/temp_utils if shared)
FAHRENHEIT_DISPLAY = True # Assuming historical data is stored/displayed in Fahrenheit
Y_PADDING = 5


def get_historical_roasts_options() -> list[dict]:
    """Queries the database for historical roasts and returns options for dcc.Checklist."""
    options = []
    with next(get_db()) as db:
        roasts = db.query(Roast).order_by(Roast.start_time.desc()).all()
        for roast in roasts:
            label = f"{roast.start_time.strftime('%Y-%m-%d %H:%M')}"
            if roast.bean_info:
                label += f" - {roast.bean_info[:10]}"
            options.append({"label": label, "value": roast.id})
    return options


def create_historical_temperature_plot(roasts_data: list[dict]):
    """
    Creates a Plotly figure for historical roast data.
    Args:
        roasts_data: A list of dicts, where each dict contains:
            {'id', 'start_time', 'bean_info', 'time_data', 'temp_data', 'event_markers'}
            'time_data' here are already datetime objects.
    """
    fig = create_temperature_plot(roasts_data, realtime=False)

    return dcc.Graph(id="historical-roast-plot", figure=fig)


def gather_roast_info(roasts_data: list[dict]) -> list:
    """Gather roast info to display below the plot."""
    all_roast_data = []
    for roast in roasts_data:
        roast_id = roast["id"]

        this_roast = html.Div(
            [
                html.Div(
                    [
                        html.H3(roast["start_time"]),
                        html.Img(
                            src="assets/trash.svg",
                            id=f"delete-{roast_id}",
                            className="icon-button",
                        ),
                    ],
                    className="div-with-icon",
                ),
                html.Div(
                    [
                        dcc.Textarea(
                            id=f"bean-info-{roast_id}",
                            value=roast["bean_info"],
                            className="bean-info-entry",
                        ),
                        html.Img(
                            src="assets/submit.svg",
                            id=f"update-{roast_id}",
                            className="icon-button",
                        ),
                    ],
                    className="div-with-icon",
                )
            ],
            className="roast-info",
        )

        all_roast_data.append(this_roast)

    return all_roast_data


@callback(
    Output("historical-plot", "children"),
    Output("roast-info-container", "children"),
    Input("historical-roasts-checklist", "value"),
    prevent_initial_call=True,
)
def update_historical_plot(selected_roast_ids: list[int]):
    """Update the historical roast plot based on selected roast IDs."""
    if not selected_roast_ids:
        return default_plot_message, []

    with next(get_db()) as db:
        # Fetch selected roasts, ordered by start time for consistent plotting
        selected_roasts = (
            db.query(Roast)
            .filter(Roast.id.in_(selected_roast_ids))
            .order_by(Roast.start_time.asc()).all()
        )

    roast_dicts = convert_all_roasts_to_dicts(selected_roasts)
    plot = create_historical_temperature_plot(roast_dicts)
    roast_info = gather_roast_info(roast_dicts)

    return plot, roast_info


@callback(
    Output("historical-roasts-checklist", "options"),
    Input("refresh-history", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_history(_):
    """Refresh historical options on button click."""
    return get_historical_roasts_options()


default_plot_message = html.H1("Select data to see plot")

sidebar = html.Div(
    [
        html.Div(
            [
                html.H3("Historical Data"),
                html.Img(
                    src="assets/refresh.svg",
                    id="refresh-history",
                    className="icon-button",
                ),
            ],
            className="div-with-icon",
        ),
        dcc.Loading(
            id="loading",
            type="dot",
            children=html.Div(
                [
                    dcc.Checklist(
                        id="historical-roasts-checklist",
                        options=get_historical_roasts_options(),
                        value=[],
                        inline=False,
                    ),
                ]
            )
        ),
    ],
    className="database-entries-container"
)

main_content = html.Div(
    [
        html.Div(
            [default_plot_message],
            id="historical-plot",
            className="previous-plot-container",
        ),
        html.Div(
            [],
            id="roast-info-container"
        ),
    ],
    className="display-container",
)

layout = html.Div(
    [sidebar, main_content],
    className="previous-data-container",
)
