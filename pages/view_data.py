import dash
from dash import html

dash.register_page(__name__)

default_plot_message = html.H1("Select data to see plot")

layout = html.Div(
    [
        html.Div(
            [
                html.H3("Historical Data"),
            ],
            className="database-entries-container"
        ),
        html.Div(
            [
                default_plot_message
            ],
            className="previous-plot-container"
        )
    ],
    className="previous-data-container",
)
