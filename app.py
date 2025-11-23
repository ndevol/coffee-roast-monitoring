import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True)

# Define styles for the header and main content
HEADER_HEIGHT = "4rem" # Fixed height for the header
HEADER_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 0,
    "height": HEADER_HEIGHT,
    "background-color": "#343a40", # Dark background for the header
    "color": "white",
    "display": "flex",
    "align-items": "center",
    "justify-content": "space-between", # Distribute items with space between
    "padding": "0 1rem",
    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)", # Subtle shadow
    "z-index": 1000, # Ensure header is on top
}

# Style for the navigation icons within the header
NAV_ICON_STYLE = {
    "width": "24px", # Adjust icon size as needed
    "height": "24px", # Adjust icon size as needed
    "margin-left": "1rem", # Space between icons
    "text-decoration": "none", # Remove underline from links
    "transition": "opacity 0.2s ease", # Smooth opacity transition on hover
    "cursor": "pointer" # Indicate it's clickable
}

# Hover style for icons (can be applied via external CSS or dcc.Store for JS styling)
# For simplicity, we'll suggest a basic color change here.
# For more advanced hover, external CSS is recommended.
NAV_ICON_HOVER_STYLE = {
    "color": "#007bff", # Example hover color
}

# The main content needs a top margin to avoid being hidden by the fixed header
MAIN_CONTENT_STYLE = {
    "margin-top": HEADER_HEIGHT, # Push content down by header height
    "padding": "2rem 1rem",
}

# Helper to find the relative path for a page
def get_page_relative_path(page_module_name: str) -> str:
    """Get paths for specific pages."""
    for page in dash.page_registry.values():
        if page["module"].endswith(f".{page_module_name}"):
            return page["relative_path"]
    return "/"


app.layout = html.Div([
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
        style=HEADER_STYLE,
    ),
    # Main page content
    html.Div(
        dash.page_container,
        style=MAIN_CONTENT_STYLE,
    )
])

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
