pi = False

import collections
import datetime
import random

import dash
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
    html.H3('Coffee Time!'),
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
    temp, t = read_temperature()
    if temp is None:
        return dash.no_update

    X.append(t)
    Y.append(temp)

    return create_temperature_plot(X, Y)


def initialize_deques(maxlen: int = 60*5) -> tuple[collections.deque, collections.deque]:
    """Initialize deques for storing time and temperature data"""
    X = collections.deque(maxlen=maxlen)
    Y = collections.deque(maxlen=maxlen)
    return X, Y


def initialize_thermocouple():
    """Initialize the thermocouple connection."""
    if not pi:
        return MockThermocouple()

    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D5)
    cs.direction = digitalio.Direction.OUTPUT
    return adafruit_max31856.MAX31856(spi, cs)


def read_temperature(fahrenheit: bool = True) -> tuple[float | None, datetime.datetime | None]:
    """Read temperature from thermocouple."""
    try:
        reading_time = datetime.datetime.now()
        temp_c = thermocouple.temperature
        if fahrenheit:
            return temp_c * 9/5 + 32, reading_time
        return temp_c, reading_time
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None, None


def create_temperature_plot(X, Y, fahrenheit: bool = True, y_padding: float = 5):
    """Create timeseries temperature plot."""
    fig = go.Figure(data=[go.Scatter(x=list(X), y=list(Y))])
    fig.update_layout(
        yaxis_title=f"Temperature (°{'F' if fahrenheit else 'C'})",
        yaxis=dict(range=[min(Y) - y_padding, max(Y) + y_padding] if Y else [0, 100]),
    )
    return fig


if __name__ == '__main__':
    X, Y = initialize_deques()
    thermocouple = initialize_thermocouple()
    app.run(debug=True, host="0.0.0.0")
