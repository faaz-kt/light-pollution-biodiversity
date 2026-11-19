# %% [markdown]
# # India: map of the light effect from overlapping 150 km windows (post-hoc, EXPLORATORY)
#
# Reads results/india_posthoc_moving_window.csv (one step 5 model per window, centres every 1 degree, run in Colab:
# india_posthoc_places cell "POST-HOC 4") and results/india_posthoc_coverage_halfdeg.txt (0.5 degree cells that hold
# model squares, for the grey background). Writes results/india_light_effect_map.png.
# Windows overlap (neighbours share squares), so this is a picture, not a test.

# %%
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
RES = HERE / "results"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
# diverging: red = fewer species where brighter, grey = no change, blue = more species
CMAP = LinearSegmentedColormap.from_list("div", ["#9e2b2a", "#e34948", "#f0efec", "#5598e7", "#184f95"])
LIM = 15

mw = pd.read_csv(RES / "india_posthoc_moving_window.csv")
cov = []
for row in (RES / "india_posthoc_coverage_halfdeg.txt").read_text().strip().split("|"):
    i, js = row.split(":")
    cov += [(int(i) * 0.5, int(j) * 0.5) for j in js.split(",")]

CITIES = [("Delhi", 28.61, 77.21), ("Mumbai", 19.08, 72.88), ("Kolkata", 22.57, 88.36), ("Chennai", 13.08, 80.27),
          ("Bengaluru", 12.97, 77.59), ("Hyderabad", 17.39, 78.49), ("Ahmedabad", 23.02, 72.57), ("Pune", 18.52, 73.86),
          ("Jaipur", 26.91, 75.79), ("Lucknow", 26.85, 80.95), ("Nagpur", 21.15, 79.09), ("Bhopal", 23.26, 77.41),
          ("Raipur", 21.25, 81.63), ("Bhubaneswar", 20.30, 85.82), ("Guwahati", 26.14, 91.74), ("Kochi", 9.93, 76.27),
          ("Thiruvananthapuram", 8.52, 76.94), ("Dehradun", 30.32, 78.03), ("Visakhapatnam", 17.69, 83.22),
          ("Goa", 15.49, 73.83), ("Shimla", 31.10, 77.17)]
# label positions placed by hand near each state's data, away from the circles
STATES = [("Andhra Pradesh", 16.0, 79.6), ("Assam", 27.4, 93.6), ("Chhattisgarh", 20.9, 82.9),
          ("Gujarat", 22.0, 70.4), ("Himachal Pradesh", 32.1, 79.6), ("Karnataka", 14.0, 77.6),
          ("Kerala", 9.0, 75.2), ("Madhya Pradesh", 24.3, 79.8), ("Maharashtra", 19.9, 76.6),
          ("Odisha", 21.4, 85.3), ("Rajasthan", 26.2, 73.6), ("Tamil Nadu", 11.0, 79.4),
          ("Uttar Pradesh", 26.3, 81.7), ("Uttarakhand", 30.3, 81.3), ("West Bengal", 24.2, 88.0)]

fig, ax = plt.subplots(figsize=(8.6, 9.6), facecolor=SURFACE)
ax.set_facecolor(SURFACE)
for la, lo in cov:
    ax.add_patch(Rectangle((lo, la), 0.5, 0.5, facecolor=GRID, edgecolor="none", zorder=1))
HALO = [pe.withStroke(linewidth=2.6, foreground=SURFACE)]
for name, la, lo in STATES:
    ax.text(lo, la, name, fontsize=7.5, color=INK2, style="italic", ha="center", va="center", zorder=6,
            path_effects=HALO)
clear = (mw["coef"].abs() > 1.96 * mw["se"]).to_numpy()
norm = Normalize(-LIM, LIM)
ax.scatter(mw["lon"][~clear], mw["lat"][~clear], s=150, c=mw["coef"][~clear].clip(-LIM, LIM), cmap=CMAP, norm=norm,
           edgecolors=SURFACE, linewidths=2, zorder=3)
ax.scatter(mw["lon"][clear], mw["lat"][clear], s=150, c=mw["coef"][clear].clip(-LIM, LIM), cmap=CMAP, norm=norm,
           edgecolors=INK, linewidths=1.3, zorder=4)
for name, la, lo in CITIES:
    ax.plot(lo, la, marker="o", ms=3, color=INK, zorder=5)
    ax.text(lo + 0.25, la + 0.18, name, fontsize=7, color=INK, zorder=7, path_effects=HALO)
ax.set_xlim(67.5, 97.5)
ax.set_ylim(7.0, 35.0)
ax.set_aspect(1 / np.cos(np.radians(21)))
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(colors=INK2, labelsize=7)
ax.set_xlabel("longitude (°E)", fontsize=8, color=INK2)
ax.set_ylabel("latitude (°N)", fontsize=8, color=INK2)
ax.set_title("Where brighter squares hold fewer bird species (India, 2015-2025)", fontsize=12, color=INK, loc="left",
             pad=22)
ax.text(0, 1.012, "Each circle: one model over the squares within 150 km, after buildings, trees, farmland, water, "
        "elevation. Exploratory.", transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")
sm = plt.cm.ScalarMappable(cmap=CMAP, norm=norm)
cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.07, extend="both")
cb.set_label("change in species (per 200 records) when a square is 10x brighter", fontsize=8, color=INK)
cb.ax.tick_params(labelsize=7, colors=INK2)
cb.outline.set_visible(False)
handles = [Line2D([0], [0], marker="o", ls="", ms=9, mfc="#e34948", mec=INK, mew=1.3, label="95% range excludes 0"),
           Line2D([0], [0], marker="o", ls="", ms=9, mfc="#e34948", mec=SURFACE, mew=2, label="unclear"),
           Rectangle((0, 0), 1, 1, facecolor=GRID, edgecolor="none", label="area with data"),
           Line2D([0], [0], marker="o", ls="", ms=4, color=INK, label="city")]
leg = ax.legend(handles=handles, loc="lower right", fontsize=7.5, frameon=False, labelcolor=INK)
fig.tight_layout()
fig.savefig(RES / "india_light_effect_map.png", dpi=150, facecolor=SURFACE)
print("saved", RES / "india_light_effect_map.png", len(mw), "windows,", int(clear.sum()), "clear")
