import collections
import datetime

import adafruit_max31856
import board
import dash
import digitalio
import plotly.graph_objs as go

from dash import dcc, html, callback, Output, Input


app = dash.Dash(__name__)
app.layout = html.Div([
    html.H3('Live Temperature'),
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1000, 
        n_intervals=0
    )
])

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

    fig = go.Figure(data=[go.Scatter(x=list(X), y=list(Y))])
    return fig


def read_temperature(fahrenheit: bool = True) -> float | None:
    """Read temperature from thermocouple."""
    try:
        temp_c = thermocouple.temperature
        if fahrenheit:
            return temp * 9/5 + 32
        return temp_c
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
