"""Regenerates the sample images of this template (needs matplotlib).
    python figures/make_samples.py
Replace them with your own figures; nothing else depends on them."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "stix", "font.size": 11})

# a vector plot (PDF): two quantities over five cases -- used by figures and shapes
cases = ["C1", "C2", "C3", "C4", "C5"]
a = [1.90, 1.83, 1.88, 1.78, 1.57]
b = [0.38, 0.33, 0.34, 0.62, 0.95]
fig, ax = plt.subplots(figsize=(4.2, 3.0))
ax.plot(cases, a, "o-", color="#0072bd", label="Quantity A")
ax.set_ylabel("Quantity A", color="#0072bd")
ax2 = ax.twinx()
ax2.plot(cases, b, "s-", color="#d95319", label="Quantity B")
ax2.set_ylabel("Quantity B", color="#d95319")
fig.legend(loc="upper center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.9))
fig.savefig(os.path.join(HERE, "sample-plot.pdf"))
plt.close(fig)

# a raster image (PNG): a smooth field
x, y = np.meshgrid(np.linspace(-3, 3, 300), np.linspace(-2, 2, 200))
field = np.sin(2 * x) * np.exp(-y ** 2) + 0.5 * np.cos(3 * y + x)
fig, ax = plt.subplots(figsize=(4.2, 2.8))
ax.contourf(x, y, field, 24, cmap="RdBu_r")
ax.set_xlabel("$x$")
ax.set_ylabel("$y$")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "sample-field.png"), dpi=110)
plt.close(fig)

# animation frames: four cases, frames 0, 2, ..., 22 -> anim/case<k>_<n>.png
t = np.linspace(0, 2 * np.pi, 200)
for k, speed in enumerate((1.0, 1.5, 2.0, 3.0), 1):
    for n in range(0, 24, 2):
        fig, ax = plt.subplots(figsize=(2.4, 1.8))
        ph = speed * n * np.pi / 12
        ax.plot(t, np.sin(t - ph), color="#1f497d", lw=2)
        ax.plot(t, 0.5 * np.sin(2 * t + ph), color="#d95319", lw=1.5, ls="--")
        ax.set_ylim(-1.2, 1.2)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout(pad=0.2)
        fig.savefig(os.path.join(HERE, "anim", "case%d_%d.png" % (k, n)), dpi=100)
        plt.close(fig)

# a time series (CSV): three responses settling to a steady oscillation --
# plotted by slideplot (one file, a column per case)
ts = np.round(np.arange(0, 40.0001, 0.02), 2)
cols = [np.round(amp * (1 - np.exp(-ts / 6)) * np.sin(2 * np.pi * f * ts), 5)
        for amp, f in ((0.6, 0.20), (0.45, 0.24), (0.15, 0.31))]
with open(os.path.join(HERE, "sample-response.csv"), "w") as f:
    f.write("time,case1,case2,case3\n")
    for row in zip(ts, *cols):
        f.write(",".join("%g" % v for v in row) + "\n")

# a video (MP4, needs ffmpeg): the field travelling for 4 s -> sample-video.mp4,
# its first frame -> sample-video.png (the poster)
import shutil
import subprocess
import tempfile
if shutil.which("ffmpeg"):
    with tempfile.TemporaryDirectory() as tmp:
        for n in range(100):
            ph = n * 2 * np.pi / 100
            f = np.sin(2 * x - ph) * np.exp(-y ** 2) + 0.5 * np.cos(3 * y + x + ph)
            fig = plt.figure(figsize=(4.8, 2.7), dpi=100)
            ax = fig.add_axes((0, 0, 1, 1))
            ax.contourf(x, y, f, 24, cmap="RdBu_r")
            ax.set_axis_off()
            fig.savefig(os.path.join(tmp, "f%03d.png" % n))
            if n == 0:
                fig.savefig(os.path.join(HERE, "sample-video.png"))
            plt.close(fig)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25",
                        "-i", os.path.join(tmp, "f%03d.png"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "28", "-movflags", "+faststart",
                        os.path.join(HERE, "sample-video.mp4")], check=True)
else:
    print("ffmpeg not found: sample-video.mp4 not made")
