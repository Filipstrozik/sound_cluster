import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import librosa
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


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
        # TODO: make this more efficient
        y, sr = librosa.load(file_path)

        if y.size == 0:
            return [0] * 8

        n_fft = min(2048, y.shape[-1])

        pitch = librosa.yin(
            y,
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            frame_length=n_fft,
        )
        mean_pitch = np.mean(pitch) if pitch.size > 0 else 0

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
        self.fig = make_subplots(rows=1, cols=2, column_widths=[0.6, 0.4])

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

        self.fig.update_layout(hovermode="closest")

        # Add empty waveform plot initially
        self.fig.add_trace(
            go.Scatter(
                y=[],
                line=dict(color="black", width=1),
                showlegend=False,
                hoverinfo="none",
            ),
            row=1,
            col=2,
        )

        self.fig.update_layout(
            xaxis_title="PC1",
            yaxis_title="PC2",
            xaxis2_title="Time (s)",
            yaxis2_title="Amplitude",
            showlegend=False,
        )

    def update_waveform(self, file_path):
        self.chosen_audio_file_path = file_path
        y, sr = librosa.load(file_path)

        self.fig.update_traces(
            y=y,
            row=1,
            col=2,
        )
