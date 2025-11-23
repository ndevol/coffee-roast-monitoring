import dash
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True)

# Define common styles for the sidebar and main content
# Using a fixed position sidebar for persistent navigation
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",  # Width of the sidebar
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",  # Light grey background
    "border-right": "1px solid #dee2e6",  # Subtle right border
    "overflow-y": "auto",  # Enable scrolling if content overflows
}

# The main content will need a left margin to avoid being hidden by the fixed sidebar
CONTENT_STYLE = {
    "margin-left": "18rem",  # Must be greater than sidebar width + padding
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

app.layout = html.Div([
    # Sidebar
    html.Div(
        [
            html.H2("Coffee Roast Monitoring", style={"color": "#343a40", "margin-bottom": "1.5rem"}),
            html.Hr(),  # Horizontal separator
            html.Nav(
                [
                    html.Div(
                        dcc.Link(
                            f"{page['name']}",  # Display only the page name
                            href=page["relative_path"],
                            style={
                                "display": "block",
                                "padding": "0.75rem 1rem",
                                "text-decoration": "none",
                                "color": "#007bff",  # Bootstrap primary blue
                                "border-radius": "0.25rem",
                                "margin-bottom": "0.5rem",
                                # You can add more advanced hover/active styles using external CSS
                                # For example: ":hover": {"background-color": "#e2e6ea"}
                            }
                        )
                    ) for page in dash.page_registry.values()
                ],
            )
        ],
        style=SIDEBAR_STYLE,
    ),
    # Main page content
    html.Div(
        dash.page_container,
        style=CONTENT_STYLE,
    )
])

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
