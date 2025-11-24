import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True)


# Style for the navigation icons within the header
NAV_ICON_STYLE = {
    "width": "24px",
    "height": "24px",
    "margin-left": "1rem",
    "text-decoration": "none",
    "transition": "opacity 0.2s ease",
    "cursor": "pointer",
}

# Hover style for icons (can be applied via external CSS or dcc.Store for JS styling)
# For simplicity, we'll suggest a basic color change here.
# For more advanced hover, external CSS is recommended.
NAV_ICON_HOVER_STYLE = {
    "color": "#007bff",
}


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
                html.H2("Coffee Roast Monitoring", style={"margin": 0, "font-size": "1.5rem"}),
                html.Div(
                    [
                        dcc.Link(
                            html.Img(src="assets/thermometer.svg", style=NAV_ICON_STYLE),
                            href=get_page_relative_path("collect_data"),
                            className="header-icon",
                        ),
                        dcc.Link(
                            html.Img(src="assets/document_search.svg", style=NAV_ICON_STYLE),
                            href=get_page_relative_path("view_data"),
                            className="header-icon",
                        ),
                    ],
                    style={"display": "flex", "align-items": "center"}
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
