import json
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pygame
import os
import sys
from audio_analyzer import AudioAnalyzer
import platform
import subprocess

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
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="main-plot",
                                        figure=audio_analyzer.fig,
                                        config={
                                            "editable": True,
                                            "displayModeBar": False,
                                        },
                                    ),
                                ]
                            )
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.Div(id="audio-info"),
                                    html.Button(
                                        "Show audio", id="show-audio-button", n_clicks=0
                                    ),
                                ]
                            )
                        ),
                    ]
                ),
                html.Div(
                    f"Loaded directory: {directory} with {len(audio_analyzer.audio_files)} audio files"
                ),
            ]
        )
    except Exception as e:
        return f"Error loading directory: {str(e)}"


# Initialize audio analyzer with the provided directory
if initial_directory:
    audio_analyzer = AudioAnalyzer(initial_directory)
else:
    audio_analyzer = None

audio_path = None

# Modify the app layout to show initial data if directory was provided
app.layout = html.Div(
    [
        html.H1("Sound Cluster"),
        html.Div(id="directory-status", style={"marginTop": "10px"}),
        html.Div(
            id="main-content",
            children=(
                load_directory(True, initial_directory)
                if initial_directory
                else "Please choose a directory."
            ),
        ),
        dcc.Store(id="audio-data-store"),
        html.Div(
            id="directory-path-hidden",
            style={"display": "none"},
            children=initial_directory or "",
        ),
    ]
)


@app.callback(
    Output("main-plot", "figure"),
    Output("audio-info", "children"),
    Output("main-plot", "clickData"),
    [Input("main-plot", "clickData")],
    [State("directory-path-hidden", "children")],
    prevent_initial_call=True,
)
def update_audio(clickData, directory):
    if clickData:
        ind = clickData["points"][0]["pointIndex"]
        audio_file = audio_analyzer.audio_files[ind]
        file_path = os.path.join(directory, audio_file)

        try:
            # Initialize pygame mixer if not already initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            # Stop any currently playing audio
            pygame.mixer.music.stop()

            # Unload previous audio and load the new one
            pygame.mixer.music.unload()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            audio_analyzer.update_waveform(file_path)
            return audio_analyzer.fig, f"Now playing: {audio_file}", None
        except Exception as e:
            return audio_analyzer.fig, f"Error playing audio: {str(e)}", None

    return audio_analyzer.fig, None, None


@app.callback(
    Output("show-audio-button", "n_clicks"),
    Input("show-audio-button", "n_clicks"),
    [State("directory-path-hidden", "children")],
    prevent_initial_call=True,
)
def show_audio_file(n_clicks, directory):
    if n_clicks is None:
        return 0
    if not audio_analyzer:
        return 0
    if not audio_analyzer.chosen_audio_file_path:
        return 0

    audio_file = audio_analyzer.chosen_audio_file_path
    file_path = os.path.join(directory, audio_file)

    # Different commands for different operating systems
    if platform.system() == "Windows":
        subprocess.run(["explorer", "/select,", os.path.normpath(file_path)])
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", "-R", file_path])
    else:  # Linux
        try:
            subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except FileNotFoundError:
            subprocess.run(["nautilus", os.path.dirname(file_path)])

    return 0


if __name__ == "__main__":
    if sys.platform.startswith("darwin"):  # macOS
        app.run_server(debug=True, use_reloader=False)
    else:
        app.run_server(debug=True)
