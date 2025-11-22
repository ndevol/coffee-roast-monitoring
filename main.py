import collections
import datetime

import adafruit_max31856
import board
import dash
import digitalio
import plotly.graph_objs as go

from dash import dcc, html, callback, Output, Input


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

# Initialize the thermocouple connection
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
cs.direction = digitalio.Direction.OUTPUT
thermocouple = adafruit_max31856.MAX31856(spi, cs)

# Store last 100 readings for the live graph
X = collections.deque(maxlen=100)
Y = collections.deque(maxlen=100)


@callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
)
def update_graph_live(n):
    temp = read_temperature()
    if temp is None:
        return dash.no_update

    X.append(datetime.datetime.now())
    Y.append(temp)

    return create_temperature_plot(X, Y)


def read_temperature(fahrenheit: bool = True) -> float | None:
    """Read temperature from thermocouple."""
    try:
        temp_c = thermocouple.temperature
        if fahrenheit:
            return temp_c * 9/5 + 32
        return temp_c
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None


def create_temperature_plot(X, Y, fahrenheit: bool = True, y_padding: float = 5):
    fig = go.Figure(data=[go.Scatter(x=list(X), y=list(Y))])
    fig.update_layout(
        yaxis_title=f"Temperature (°{'F' if fahrenheit else 'C'})",
        yaxis=dict(range=[min(Y) - y_padding, max(Y) + y_padding] if Y else [0, 100]), 
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
