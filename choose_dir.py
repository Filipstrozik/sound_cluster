import os
import dash_bootstrap_components as dbc
import tkinter as tk
from tkinter import filedialog
import subprocess
import sys


def select_directory():
    # Create and hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open directory selection dialog
    directory = filedialog.askdirectory(
        title="Select Directory with Audio Files", mustexist=True
    )

    if directory:
        print(f"Selected directory: {directory}")
        sound_cluster_path = os.path.join(os.path.dirname(__file__), "sound_cluster.py")
        subprocess.Popen([sys.executable, sound_cluster_path, directory])
    else:
        print("No directory selected")

    root.destroy()


if __name__ == "__main__":
    select_directory()
