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

from dash import dcc, html, callback, Output, Input

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
        return 20 + random.random() * 10


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
            dcc.Input(id="bean-info", placeholder="Enter bean information"),
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
                temp = temp * 9/5 + 32

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
    Output("record-data-switch", "on"),
    Input("record-data-switch", "on"),
    prevent_initial_call=True
)
def toggle_recording(is_on):
    global recording

    with data_lock:
        recording = is_on
    logging.info(f"Data recording set to: {recording}")

    if not is_on:
        write_data_to_db()

    return is_on


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
    # Take the first time as the timestamp for the entry
    # Convert all the timestamps to seconds from the start for easy overlays later
    with data_lock:
        if not temp_recorded:
            logging.warning("No data was found to be written to database.")
            return None
        logging.info(f"Writing {len(temp_recorded)} data points to database...")
        # TODO write to database
        temp_recorded.clear()
        time_recorded.clear()


def create_temperature_plot(temp_data: list, time_data: list, fahrenheit: bool = True, y_padding: float = 5):
    """Create timeseries temperature plot."""
    y_range = [0,100]
    if temp_data:
        y_range = [min(temp_data) - y_padding, max(temp_data) + y_padding]

    fig = go.Figure(data=[go.Scatter(x=list(time_data), y=list(temp_data))])
    fig.update_layout(
        xaxis={"tickformat": "%H:%M"},
        yaxis_title=f"Temperature (°{'F' if fahrenheit else 'C'})",
        yaxis={"range": y_range},
        margin={"l": 20, "r": 20, "b": 20, "t": 20},
    )
    return fig

data_lock = threading.Lock()
recording = False
temp_recorded, time_recorded = [], []
temp_plot, time_plot = initialize_plot_deques()

thermocouple = initialize_thermocouple()
temperature_thread = threading.Thread(target=continually_read_temperature, daemon=True)
temperature_thread.start()
