"""
Peak Analysis - Multi-Measurement Comparison
=============================================
Add the folders you want to compare to the FOLDERS list below, then run the script.
"""

import math
import pickle

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colormaps
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
from sklearn.linear_model import RANSACRegressor, LinearRegression


# ---------------------------------------------------------------------------
# CONFIGURATION — edit these
# ---------------------------------------------------------------------------

#Offsets
#FOLDERS = [
#    "Data/Pipe_Can_717_n2/",
#    "Data/Pipe_Can_717_n1/",
#    "Data/Pipe_Can_717_0/",
#    "Data/Pipe_Can_717_1/",
#    "Data/Pipe_Can_717_2/",
#    "Data/Pipe_Can_717_3/"
#]

#Open Air
#FOLDERS = [
#    "Data/Air_Target_241_0/",
#    "Data/Air_Target_717_0/",
#    "Data/Air_Target2_717_0/",
#]

#Varying Pipes
FOLDERS = [
    "Data/Pipe_Can_717_0/",
    "Data/PipeLarge_Target_717_0/",
    "Data/PipeMedium_Target_717_0/"
]

#FOLDERS = [
#    "Data/Pipe_Can_717_0/",
#    "Data/Air_Target_717_0/"
#]

SHOW_ERRORBARS = True   # set to False if the chart gets too cluttered
REMOVE_OFFSET  = False  # set to True to subtract the y-intercept so all lines pass through 0,0
FONT_SIZE      = 16     # base font size for axis labels, ticks, and legend


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


def find_peak_positions(x, data_lin, data_log, threshold):
    """Return (actual_pos, measured_pos) arrays."""
    measured_pos = []

    for lin, log in zip(data_lin, data_log):
        smoothed = gaussian_filter1d(lin, sigma=1)
        peaks, _ = find_peaks(smoothed, height=threshold)
        measured_pos.append(x[peaks[0]] * 100.0 if peaks.size else None)

    return np.array(range(0, 205, 5)), np.array(measured_pos, dtype=object)


def fit_ransac(actual_pos, measured_pos):
    """RANSAC regression; returns (m, c, inlier_mask, outlier_mask)."""
    valid = [(x, y) for x, y in zip(actual_pos, measured_pos) if y is not None]
    if len(valid) < 2:
        return None, None, np.zeros(len(actual_pos), bool), np.zeros(len(actual_pos), bool)

    actual_clean   = np.array([v[0] for v in valid]).reshape(-1, 1)
    measured_clean = np.array([v[1] for v in valid], dtype=float)

    ransac = RANSACRegressor(LinearRegression(), residual_threshold=10.0)
    ransac.fit(actual_clean, measured_clean)

    m = ransac.estimator_.coef_[0]
    c = ransac.estimator_.intercept_

    # Map inlier/outlier flags back to the full-length arrays
    full_inlier  = np.zeros(len(actual_pos), bool)
    full_outlier = np.zeros(len(actual_pos), bool)
    valid_idx = [i for i, y in enumerate(measured_pos) if y is not None]
    for j, vi in enumerate(valid_idx):
        full_inlier[vi]  = ransac.inlier_mask_[j]
        full_outlier[vi] = not ransac.inlier_mask_[j]

    return m, c, full_inlier, full_outlier


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 7))
cmap = colormaps.get_cmap("tab10")

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

    actual_pos, measured_pos = find_peak_positions(
        x, data_lin, data_log, meta["threshold"]
    )

    m, c, inlier_mask, outlier_mask = fit_ransac(actual_pos, measured_pos)

    # Subtract the y-intercept from all measured values so the line passes through 0,0
    offset = c if (REMOVE_OFFSET and c is not None) else 0.0
    measured_pos = np.where(
        measured_pos != None,
        measured_pos.astype(float) - offset,
        None
    )

    actual_inliers    = actual_pos[inlier_mask]
    measured_inliers  = measured_pos[inlier_mask].astype(float)
    actual_outliers   = actual_pos[outlier_mask]
    measured_outliers = measured_pos[outlier_mask].astype(float)

    x_err = 1.0
    y_err = resolution * 50
    label = meta["title"]
    off_name = folder.split("_")[-1][0:-1]
    temp = {"n2":-2,
            "n1":-1,
            "0":0,
            "1":1,
            "2":2,
            "3":3}

    if SHOW_ERRORBARS:
        ax.errorbar(actual_inliers, measured_inliers, xerr=x_err, yerr=y_err,
                    fmt="o", capsize=3, color=colour)
        if actual_outliers.size:
            ax.errorbar(actual_outliers, measured_outliers, xerr=x_err, yerr=y_err,
                        fmt="x", capsize=3, color=colour)
    else:
        ax.plot(actual_inliers, measured_inliers, "o", color=colour)
        if actual_outliers.size:
            ax.plot(actual_outliers, measured_outliers, "x", color=colour)

    if m is not None:
        line_x = np.array([actual_pos[0], actual_pos[-1]])
        # With offset removed the effective intercept is always 0
        displayed_c = 0.0 if REMOVE_OFFSET else c
        ax.plot(line_x, m * line_x + displayed_c, "-", color=colour, linewidth=1.5,
                label=f"{label}: y={m:.2f}x+{displayed_c:.2f}")

ax.set_xlabel("Actual Position (cm)", fontsize=FONT_SIZE)
ax.set_ylabel("Measured Position (cm)" + (" (offset removed)" if REMOVE_OFFSET else ""), fontsize=FONT_SIZE)
ax.set_title("Peak Position Comparison Across Measurements", fontsize=FONT_SIZE + 2)
ax.tick_params(labelsize=FONT_SIZE)
ax.legend(fontsize=FONT_SIZE, loc="upper left")
ax.grid(True)
plt.tight_layout()
plt.show()