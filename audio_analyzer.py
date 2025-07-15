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
        print(f"Initializing AudioAnalyzer with directory: {directory}")
        self.directory = directory
        self.audio_files = self.list_audio_files()
        self.sounds_df = pd.DataFrame(columns=range(8))
        self.chosen_audio_file_path = ""
        self.process_audio_files()

        # Create separate figures instead of subplots
        self.scatter_fig = go.Figure()
        self.waveform_fig = go.Figure()
        self.spectrogram_fig = go.Figure()

        # Initialize both figures
        self._initialize_scatter_plot()
        self._initialize_waveform_plot()
        self._initialize_spectrogram_plot()

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

    def _initialize_scatter_plot(self):
        self.scatter_fig.add_trace(
            go.Scatter(
                x=self.sounds_df_pca["PC1"],
                y=self.sounds_df_pca["PC2"],
                mode="markers",
                text=self.audio_files,
                hoverinfo="text",
                marker=dict(
                    size=16,
                    color=self.sounds_df_pca["PC1"],
                    colorscale="Viridis",
                    showscale=False,
                ),
            )
        )
        self.scatter_fig.update_layout(
            title="Audio Files Clustering",
            xaxis_title="X",
            yaxis_title="Y",
            showlegend=False,
        )

    def _initialize_waveform_plot(self):
        self.waveform_fig.update_layout(
            title="Waveform",
            xaxis_title="Time",
            yaxis_title="Amplitude",
            showlegend=False,
        )

    def _initialize_spectrogram_plot(self):
        self.spectrogram_fig.update_layout(
            title="Spectrogram",
            xaxis_title="Frequency",
            yaxis_title="Magnitude",
        )

    def update_waveform(self, file_path):
        self.chosen_audio_file_path = os.path.basename(file_path)
        y, sr = librosa.load(file_path)
        times = np.arange(len(y)) / sr

        self.waveform_fig.data = []  # Clear existing traces
        self.waveform_fig.add_trace(
            go.Scatter(
                x=times,
                y=y,
                mode="lines",
                name="waveform",
                line=dict(color="black", width=2),
            )
        )
        self.waveform_fig.update_layout(
            title=f"Waveform - {os.path.basename(file_path)}",
            xaxis_title="Time (s)",
            yaxis_title="Amplitude",
        )

    def update_spectrogram(self, file_path):
        y, sr = librosa.load(file_path)
        print(f"sr: {sr}")
        # compute a Fast Fourier Transform
        fft_values = np.fft.fft(y)
        fft_magnitudes = np.abs(fft_values)
        freqs = np.fft.fftfreq(len(y), d=1 / sr)

        mask = (freqs >= 0) & (freqs <= 20000)
        freqs = freqs[mask]
        fft_magnitudes = fft_magnitudes[mask]

        self.spectrogram_fig.data = []  # Clear existing traces
        self.spectrogram_fig.add_trace(
            go.Scatter(
                x=freqs,
                y=fft_magnitudes,
                mode="lines",
                name="FFT",
                line=dict(width=2, color="black"),
            )
        )
        self.spectrogram_fig.update_layout(
            title=f"Spectrogram - {os.path.basename(file_path)}",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Magnitude",
            xaxis_type="log",
            xaxis=dict(
                range=[np.log10(20), np.log10(20000)],
                tickvals=[20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000],
                ticktext=[
                    "20",
                    "50",
                    "100",
                    "200",
                    "500",
                    "1k",
                    "2k",
                    "5k",
                    "10k",
                    "20k",
                ],
            ),
        )
