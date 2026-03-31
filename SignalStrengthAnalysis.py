"""
Signal Strength Analysis - Multi-Measurement Comparison
========================================================
For each folder, finds the peak signal strength (dB) at each measured position
and plots it against actual distance. Add folders to FOLDERS to compare.
"""

import math
import pickle

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colormaps
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d


# ---------------------------------------------------------------------------
# CONFIGURATION — edit these
# ---------------------------------------------------------------------------

#Offsets
FOLDERS = [
    "Data/Pipe_Can_717_n2/",
    "Data/Pipe_Can_717_n1/",
    "Data/Pipe_Can_717_0/",
    "Data/Pipe_Can_717_1/",
    "Data/Pipe_Can_717_2/",
    "Data/Pipe_Can_717_3/"
]

#Open Air
#FOLDERS = [
#    "Data/Air_Target_241_0/",
#    "Data/Air_Target_717_0/",
#    "Data/Air_Target2_717_0/",
#]

#Varying Pipes
#FOLDERS = [
#    "Data/Pipe_Can_241_0/",
#    "Data/Pipe_Can2_241_0/",
#    "Data/Pipe_Alt_241_0/",
#    "Data/Pipe_Can_717_0/",
#    "Data/Pipe_Can2_717_0/",
#    "Data/Pipe_Alt_717_0/",
#    "Data/PipeLarge_Target_717_0/",
#    "Data/PipeMedium_Target_717_0/"
#]

#FOLDERS = [
#    "Data/Pipe_Can_717_0/",
#    "Data/Pipe_Alt_717_0/",
#    "Data/PipeLarge_Target_717_0/",
#    "Data/PipeMedium_Target_717_0/",
#    "Data/Air_Target_717_0/",
#    "Data/Air_Target2_717_0/"
#]

FONT_SIZE = 12  # base font size for axis labels, ticks, and legend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_folder_metadata(folder):
    """Derive resolution, threshold, and a human-readable title from folder path."""
    seg = folder.replace("\\", "/").rstrip("/").split("/")[-1].split("_")

    medium = seg[0]
    target = seg[1] if len(seg) > 1 else "?"
    sensor = seg[2] if len(seg) > 2 else "unknown"

    if sensor == "717":
        resolution = 0.0352
        threshold = 100_000 if medium == "Air" else 0.8e6
    else:
        resolution = 0.046875
        threshold = 300_000 if medium == "Air" else 2.0e6

    title = f"{medium} | {target}"
    return dict(resolution=resolution, threshold=threshold, title=title)


def load_folder(folder, resolution):
    """Load all .pkl files from a folder and return (x, data_lin, data_log)."""
    folder = folder.rstrip("/\\") + "/"

    def process_file(path):
        with open(path, "rb") as f:
            raw = pickle.load(f)
        col8 = [val[8] for val in raw]
        return [sum(col) / len(col) for col in zip(*col8)]

    first = process_file(folder + "None.pkl")
    n = len(first)
    x = np.linspace(0, n * resolution, n)

    def to_lin(data):
        return [(32.0 / n) * (2 ** (v / 512.0)) for v in data]

    def to_log(data):
        return [(v * 20.0 * math.log10(2.0)) / 512.0 + 20.0 * math.log10(32.0 / n)
                for v in data]

    data_lin = [to_lin(first)]
    data_log = [to_log(first)]

    for i in range(5, 205, 5):
        data = process_file(folder + f"{i}.pkl")
        data_lin.append(to_lin(data))
        data_log.append(to_log(data))

    return x, data_lin, data_log


def get_peak_strengths(data_lin, data_log, threshold):
    """
    For each measurement, find the peak using the linear data (same method as
    peak_analysis.py) then read the dB value at that index from the log data.
    Returns a list of dB values (or None where no peak was found).
    """
    strengths = []
    for lin, log in zip(data_lin, data_log):
        smoothed = gaussian_filter1d(lin, sigma=1)
        peaks, _ = find_peaks(smoothed, height=threshold)
        if peaks.size:
            strengths.append(log[peaks[0]])
        else:
            strengths.append(None)
    return strengths


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 7))
cmap = colormaps.get_cmap("tab10")

actual_pos = np.array(range(0, 205, 5))

for idx, folder in enumerate(FOLDERS):
    colour = cmap(idx % 10)
    print(f"Processing: {folder}")

    meta = parse_folder_metadata(folder)
    resolution = meta["resolution"]

    try:
        x, data_lin, data_log = load_folder(folder, resolution)
    except FileNotFoundError as e:
        print(f"  Skipping — {e}")
        continue

    strengths = get_peak_strengths(data_lin, data_log, meta["threshold"])

    not_found = sum(1 for s in strengths if s is None)
    if not_found:
        print(f"  Peaks not found for {not_found} position(s) — those points skipped.")

    # Separate out valid points for plotting
    valid_pos      = [p for p, s in zip(actual_pos, strengths) if s is not None]
    valid_strength = [s for s in strengths if s is not None]

    ax.plot(valid_pos, valid_strength, "o-", color=colour,
            linewidth=1.5, markersize=4, label=meta["title"])

ax.set_xlabel("Actual Position (cm)", fontsize=FONT_SIZE)
ax.set_ylabel("Peak Signal Strength (dB)", fontsize=FONT_SIZE)
ax.set_title("Peak Signal Strength vs Distance", fontsize=FONT_SIZE + 2)
ax.tick_params(labelsize=FONT_SIZE)
ax.legend(fontsize=FONT_SIZE, loc="lower right")
ax.grid(True)
plt.tight_layout()
plt.show()