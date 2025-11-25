import json

import plotly.graph_objs as go
from dash import html, dcc, callback, Output, Input, no_update

from models import Roast
from utils.temp_utils import ROAST_EVENTS, ROAST_STAGES, ROAST_TEMPS, f_to_c

FAHRENHEIT_DISPLAY = True
Y_PADDING = 5

def create_temperature_plot(roasts_data: list[Roast] | list[dict], show_legend: bool = False):
    """
    Creates a Plotly figure for historical roast data.
    Args:
        roasts_data: A list of Roasts or dicts, each containing:
            {'start_time', 'bean_info', 'time_data', 'temp_data', 'event_markers'}
            'time_data' can be datetime objects or float
            '
    """

    num_roasts = len(roasts_data)
    colors = [f"hsl({h * 20}, 70%, 50%)" for h in range(1, num_roasts+1)]

    fig = go.Figure()
    all_temp_values = []
    for i, roast in enumerate(roasts_data):
        if isinstance(roast, Roast):
            roast = convert_object_to_dict(roast)


        all_temp_values.extend(roast["temp_data"])

        # Add main temperature trace for this roast
        legend_name = f"{roast["start_time"].strftime('%Y-%m-%d %H:%M')} - {roast["bean_info"]}"
        fig.add_trace(go.Scatter(
            x=roast["time_data"],
            y=roast["temp_data"],
            mode="lines",
            name=legend_name,
            line={"color": colors[i]},
            showlegend=True,
        ))

        # Add event markers for this roast (1st crack, 2nd crack)
        for event_name in ["first_crack_start", "second_crack_start"]:
            event_time = roast[f"{event_name}_time"]
            event_temp = roast[f"{event_name}_temp"]
            if event_time is None or event_temp is None:
                continue

            fig.add_trace(go.Scatter(
                x=[event_time],
                y=[event_temp],
                mode='markers',
                marker={"symbol": "star", "size": 10, "color": colors[i], "line": {"width": 1, "color": "white"}},
                name=f"{event_name} ({legend_name})",
                showlegend=False
            ))
            fig.add_annotation(
                x=event_time,
                y=event_temp,
                text=f'{event_name}',
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-30,
                font={"color": colors[i], "size": 9},
                bgcolor="rgba(255, 255, 255, 0.7)",
                opacity=0.8
            )

    # Add common elements like roast stage hlines and annotations if there's any data
    y_range = [0, 100]
    if all_temp_values:
        min_overall_temp = min(all_temp_values)
        max_overall_temp = max(all_temp_values)
        y_range = [min_overall_temp - Y_PADDING, max_overall_temp + Y_PADDING]

        # Roast stage hlines and annotations (these are constant for all roasts)
        roast_temps = ROAST_TEMPS
        if not FAHRENHEIT_DISPLAY:
            roast_temps = [f_to_c(t) for t in ROAST_TEMPS]

        for temp, stage_name in zip(roast_temps, ROAST_STAGES):
            fig.add_hline(y=temp, line_width=2, line_dash="dash", line_color="brown", opacity=0.5)
            # Annotations are placed at the left edge of the plot
            fig.add_annotation(
                x=0,
                xref="paper",
                y=temp,
                text=stage_name,
                showarrow=False,
                yshift=10,
                xanchor="left",
                font={"color": "brown", "size": 10},
                opacity=0.7
            )

    fig.update_layout(
        xaxis={"tickformat": "%H:%M"},
        yaxis_title=f"Temperature (°{'F' if FAHRENHEIT_DISPLAY else 'C'})",
        yaxis={"range": y_range},
        margin={"l": 20, "r": 20, "b": 20, "t": 20},
        hovermode="x unified",
        # legend=dict(x=1.02, y=1, xanchor='left', yanchor='top', bgcolor='rgba(255,255,255,0.8)', bordercolor='rgba(0,0,0,0.1)', borderwidth=1)
    )
    if type(roasts_data[0]["time_data"]) == float:
        fig.update_layout(xaxis_title="Time [min]")
    else:
        fig.update_layout(xaxis={"tickformat": "%H:%M"})
    if show_legend:
        fig.update_layout(showlegend=False)
    return fig


def convert_object_to_dict(roast: Roast) -> dict:
    keys = [
        "start_time",
        "bean_info",
        "first_crack_start_time",
        "first_crack_start_temp",
        "second_crack_start_time",
        "second_crack_start_temp"
    ]

    result = {}
    for key in keys:
        result[key] = getattr(roast, key)

    result["time_data"] = json.loads(roast.sec_from_start)
    result["temp_data"] = json.loads(roast.temperature_f)

    return result
