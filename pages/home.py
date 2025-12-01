import dash
from dash import html

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('Welcome to the Coffee Roast Monitor'),
    html.P('Use the icons in the header to navigate:'),
    html.Ul([
        html.Li('Thermometer: Start a new roast and collect data.'),
        html.Li('Document Search: View and compare previous roasts.'),
    ])
])
