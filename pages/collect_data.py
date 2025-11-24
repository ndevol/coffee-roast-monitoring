pi = False

import collections
import datetime
import logging
import random
import time
import threading

import dash
import dash_daq as daq
import plotly.graph_objs as go

from dash import dcc, html, callback, Output, Input, ctx

from utils.temp_utils import ROAST_EVENTS, ROAST_STAGES, ROAST_TEMPS, c_to_f, f_to_c

if pi:
    import adafruit_max31856
    import board
    import digitalio


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

dash.register_page(__name__)


class MockThermocouple:
    """Mock thermocouple for local testing."""
    @property
    def temperature(self):
        """Randomly generate a temperature between 20 and 30."""
        return 200 + random.random() * 100


def initialize_roast_event_markers():
    return {
        roast_event_id(event): {
            "name": event,
            "data": None,
        } 
        for event in ROAST_EVENTS
    }


def roast_event_id(event: str) -> str:
    """Format the event name to be id friendly."""
    return f"{event.lower().replace(' ', '-')}_button"


roast_event_markers = initialize_roast_event_markers()


def continually_read_temperature(interval: float = 1.0, fahrenheit: bool = True) -> None:
    """
    Continually read temperature from thermocouple.
    
    Args:
        interval (float): Seconds between readings.
        fahrenheit (bool): Option to convert readings to fahrenheit.
    """
    global temp_plot, time_plot

    while True:
        try:
            reading_time = datetime.datetime.now()
            temp = thermocouple.temperature
            if fahrenheit:
                temp = c_to_f(temp)

            with data_lock:
                temp_plot.append(temp)
                time_plot.append(reading_time)

                if recording:
                    record_data(temp, reading_time)

            time.sleep(interval)

        except Exception as e:
            logging.error(f"Error reading temperature: {e}")
            time.sleep(interval)


@callback(
    Output("live-update-graph", "figure"),
    Input("interval-component", "n_intervals"),
)
def update_graph_live(_):
    """Callback to update the live temperature graph."""
    with data_lock:
        current_temp_plot = list(temp_plot)
        current_time_plot = list(time_plot)

    return create_temperature_plot(temp_data=current_temp_plot, time_data=current_time_plot)


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
    Input("record-data-switch", "on"),
    prevent_initial_call=True,
)
def toggle_recording(is_on):
    """Start or stop recording."""
    global recording

    with data_lock:
        recording = is_on
    logging.info(f"Data recording set to: {recording}")

    num_markers = len(roast_event_markers)
    if not is_on:
        # Recording was just turned off
        write_data_to_db()
        return [True]*num_markers, ["roast-stage-button-disabled"]*num_markers

    return [False]*num_markers, ["roast-stage-button-enabled"]*num_markers


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
def event_button_clicked(*n_clicks):
    """Record time and temp when an event button is clicked."""
    global roast_event_markers, recording
    # Record event
    event: str = ctx.triggered_id
    event_time = time_recorded[-1]
    event_temp = temp_recorded[-1]
    logging.info(
        "%s clicked at %s with temp %s",
        roast_event_markers[event]['name'],
        event_time,
        event_temp,
    )
    roast_event_markers[event]["data"] = (event_temp, event_time)

    # Disable button
    num_markers = len(roast_event_markers)
    disabled = [False]*num_markers
    class_name = ["roast-stage-button-enabled"]*num_markers
    for idx, event in enumerate(roast_event_markers):
        if roast_event_markers[event]["data"] is not None:
            disabled[idx] = True
            class_name[idx] = "roast-stage-button-disabled"

    return disabled, class_name


def initialize_plot_deques(maxlen_plot: int = 60*5) -> tuple[collections.deque, collections.deque]:
    """Initialize deques for storing time and temperature data for plotting."""
    temp_plot_local = collections.deque(maxlen=maxlen_plot)
    time_plot_local = collections.deque(maxlen=maxlen_plot)
    return temp_plot_local, time_plot_local


def initialize_thermocouple():
    """Initialize the thermocouple connection."""
    if not pi:
        return MockThermocouple()

    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D5)
    cs.direction = digitalio.Direction.OUTPUT
    return adafruit_max31856.MAX31856(spi, cs)


def record_data(temp: float, reading_time: datetime.datetime, maxlen: int = 60*30) -> None:
    """Record temperature data."""
    global temp_recorded, time_recorded

    temp_recorded.append(temp)
    time_recorded.append(reading_time)

    if len(temp_recorded) > maxlen:
        logging.warning("maxlen reached for recording, writing to database.")
        write_data_to_db()
        # TODO change toggle back


def write_data_to_db():
    """Write temp_recorded and time_recorded to database."""
    global roast_event_markers
    # Take the first time as the timestamp for the entry
    # Convert all the timestamps to seconds from the start for easy overlays later
    with data_lock:
        if not temp_recorded:
            logging.warning("No data was found to be written to database.")
            return None
        logging.info(f"Writing {len(temp_recorded)} data points to database...")
        # TODO write to database
        # also write when roast stages were hit
        temp_recorded.clear()
        time_recorded.clear()

        roast_event_markers = initialize_roast_event_markers()


def create_temperature_plot(temp_data: list, time_data: list, fahrenheit: bool = True, y_padding: float = 5):
    """Create timeseries temperature plot."""
    roast_temps = ROAST_TEMPS
    if not fahrenheit:
        roast_temps = [f_to_c(t) for t in ROAST_TEMPS]

    y_range = [0,100]
    if temp_data:
        y_range = [min(temp_data) - y_padding, max(temp_data) + y_padding]

    fig = go.Figure(data=[go.Scatter(x=list(time_data), y=list(temp_data))])
    for temp, stage in zip(roast_temps, ROAST_STAGES):
        fig.add_hline(y=temp, line_width=2, line_dash="dash", line_color="brown")
        fig.add_annotation(
            x=0,
            xref="paper",
            y=temp,
            text=stage,
            showarrow=False,
            yshift=10,
            xanchor="left",
            font={"color":"brown", "size":10}
        )

    fig.update_layout(
        xaxis={"tickformat": "%H:%M"},
        yaxis_title=f"Temperature (°{'F' if fahrenheit else 'C'})",
        yaxis={"range": y_range},
        margin={"l": 20, "r": 20, "b": 20, "t": 20},
    )
    return fig


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
                        className="roast-stage-button-disabled",
                        disabled=True,
                    )
                    for event in ROAST_EVENTS
                ],
                id="roast-stage-container",
            ),
            dcc.Textarea(id="bean-info", placeholder="Enter bean information", style={"width": "50%"}),
        ],
        id="database-information",
        style={
            "display": "flex",
            "flex-direction": "column", # Stack children vertically
            "align-items": "flex-start", # Align children to the start (left) of the cross axis
            "gap": "10px", # Add some space between the children for better readability
        }
    )
])


data_lock = threading.Lock()
recording = False
temp_recorded, time_recorded = [], []
temp_plot, time_plot = initialize_plot_deques()

thermocouple = initialize_thermocouple()
temperature_thread = threading.Thread(target=continually_read_temperature, daemon=True)
temperature_thread.start()
