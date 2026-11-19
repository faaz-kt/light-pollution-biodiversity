# %% [markdown]
# # India: two maps of CHANGE 2015 -> 2025 on a 0.5 degree grid (post-hoc, EXPLORATORY)
#
# Data: results/india_change_cells.txt, copied from Colab cell "POST-HOC 5" (18 Nov 2026), one entry per 0.5 degree
# cell: ci, cj (cell = floor(lat / 0.5), floor(lon / 0.5)), light ratio (median over the cell's squares of
# (radiance 2024-25 + 0.1) / (radiance 2015-16 + 0.1)), bird change (median over squares followed in both periods of
# species per visit 2022-25 minus 2015-18), number of such squares.
# Writes results/india_map_light_change.png and results/india_map_bird_change.png.

# %%
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
RES = HERE / "results"
SURFACE, INK, INK2, EMPTY = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
DIV = LinearSegmentedColormap.from_list("div", ["#9e2b2a", "#e34948", "#f0efec", "#5598e7", "#184f95"])
MIN_SQ = 3

cells = []
for r in (RES / "india_change_cells.txt").read_text().strip().split(";"):
    v = r.split(",")
    cells.append((int(v[0]) * 0.5, int(v[1]) * 0.5, float(v[2]),
                  float(v[3]) if v[3] else np.nan, int(v[4]) if v[4] else 0))

CITIES = [("Delhi", 28.61, 77.21), ("Mumbai", 19.08, 72.88), ("Kolkata", 22.57, 88.36), ("Chennai", 13.08, 80.27),
          ("Bengaluru", 12.97, 77.59), ("Hyderabad", 17.39, 78.49), ("Ahmedabad", 23.02, 72.57),
          ("Jaipur", 26.91, 75.79), ("Lucknow", 26.85, 80.95), ("Nagpur", 21.15, 79.09), ("Bhopal", 23.26, 77.41),
          ("Bhubaneswar", 20.30, 85.82), ("Guwahati", 26.14, 91.74), ("Kochi", 9.93, 76.27), ("Pune", 18.52, 73.86)]
HALO = [pe.withStroke(linewidth=2.6, foreground=SURFACE)]


def base(title, subtitle):
    fig, ax = plt.subplots(figsize=(8.2, 9.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_xlim(67.5, 97.5)
    ax.set_ylim(6.0, 35.5)
    ax.set_aspect(1 / np.cos(np.radians(21)))
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=INK2, labelsize=7)
    ax.set_title(title, fontsize=12, color=INK, loc="left", pad=22)
    ax.text(0, 1.012, subtitle, transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")
    return fig, ax


def cities(ax):
    for name, la, lo in CITIES:
        ax.plot(lo, la, marker="o", ms=3, color=INK, zorder=5)
        ax.text(lo + 0.25, la + 0.18, name, fontsize=7, color=INK, zorder=6, path_effects=HALO)


# Map 1: light
fig, ax = base("How much brighter India got at night, 2015-16 to 2024-25",
               "Each cell (about 55 km): median change in VIIRS night light over its birded squares. "
               "Blank = no birded squares.")
norm = TwoSlopeNorm(vmin=np.log10(0.5), vcenter=0.0, vmax=np.log10(5))
cmap_l = LinearSegmentedColormap.from_list("lt", ["#2a78d6", "#f0efec", "#f2b25c", "#e34948", "#7a1f1e"])
for la, lo, ratio, _, _ in cells:
    ax.add_patch(Rectangle((lo, la), 0.5, 0.5, facecolor=cmap_l(norm(np.clip(np.log10(ratio), np.log10(0.5), np.log10(5)))),
                           edgecolor=SURFACE, linewidth=0.4, zorder=2))
cities(ax)
sm = plt.cm.ScalarMappable(cmap=cmap_l, norm=norm)
cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.06, extend="both")
ticks = [0.5, 1, 1.5, 2, 3, 5]
cb.set_ticks(np.log10(ticks), labels=[f"{t:g}x" for t in ticks])
cb.set_label("night light in 2024-25 compared with 2015-16 (1x = no change)", fontsize=8, color=INK)
cb.ax.tick_params(labelsize=7, colors=INK2)
cb.outline.set_visible(False)
fig.tight_layout()
fig.savefig(RES / "india_map_light_change.png", dpi=150, facecolor=SURFACE)

# Map 2: birds
fig, ax = base("How bird variety changed in the same places, 2015-18 to 2022-25",
               f"Each cell: median change in species per birding visit, same squares compared with themselves "
               f"(cells with >= {MIN_SQ} such squares). Light grey = too few.")
normb = TwoSlopeNorm(vmin=-6, vcenter=0, vmax=6)
for la, lo, _, ch, n in cells:
    if n >= MIN_SQ:
        color = DIV(normb(np.clip(ch, -6, 6)))
    else:
        color = EMPTY
    ax.add_patch(Rectangle((lo, la), 0.5, 0.5, facecolor=color, edgecolor=SURFACE, linewidth=0.4, zorder=2))
cities(ax)
sm = plt.cm.ScalarMappable(cmap=DIV, norm=normb)
cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.06, extend="both")
cb.set_label("change in species seen per visit (red = fewer, blue = more; a visit sees about 17)", fontsize=8,
             color=INK)
cb.ax.tick_params(labelsize=7, colors=INK2)
cb.outline.set_visible(False)
fig.tight_layout()
fig.savefig(RES / "india_map_bird_change.png", dpi=150, facecolor=SURFACE)
n_ok = sum(1 for c in cells if c[4] >= MIN_SQ)
print("saved two maps;", len(cells), "cells with light,", n_ok, "with bird change")
