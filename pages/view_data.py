# TODO add tasting notes options

import dash
from dash import html, dcc, callback, Output, Input, no_update
import json
import plotly.graph_objs as go
from models import Roast, get_db
from utils.temp_utils import ROAST_STAGES, ROAST_TEMPS
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
            # Format label: "YYYY-MM-DD HH:MM - Bean Info"
            label = f"{roast.start_time.strftime('%Y-%m-%d %H:%M')}"
            if roast.bean_info:
                label += f" - {roast.bean_info[:10]}"
            options.append({"label": label, "value": roast.id})
    return options


def create_historical_temperature_plot(roasts_data: list[Roast]):
    """
    Creates a Plotly figure for historical roast data.
    Args:
        roasts_data: A list of dicts, where each dict contains:
            {'id', 'start_time', 'bean_info', 'time_data', 'temp_data', 'event_markers'}
            'time_data' here are already datetime objects.
    """
    fig = go.Figure()
    all_temp_values = []

    # Generate distinct colors for each roast for better differentiation
    num_roasts = len(roasts_data)
    colors = [f'hsl({h * 360 / num_roasts}, 70%, 50%)' for h in range(num_roasts)]


    for i, roast in enumerate(roasts_data):
        start_time = roast.start_time
        bean_info = roast.bean_info
        time_data = json.loads(roast.sec_from_start)
        temp_data = json.loads(roast.temperature_f)
        event_markers = {
                "1st Crack Start": {
                    "time_from_start": roast.first_crack_start_time,
                    "temp": roast.first_crack_start_temp
                },
                "2nd Crack Start": {
                    "time_from_start": roast.second_crack_start_time,
                    "temp": roast.second_crack_start_temp
                }
            }

        all_temp_values.extend(temp_data)

        # Add main temperature trace for this roast
        legend_name = f"{start_time.strftime('%Y-%m-%d %H:%M')} - {bean_info}"
        fig.add_trace(go.Scatter(
            x=time_data,
            y=temp_data,
            mode='lines',
            name=legend_name,
            line=dict(color=colors[i]), # Assign a unique color
            showlegend=True
        ))

        # Add event markers for this roast (1st crack, 2nd crack)
        for event_name, event_data in event_markers.items():
            if event_data['time_from_start'] is not None and event_data['temp'] is not None:
                # Reconstruct datetime from start_time and elapsed seconds
                # Event temp is already in F from models.py structure, so use directly
                fig.add_trace(go.Scatter(
                    x=[event_data['time_from_start']],
                    y=[event_data['temp']],
                    mode='markers',
                    marker=dict(symbol='star', size=10, color='red', line=dict(width=1, color='white')),
                    name=f"{event_name} ({legend_name})",
                    showlegend=False
                ))
                fig.add_annotation(
                    x=event_data['time_from_start'],
                    y=event_data['temp'],
                    text=f'{event_name}',
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-30,
                    font=dict(color="red", size=9),
                    bgcolor="rgba(255, 255, 255, 0.7)",
                    opacity=0.8
                )
    
    # Add common elements like roast stage hlines and annotations if there's any data
    y_range = [0, 100] # Default range
    if all_temp_values:
        min_overall_temp = min(all_temp_values)
        max_overall_temp = max(all_temp_values)
        y_range = [min_overall_temp - Y_PADDING, max_overall_temp + Y_PADDING]

        # Roast stage hlines and annotations (these are constant for all roasts)
        for temp_f, stage_name in zip(ROAST_TEMPS, ROAST_STAGES): # ROAST_TEMPS are in F
            fig.add_hline(y=temp_f, line_width=2, line_dash="dash", line_color="brown", opacity=0.5)
            # Annotations are placed at the left edge of the plot
            fig.add_annotation(
                x=0, # Left edge of the plot
                xref="paper",
                y=temp_f,
                text=stage_name,
                showarrow=False,
                yshift=10,
                xanchor="left",
                font={"color": "brown", "size": 10},
                opacity=0.7
            )

    fig.update_layout(
        xaxis_title="Time [s]",
        yaxis_title=f"Temperature (°{'F' if FAHRENHEIT_DISPLAY else 'C'})",
        yaxis=dict(range=y_range),
        margin={"l": 20, "r": 20, "b": 20, "t": 20},
        hovermode="x unified",
        legend=dict(x=1.02, y=1, xanchor='left', yanchor='top', bgcolor='rgba(255,255,255,0.8)', bordercolor='rgba(0,0,0,0.1)', borderwidth=1, title="Roasts")
    )
    return dcc.Graph(id="historical-roast-plot", figure=fig)


@callback(
    Output("historical-plot", "children"),
    Input("historical-roasts-checklist", "value"),
    prevent_initial_call=True,
)
def update_historical_plot(selected_roast_ids: list[int]):
    """Update the historical roast plot based on selected roast IDs."""
    if not selected_roast_ids:
        return default_plot_message

    with next(get_db()) as db:
        # Fetch selected roasts, ordered by start time for consistent plotting
        selected_roasts = (
            db.query(Roast)
            .filter(Roast.id.in_(selected_roast_ids))
            .order_by(Roast.start_time.asc()).all()
        )

    return create_historical_temperature_plot(selected_roasts)

default_plot_message = html.H1("Select data to see plot")
layout = html.Div(
    [
        html.Div(
            [
                html.H3("Historical Data"),
                # TODO add refresh button
                dcc.Checklist(
                    id="historical-roasts-checklist",
                    options=get_historical_roasts_options(),
                    value=[],
                    inline=False,
                    style={'maxHeight': '80vh', 'overflowY': 'auto', 'paddingRight': '10px'}
                ),
            ],
            className="database-entries-container"
        ),
        html.Div(
            [default_plot_message],
            id="historical-plot",
            className="previous-plot-container",
        )
    ],
    className="previous-data-container",
)
