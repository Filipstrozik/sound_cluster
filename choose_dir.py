import os
import base64
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import tkinter as tk
from tkinter import filedialog
import subprocess
import sys

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        html.H1("Directory Selector", className="mt-4 mb-4"),
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("Select a Directory"),
                        html.P(
                            "Select any file from the directory you want to choose. "
                            "The app will use the directory containing that file."
                        ),
                        dbc.Button(
                            "Choose File from Directory",
                            id="choose-dir-button",
                            color="primary",
                            className="mb-3",
                        ),
                        dcc.Upload(
                            id="upload-data",
                            children=[],
                            style={"display": "none"},
                            multiple=False,
                        ),
                        html.Div(id="selected-dir-output", className="mt-3"),
                    ]
                )
            ],
            className="mb-4",
        ),
    ]
)


@app.callback(
    Output("selected-dir-output", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_selected_directory(contents, filename):
    if contents is not None and filename is not None:
        try:
            # Get just the filename (we can't get the full path from the browser)
            return [
                html.Strong("Selected file: "),
                html.Span(filename),
                html.Br(),
                html.Span("The parent directory of this file will be used."),
            ]
        except:
            return html.Div("Error processing file selection.")
    return []


app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            document.getElementById('upload-data').click();
            return n_clicks;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("choose-dir-button", "n_clicks"),
    Input("choose-dir-button", "n_clicks"),
    prevent_initial_call=True,
)

def select_directory():
    # Create and hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open directory selection dialog
    directory = filedialog.askdirectory(
        title='Select Directory with Audio Files',
        mustexist=True
    )
    
    if directory:
        # Launch the Dash app with the selected directory
        sound_cluster_path = os.path.join(os.path.dirname(__file__), 'sound_cluster.py')
        subprocess.Popen([sys.executable, sound_cluster_path, directory])
        
    root.destroy()

if __name__ == "__main__":
    select_directory()
