import dash
from dash import html

dash.register_page(__name__, path='/')

layout = html.Div(
    [
        html.Img(
            src="assets/gemini_cat.png",
            style={"max-width": "50%", "max-height": "50%"}
        )
    ],
    style={
        "background-color": "black",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "height": "100%",
    }
)
