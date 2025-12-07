import dash
from dash import Dash, html, dcc, Input, Output
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
                dcc.Link(
                    html.Button(
                        html.Img(
                            src="assets/power_off.svg",
                            alt="Shutdown",
                            className="icon-button"
                        ),
                        id="shutdown-button",
                        className="button",
                        title="Shutdown Raspberry Pi",
                    ),
                    href="/",
                ),
            ],
            className="link-container",
        ),
    ],
    className="header",
)

body = html.Div(
    dash.page_container,
    className="content-container",
)

app.layout = html.Div([
    header,
    body,
    html.Div(id="dummy-div", style={"display": "none"}),
], className="app-container")


@app.callback(
    Output("dummy-div", "children"),
    Input("shutdown-button", "n_clicks"),
    prevent_initial_call=True
)
def initiate_shutdown(n_clicks):
    if not n_clicks:
        return dash.no_update

    logging.info("Shutdown button clicked. Initiating system shutdown.")
    try:
        # -h for halt (power off), now for immediate
        # check=True will raise CalledProcessError if command fails
        subprocess.run(["sudo", "shutdown"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to execute shutdown command: %s", e)
        return f"Error: Shutdown command failed. {e}"
    except FileNotFoundError:
        logging.error("Shutdown command (sudo/shutdown) not found. Check system PATH.")
        return "Error: Shutdown command not found."


if __name__ == "__main__":
    # app.run(host="0.0.0.0")
    app.run(debug=True, host="0.0.0.0")
