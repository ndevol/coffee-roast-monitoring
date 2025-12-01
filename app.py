import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True)


def get_page_relative_path(page_module_name: str) -> str:
    """Get relative paths for specific pages."""
    for page in dash.page_registry.values():
        if page["module"].endswith(f".{page_module_name}"):
            return page["relative_path"]
    return "/"

header = html.Div(
    [
        html.H2("Coffee Roast Monitoring", className="header-title"),
        html.Div(
            [
                dcc.Link(
                    html.Img(src="assets/thermometer.svg", className="icon-button"),
                    href=get_page_relative_path("collect_data"),
                ),
                dcc.Link(
                    html.Img(src="assets/document_search.svg", className="icon-button"),
                    href=get_page_relative_path("view_data"),
                ),
            ],
            className="link-container",
        )
    ],
    className="header",
)

body = html.Div(
    dash.page_container,
    className="content-container",
)

app.layout = html.Div([header, body], className="app-container")

if __name__ == "__main__":
    # app.run(debug=True, use_reloader=False, host="0.0.0.0")
    app.run(debug=True, host="0.0.0.0")
