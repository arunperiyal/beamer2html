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
