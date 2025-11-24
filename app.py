import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True)


def get_page_relative_path(page_module_name: str) -> str:
    """Get relative paths for specific pages."""
    for page in dash.page_registry.values():
        if page["module"].endswith(f".{page_module_name}"):
            return page["relative_path"]
    return "/"


app.layout = html.Div(
    [
        # Header
        html.Div(
            [
                html.H2("Coffee Roast Monitoring"),
                html.Div(
                    [
                        dcc.Link(
                            html.Img(src="assets/thermometer.svg", className="header-icon"),
                            href=get_page_relative_path("collect_data"),
                        ),
                        dcc.Link(
                            html.Img(src="assets/document_search.svg", className="header-icon"),
                            href=get_page_relative_path("view_data"),
                        ),
                    ],
                    className="link-container",
                )
            ],
            className="header",
        ),
        # Main page content
        html.Div(
            dash.page_container,
            className="content-container",
        )
    ],
    className="app-container",
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
