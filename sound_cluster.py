import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pygame
import os
import sys
from audio_analyzer import AudioAnalyzer

# Initialize Dash app with suppressed callback exceptions
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Get directory path from command line arguments
initial_directory = sys.argv[1] if len(sys.argv) > 1 else None

def load_directory(contents, filename):
    if not contents:
        return "Please choose a directory."

    directory = filename
    if not os.path.isdir(directory):
        return "Invalid directory path. Please choose a valid directory."

    global audio_analyzer
    try:
        audio_analyzer = AudioAnalyzer(directory)
        return html.Div([
            dbc.Row([
                dbc.Col(
                    html.Div([
                        dcc.Graph(
                            id="main-plot",
                            figure=audio_analyzer.fig,
                            config={"editable": False},
                        ),
                    ])
                ),
                dbc.Col(
                    html.Div([
                        html.Button("Play Audio", id="play-button", n_clicks=0),
                        html.Div(id="audio-info"),
                    ])
                ),
            ]),
            html.Div(f"Loaded directory: {directory} with {len(audio_analyzer.audio_files)} audio files")
        ])
    except Exception as e:
        return f"Error loading directory: {str(e)}"

# Initialize audio analyzer with the provided directory
if initial_directory:
    audio_analyzer = AudioAnalyzer(initial_directory)
else:
    audio_analyzer = None

# Modify the app layout to show initial data if directory was provided
app.layout = html.Div([
    html.H1("Sound Cluster"),
    html.Div(id="directory-status", style={"marginTop": "10px"}),
    html.Div(
        id="main-content",
        children=load_directory(True, initial_directory) if initial_directory else "Please choose a directory."
    ),
    dcc.Store(id="audio-data-store"),
    html.Div(id="directory-path-hidden", style={"display": "none"}, children=initial_directory or ""),
])


@app.callback(
    Output("audio-info", "children"),
    [Input("main-plot", "clickData"), 
     Input("play-button", "n_clicks")],
    [State("directory-path-hidden", "children")],
    prevent_initial_call=True,
)
def update_audio(clickData, play_clicks, directory):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if clickData and (trigger_id == "main-plot" or trigger_id == "play-button"):
        ind = clickData["points"][0]["pointIndex"]
        audio_file = audio_analyzer.audio_files[ind]
        file_path = os.path.join(directory, audio_file)

        try:
            # Initialize pygame mixer if not already initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            # Always reload and play the file
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            audio_analyzer.chosen_audio_file_path = file_path
            return f"Now playing: {audio_file}"
        except Exception as e:
            return f"Error playing audio: {str(e)}"

    return "Click on a point to play audio."

if __name__ == '__main__':
    if sys.platform.startswith('darwin'):  # macOS
        app.run_server(debug=True, use_reloader=False)
    else:
        app.run_server(debug=True)
