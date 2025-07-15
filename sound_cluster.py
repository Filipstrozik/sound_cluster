import json
import webbrowser
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pygame
import os
import sys
from audio_analyzer import AudioAnalyzer
import platform
import subprocess

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "Sound Cluster by @filipstrozik"

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
                    dbc.Col(
                        html.Div(
                            f"Loaded directory: {directory} with {len(audio_analyzer.audio_files)} audio files",
                            style={"margin": "10px"},
                        )
                    )
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="scatter-plot",
                                        figure=audio_analyzer.scatter_fig,
                                        config={
                                            "editable": False,
                                            "displayModeBar": False,
                                            "displaylogo": False,
                                            "displayMode": "static",
                                        },
                                        style={"height": "70vh"},
                                    ),
                                ]
                            ),
                            width=7,  # 7/12 ≈ 60%
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Row(
                                        dcc.Graph(
                                            id="waveform-plot",
                                            figure=audio_analyzer.waveform_fig,
                                            config={
                                                "editable": True,
                                                "displayModeBar": False,
                                                "displaylogo": False,
                                                "displayMode": "static",
                                                "staticPlot": True,
                                            },
                                            style={"height": "35vh"},
                                        )
                                    ),
                                    dbc.Row(
                                        dcc.Graph(
                                            id="spectrogram-plot",
                                            figure=audio_analyzer.spectrogram_fig,
                                            config={
                                                "editable": True,
                                                "displayModeBar": False,
                                                "displaylogo": False,
                                                "displayMode": "static",
                                                "staticPlot": True,
                                            },
                                            style={"height": "35vh"},
                                        )
                                    ),
                                ]
                            ),
                            width=5,  # 5/12 ≈ 40%
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.Div(id="audio-info", style={"margin": "10px"}),
                                    dbc.Button(
                                        "Show audio",
                                        id="show-audio-button",
                                        n_clicks=0,
                                        style={"margin": "10px"},
                                    ),
                                ]
                            )
                        ),
                    ]
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
        html.H1("Sound Cluster", style={"margin": "10px"}),
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
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Exit Application", id="exit-button", style={"margin": "10px"}
                    )
                )
            ]
        ),
    ]
)


@app.callback(
    Output("waveform-plot", "figure"),
    Output("spectrogram-plot", "figure"),
    Output("audio-info", "children"),
    Output("scatter-plot", "clickData"),
    [Input("scatter-plot", "clickData")],
    prevent_initial_call=True,
)
def update_audio(clickData):
    if clickData and audio_analyzer:
        ind = clickData["points"][0]["pointIndex"]
        audio_file = audio_analyzer.audio_files[ind]
        file_path = os.path.join(audio_analyzer.directory, audio_file)

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
            audio_analyzer.update_spectrogram(file_path)

            return (
                audio_analyzer.waveform_fig,
                audio_analyzer.spectrogram_fig,
                f"Now playing: {audio_file}",
                None,
            )
        except Exception as e:
            return (
                audio_analyzer.waveform_fig,
                audio_analyzer.spectrogram_fig,
                f"Error playing audio: {str(e)}",
                None,
            )

    if audio_analyzer:
        return audio_analyzer.waveform_fig, audio_analyzer.spectrogram_fig, None, None
    else:
        return None, None, None, None


@app.callback(
    Output("show-audio-button", "n_clicks"),
    Input("show-audio-button", "n_clicks"),
    prevent_initial_call=True,
)
def show_audio_file(n_clicks):
    if n_clicks is None:
        return 0
    if not audio_analyzer:
        return 0
    if not audio_analyzer.chosen_audio_file_path:
        return 0

    audio_file = audio_analyzer.chosen_audio_file_path
    file_path = os.path.join(audio_analyzer.directory, audio_file)

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


# Exit app when window is closed
@app.callback(
    Output("exit-button", "n_clicks"),
    Input("exit-button", "n_clicks"),
    prevent_initial_call=True,
)
def exit_application(n_clicks):
    if n_clicks is not None:
        # Stop any playing audio before exiting
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        # Kill any processes using port 8050
        if platform.system() == "Windows":
            subprocess.run(["netstat", "-ano", "|", "findstr", ":8050"], shell=True)
            subprocess.run(["taskkill", "/F", "/PID", str(os.getpid())], shell=True)
        else:
            subprocess.run(["lsof", "-i", ":8050"])
            subprocess.run(["kill", "-9", str(os.getpid())])

        # exit the application
        os._exit(0)

    return 0


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8050")
    if sys.platform.startswith("darwin"):  # macOS
        app.run_server(debug=False, use_reloader=False)
    else:
        app.run_server(debug=False)
