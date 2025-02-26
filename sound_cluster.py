import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import librosa
import pandas as pd
import pygame
import subprocess
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import sys

# Initialize Dash app with suppressed callback exceptions
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Get directory path from command line arguments
initial_directory = sys.argv[1] if len(sys.argv) > 1 else None

class AudioAnalyzer:
    def __init__(self, directory):
        self.directory = directory
        self.audio_files = self.list_audio_files()
        self.sounds_df = pd.DataFrame(columns=range(8))
        self.chosen_audio_file_path = ""
        self.process_audio_files()
        self.create_plot()

    def list_audio_files(self):
        return [
            sounds_figure
            for sounds_figure in os.listdir(self.directory)
            if sounds_figure.endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a"))
        ]

    def analyze_audio(self, file_path):
        y, sr = librosa.load(file_path)

        if y.size == 0:
            return [
                0
            ] * 8  # Adjusted to return 8 zeros to match the feature vector length

        n_fft = min(2048, y.shape[-1])

        pitch = librosa.yin(
            y,
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            frame_length=n_fft,
        )
        mean_pitch = (
            np.mean(pitch) if pitch.size > 0 else 0
        )  # Check if pitch is not empty

        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=n_fft)
        mean_mfccs = np.mean(mfccs, axis=1)

        zcr = librosa.feature.zero_crossing_rate(y, frame_length=n_fft)
        mean_zcr = np.mean(zcr)

        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft)
        mean_chroma = np.mean(chroma, axis=1)

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft)
        mean_spectral_centroid = np.mean(spectral_centroid)

        harmonic = librosa.effects.harmonic(y, n_fft=n_fft)
        mean_harmonic = np.mean(harmonic)

        percussive = librosa.effects.percussive(y, n_fft=n_fft)
        mean_percussive = np.mean(percussive)

        spectral_flatness = librosa.feature.spectral_flatness(y=y, n_fft=n_fft)
        mean_spectral_flatness = np.mean(spectral_flatness)

        duration = librosa.get_duration(y=y, sr=sr, n_fft=n_fft)
        rms = np.sqrt(np.mean(y**2))

        feature_vector = [
            duration,
            rms,
            mean_pitch,
            mean_spectral_centroid,
            mean_zcr,
            mean_spectral_flatness,
            mean_harmonic,
            mean_percussive,
        ]

        return feature_vector

    def process_audio_files(self):
        for audio_file in self.audio_files:
            file_path = os.path.join(self.directory, audio_file)
            audio_features = self.analyze_audio(file_path)
            self.sounds_df.loc[audio_file] = audio_features

        scaler = StandardScaler()
        sounds_df_normalized = scaler.fit_transform(self.sounds_df)

        pca = PCA(n_components=2)
        sounds_df_pca = pca.fit_transform(sounds_df_normalized)

        self.sounds_df_pca = pd.DataFrame(
            sounds_df_pca, index=self.sounds_df.index, columns=["PC1", "PC2"]
        )

    def create_plot(self):
        self.fig = make_subplots(rows=1, cols=2, column_widths=[0.7, 0.3])

        scatter = go.Scatter(
            x=self.sounds_df_pca["PC1"],
            y=self.sounds_df_pca["PC2"],
            mode="markers",
            text=self.audio_files,
            textposition="top center",
            marker=dict(size=10, color="blue", opacity=0.8),
            hoverinfo="text",
        )

        self.fig.add_trace(scatter, row=1, col=1)
        self.fig.update_layout(
            title="Sound Cluster (alpha 0.1 @zean)",
            xaxis_title="PC1",
            yaxis_title="PC2",
            showlegend=False,
        )

        self.fig.layout.hovermode = "closest"
        self.fig.add_trace(go.Scatter(y=[]), row=1, col=2)


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
