"""Page to collect data."""

import collections
import datetime
import json
import logging
import threading

import dash
import dash_daq as daq
from dash import dcc, html, callback, Output, Input, State, ctx
from models import Roast, get_db

from utils.temp_utils import ROAST_EVENTS, continually_read_temperature
from utils.plot_utils import create_temperature_plot

pi = False
PLOT_WINDOW_SEC = 60*3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

dash.register_page(__name__)


def initialize_roast_event_markers():
    return {
        roast_event_id(event): {
            "name": event,
            "data": (None, None),  # Temp, Time
        }
        for event in ROAST_EVENTS
    }


def roast_event_id(event: str) -> str:
    """Format the event name to be id friendly."""
    return f"{event.lower().replace(' ', '-')}_button"


roast_event_markers = initialize_roast_event_markers()


@callback(
    Output("live-update-graph", "figure"),
    Input("interval-component", "n_intervals"),
)
def update_graph_live(_):
    """Callback to update the live temperature graph."""
    with data_lock:
        current_temp_plot = list(temp_plot)
        current_time_plot = list(time_plot)

    plot_data = {
            "start_time": current_time_plot[0],
            "time_data": current_time_plot,
            "temp_data": current_temp_plot,
            "bean_info": None,
            "first_crack_start_time": roast_event_markers["1st-crack-start_button"]["data"][1],
            "first_crack_start_temp": roast_event_markers["1st-crack-start_button"]["data"][0],
            "second_crack_start_time": roast_event_markers["2nd-crack-start_button"]["data"][1],
            "second_crack_start_temp": roast_event_markers["2nd-crack-start_button"]["data"][0],
    }

    return create_temperature_plot([plot_data])


@callback(
    Output("record-data-switch", "on", allow_duplicate=True),
    [
        [
            Output(event_button, "disabled", allow_duplicate=True)
            for event_button in roast_event_markers
        ]
    ],
    [
        [
            Output(event_button, "className", allow_duplicate=True)
            for event_button in roast_event_markers
        ]
    ],
    Input("record-data-switch", "on"),
    State("bean-info", "value"),
    prevent_initial_call=True,
)
def toggle_recording(is_on, bean_info):
    """Start or stop recording."""
    if is_on:
        recording.set()
    else:
        recording.clear()
    logging.info("Data recording set to: %s", is_on)

    num_markers = len(roast_event_markers)
    if not is_on:
        # Recording was just turned off
        write_data_to_db(bean_info)
        return is_on, [True]*num_markers, ["button-disabled"]*num_markers

    return is_on, [False]*num_markers, ["button-enabled"]*num_markers


@callback(
    [
        [
            Output(event_button, "disabled", allow_duplicate=True)
            for event_button in roast_event_markers
        ]
    ],
    [
        [
            Output(event_button, "className", allow_duplicate=True)
            for event_button in roast_event_markers
        ]
    ],
    [
        Input(event_button, "n_clicks")
        for event_button in roast_event_markers
    ],
    prevent_initial_call = True,
)
def event_button_clicked(*_):
    """Record time and temp when an event button is clicked."""
    # Record event
    event: str = ctx.triggered_id
    with data_lock:
        event_time = time_recorded[-1]
        event_temp = temp_recorded[-1]
    logging.info(
        "%s clicked at %s with temp %s",
        roast_event_markers[event]["name"],
        event_time,
        event_temp,
    )
    roast_event_markers[event]["data"] = (event_temp, event_time)

    # Disable button
    num_markers = len(roast_event_markers)
    disabled = [False]*num_markers
    class_name = ["button-enabled"]*num_markers
    for idx, event in enumerate(roast_event_markers):
        if roast_event_markers[event]["data"][0] is not None:
            disabled[idx] = True
            class_name[idx] = "button-disabled"

    return disabled, class_name


@callback(
    Output("record-data-switch", "on", allow_duplicate=True),
    Input("interval-component", "n_intervals"),
    State("record-data-switch", "on"),
    prevent_initial_call=True
)
def check_buffer_and_force_stop(n_intervals, current_switch_state):
    if force_stop_recording.is_set():
        logging.info("Force stop event seen. Turning off record switch.")
        force_stop_recording.clear()
        if current_switch_state:
            return False
    return dash.no_update


def write_data_to_db(bean_info: str | None):
    """Write temp_recorded and time_recorded to database."""
    global roast_event_markers

    data_to_write = {}
    with data_lock:
        if not temp_recorded:
            logging.warning("No data was found to be written to database.")
            return

        # Quickly copy data and clear originals inside the lock
        data_to_write["temp"] = list(temp_recorded)
        data_to_write["time"] = list(time_recorded)
        data_to_write["markers"] = roast_event_markers

        temp_recorded.clear()
        time_recorded.clear()
        roast_event_markers = initialize_roast_event_markers()

    logging.info("Writing %s data points to database...", len(data_to_write["temp"]))
    with next(get_db()) as db:
        crack_info = prep_crack_data(data_to_write["markers"], data_to_write["time"][0])

        new_roast = Roast(
            start_time=data_to_write["time"][0],
            sec_from_start=json.dumps(datetimes_to_elapsed_seconds(data_to_write["time"])),
            temperature_f=json.dumps(data_to_write["temp"]),
            bean_info=bean_info,
            first_crack_start_time=crack_info[0],
            first_crack_start_temp=crack_info[1],
            second_crack_start_time=crack_info[2],
            second_crack_start_temp=crack_info[3],
        )
        logging.debug(new_roast)
        db.add(new_roast)
        db.commit()


def prep_crack_data(events: dict, start_time: datetime.datetime) -> list[float]:
    """Prep crack data to write to db."""
    output = []
    for event in ["1st-crack-start_button", "2nd-crack-start_button"]:
        temp, t = events[event]["data"]
        delta_t = (t - start_time).total_seconds() if t else None
        output.extend([delta_t, temp])

    return output


def datetimes_to_elapsed_seconds(datetime_list: list[datetime.datetime]) -> list[float]:
    """
    Converts a list of datetime objects into a list of floats representing
    the elapsed seconds since the first element in the list.

    Args:
        datetime_list: A list of datetime.datetime objects (e.g., from datetime.datetime.now()).

    Returns:
        A list of floats where each value is the number of seconds elapsed
        since datetime_list[0]. Returns an empty list if the input is empty.
    """
    if not datetime_list:
        return []

    reference_time = datetime_list[0]

    elapsed_seconds_list = []
    for current_time in datetime_list:
        time_delta = current_time - reference_time
        elapsed_seconds = time_delta.total_seconds()
        elapsed_seconds_list.append(elapsed_seconds)

    return elapsed_seconds_list


def initialize_deques(num: int, maxlen: int) -> list[collections.deque]:
    """
    Initialize deques

    Args:
        num (int): Number of deques to generate.
        maxlen (int): The maximum length for each deque.
    """
    return [collections.deque(maxlen=maxlen) for _ in range(num)]


layout = html.Div([
    dcc.Graph(id="live-update-graph"),
    dcc.Interval(
        id="interval-component",
        interval=1000,
        n_intervals=0
    ),
    html.Div(
        [
            daq.BooleanSwitch(
                id="record-data-switch",
                on=False,
                label="Record Data",
                labelPosition="top"
            ),
            html.Div(
                [
                    html.Button(
                        event,
                        id=roast_event_id(event),
                        className="button-disabled",
                        disabled=True,
                    )
                    for event in ROAST_EVENTS
                ],
                id="roast-stage-container",
            ),
            dcc.Textarea(id="bean-info", placeholder="Enter bean information", style={"width": "50%"}),
        ],
        className="data-collection-container",
    )
])


temp_recorded, time_recorded = initialize_deques(2, 60*30)
temp_plot, time_plot = initialize_deques(2, PLOT_WINDOW_SEC)
data_lock = threading.Lock()
recording = threading.Event()
force_stop_recording = threading.Event()

temperature_thread = threading.Thread(
    target=continually_read_temperature,
    args=(
        data_lock,
        temp_plot,
        time_plot,
        temp_recorded,
        time_recorded,
        recording,
        force_stop_recording,
        pi,
    ),
    daemon=True,
)
temperature_thread.start()
