pi = False

import collections
import datetime
import random
import logging

import dash
import dash_daq as daq
import plotly.graph_objs as go

from dash import dcc, html, callback, Output, Input

if pi:
    import adafruit_max31856
    import board
    import digitalio


class MockThermocouple:
    """Mock thermocouple for local testing."""
    @property
    def temperature(self):
        """Randomly generate a temperature between 20 and 30."""
        return 20 + random.random() * 10


# Create Dash app
app = dash.Dash(__name__)
app.layout = html.Div([
    daq.BooleanSwitch(
        on=False,
        label="Read Temperature Data",
        labelPosition="top"
    ),
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1000, 
        n_intervals=0
    )
])


@callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
)
def update_graph_live(_):
    read_temperature()
    return create_temperature_plot(temp_plot, time_plot)


def initialize_plot_deques(maxlen_plot: int = 60*5) -> tuple[collections.deque, collections.deque]:
    """Initialize deques for storing time and temperature data for plotting."""
    temp_plot = collections.deque(maxlen=maxlen_plot)
    time_plot = collections.deque(maxlen=maxlen_plot)
    return temp_plot, time_plot


def initialize_thermocouple():
    """Initialize the thermocouple connection."""
    if not pi:
        return MockThermocouple()

    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D5)
    cs.direction = digitalio.Direction.OUTPUT
    return adafruit_max31856.MAX31856(spi, cs)


def read_temperature(fahrenheit: bool = True) -> None:
    """Read temperature from thermocouple."""
    try:
        reading_time = datetime.datetime.now()
        temp = thermocouple.temperature
        if fahrenheit:
            temp = temp * 9/5 + 32, reading_time

        temp_plot.append(temp)
        time_plot.append(reading_time)

        if recording:
            record_data(temp, reading_time)


    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None, None


def record_data(temp: float, reading_time: datetime.datetime, maxlen: int = 60*30) -> None:
    """Record temperature data."""
    temp_recorded.append(temp)
    time_recorded.append(reading_time)

    if len(temp_recorded) > maxlen:
        logging.warning("maxlen reached for recording, writing to database.")
        write_data_to_db()
        temp_recorded.clear()
        time_recorded.clear()
        # TODO change toggle back

def write_data_to_db():
    """Write temp_recorded and time_recorded to database."""
    # Take the first time as the timestamp for the entry
    ...


def create_temperature_plot(temp_plot, time_plot, fahrenheit: bool = True, y_padding: float = 5):
    """Create timeseries temperature plot."""
    fig = go.Figure(data=[go.Scatter(x=list(temp_plot), y=list(time_plot))])
    fig.update_layout(
        yaxis_title=f"Temperature (°{'F' if fahrenheit else 'C'})",
        # yaxis=dict(
        #     range=[min(time_plot) - y_padding, max(time_plot) + y_padding] if time_plot else [0, 100]
        # ),
    )
    return fig


if __name__ == '__main__':
    recording = False
    temp_recorded, time_recorded = [], []
    temp_plot, time_plot = initialize_plot_deques()
    thermocouple = initialize_thermocouple()
    app.run(debug=True, host="0.0.0.0")
