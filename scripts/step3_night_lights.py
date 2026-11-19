# %% [markdown]
# # Step 3: how bright is each part of Karnataka at night?
#
# **What this does:** uses Google Earth Engine (Google's satellite-data service) to read the
# **VIIRS night-lights** maps: one picture of the whole Earth at night per year, made by NASA/NOAA's
# Suomi-NPP satellite and processed by the Earth Observation Group (VNL v2.1 for 2015-2021,
# v2.2 for 2022 onwards; ~460 m pixels).
# Google's servers cut out Karnataka, split it into squares of **0.05° (about 5.5 km)**, and give us the
# average brightness of each square for each year 2015-2025. We get back a small table, no big download.
#
# **Brightness unit:** nanowatts per steradian per cm² (nW/sr/cm²). Roughly: 0 = dark countryside,
# ~1-5 = villages/towns, 20-60+ = city centres.
#
# **Data citation:** Elvidge, C.D., Zhizhin, M., Ghosh, T., Hsu, F.-C., Taneja, J. (2021). Annual time
# series of global VIIRS nighttime lights derived from monthly averages: 2012 to 2019.
# *Remote Sensing* 13(5), 922. https://doi.org/10.3390/rs13050922
#
# **Before running, predict:** which year do you think Karnataka was brightest? And is the brightest
# square in Bengaluru city centre, the airport, or somewhere else?

# %%
# ---------------------------------------------------------------- SETTINGS --
PROJECT = "civil-clarity-442414-b7"   # your Earth Engine Cloud project ID

YEARS = list(range(2015, 2026))   # 2015-2025, the same years as the bird data
# The yearly maps are split over two Earth Engine collections (same source, slightly different
# processing): version 2.1 holds 2013-2021, version 2.2 holds 2022 onwards.
COLLECTIONS = ["NOAA/VIIRS/DNB/ANNUAL_V21", "NOAA/VIIRS/DNB/ANNUAL_V22"]   # later one wins if both have a year
CELL = 0.05                       # square size in degrees (~5.5 km). Bird data will use the same grid.
REGION = "karnataka"        # "karnataka" (main study) or "kerala" (replication, see PLAN_step8_kerala.md)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]   # box around the state
BAND = "average_masked"           # yearly average, with background noise / fires / auroras removed

# %%
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ee

if PROJECT.startswith("PUT-"):
    raise SystemExit("Type your Earth Engine project ID into PROJECT in the cell above first.")

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    BASE = Path("/content/drive/MyDrive/bigdata") / REGIONS[REGION]["folder"]
else:
    # Laptop: the data folder can be C:\Users\<you>\bigdata\<folder> or Downloads\bigdata\<folder> (first found).
    _options = [Path.home() / "bigdata" / REGIONS[REGION]["folder"],
                Path.home() / "Downloads" / "bigdata" / REGIONS[REGION]["folder"]]
    BASE = next((p for p in _options if p.exists()), _options[0])
OUT = BASE / "clean"
OUT.mkdir(parents=True, exist_ok=True)

# Log in to Earth Engine. The first time, it opens a Google sign-in: choose your own Google account.
ee.Authenticate()
ee.Initialize(project=PROJECT)
print("Earth Engine ready.")

# %%
# One image per year, stacked into one picture with one layer ("band") per year: y2015, y2016, ...
# First: which years exist in which collection? (Don't assume: some years can be missing.)
from datetime import datetime, timezone
source = {}                                   # year -> collection it comes from
for coll_id in COLLECTIONS:
    starts = ee.ImageCollection(coll_id).aggregate_array("system:time_start").getInfo()
    years_here = sorted({datetime.fromtimestamp(t / 1000, tz=timezone.utc).year for t in starts})
    print(f"{coll_id.split('/')[-1]}: years {years_here}")
    for y in years_here:
        source[y] = coll_id
missing = [y for y in YEARS if y not in source]
YEARS = [y for y in YEARS if y in source]
if missing:
    print(f"Not available, skipped: {missing}")
print(f"Using: {YEARS}")

layers = []
for year in YEARS:
    image = ee.ImageCollection(source[year]).filterDate(f"{year}-01-01", f"{year + 1}-01-01").first()
    layers.append(image.select(BAND).rename(f"y{year}"))
stack = ee.Image.cat(layers)

# In the "masked" maps, dark background pixels are blanked out. A blank here really means
# "no light", so we fill blanks with 0 before averaging (otherwise dark pixels would be ignored
# and rural squares would look brighter than they are).
stack = stack.unmask(0)

# Average all ~460 m pixels inside each 5.5 km square ("reduce resolution" with the mean).
width = round((LON_MAX - LON_MIN) / CELL)    # number of squares east-west
height = round((LAT_MAX - LAT_MIN) / CELL)   # number of squares north-south
transform = [CELL, 0, LON_MIN, 0, -CELL, LAT_MAX]   # where the grid sits on the map
gridded = (stack
           .reduceResolution(reducer=ee.Reducer.mean(), maxPixels=1024)
           .reproject(crs="EPSG:4326", crsTransform=transform))

# Ask Google's servers for the numbers (a small grid: width x height x 10 years).
print(f"Requesting a {width} x {height} grid x {len(YEARS)} years ...")
pixels = ee.data.computePixels({
    "expression": gridded,
    "fileFormat": "NUMPY_NDARRAY",
    "grid": {
        "dimensions": {"width": width, "height": height},
        "affineTransform": {"scaleX": CELL, "shearX": 0, "translateX": LON_MIN,
                            "shearY": 0, "scaleY": -CELL, "translateY": LAT_MAX},
        "crsCode": "EPSG:4326",
    },
})
print("Got it.")

# %%
# Turn the grid into a table: one row per square per year. Row 0 of the grid is the NORTH edge.
# lat/lon are the square's lower-left (south-west) corner, the same convention as step 1.
rows = []
for r in range(height):
    lat = round(LAT_MAX - (r + 1) * CELL, 4)
    for c in range(width):
        lon = round(LON_MIN + c * CELL, 4)
        for year in YEARS:
            rows.append((lat, lon, year, float(pixels[f"y{year}"][r, c])))
lights = pd.DataFrame(rows, columns=["lat", "lon", "year", "radiance"])
# Remember which processing version each year came from (v21 / v22): compare across the
# 2021 -> 2022 switch with care, part of any jump there may be processing, not real change.
lights["version"] = lights["year"].map(lambda y: source[y].split("_")[-1].lower())

out_file = OUT / f"nightlights_{CELL}deg_{YEARS[0]}-{YEARS[-1]}.csv"
lights.to_csv(out_file, index=False)
print(f"Saved {len(lights):,} rows to {out_file}")

# %%
# Quick checks: does it make sense?
latest = lights[lights["year"] == YEARS[-1]]
print(f"\nBrightest squares in {YEARS[-1]} (lower-left corner):")
print(latest.sort_values("radiance", ascending=False).head(8).to_string(index=False))
print(f"\nSquares that are completely dark (0): {(latest['radiance'] == 0).mean():.0%}")

per_year = lights.groupby("year")["radiance"].mean()
print("\nAverage brightness over the whole box, per year:")
print(per_year.round(3).to_string())
print("\nWere your predictions right?")

# %%
# Plots: a map of the latest year (log colours: a city is ~1000x brighter than a village)
# and how the average brightness changed over the years.
grid = latest.pivot(index="lat", columns="lon", values="radiance").sort_index()
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

shown = np.log10(grid.where(grid > 0.05))
im = axes[0].pcolormesh(np.append(grid.columns, grid.columns[-1] + CELL),
                        np.append(grid.index, grid.index[-1] + CELL),
                        shown.values, cmap="magma", shading="flat")
fig.colorbar(im, ax=axes[0], label="log10(radiance)  (0 = 1, 1 = 10, 2 = 100 nW/sr/cm²)")
axes[0].plot(77.59, 12.97, "c*", markersize=10, label="Bengaluru")
axes[0].plot(76.64, 12.30, "g*", markersize=8, label="Mysuru")
axes[0].set_facecolor("black")
axes[0].set_aspect("equal")
axes[0].legend(loc="lower left")
axes[0].set_title(f"Night lights {YEARS[-1]} ({CELL}° squares)")
axes[0].set_xlabel("longitude")
axes[0].set_ylabel("latitude")

axes[1].plot(per_year.index, per_year.values, "o-", color="#c4652f")
axes[1].set_xticks(per_year.index)                       # whole years only on the axis
axes[1].tick_params(axis="x", labelrotation=45)
if min(YEARS) <= 2021 < max(YEARS):                      # mark the version switch
    axes[1].axvline(2021.5, color="grey", linestyle="--")
    axes[1].text(2021.55, per_year.max(), "v2.1 | v2.2", color="grey", va="top")
axes[1].set_xlabel("year")
axes[1].set_ylabel("mean radiance (nW/sr/cm²)")
axes[1].set_title(f"Average night brightness of the {REGION.title()} box")

fig.tight_layout()
plot_file = OUT / "step3_nightlights.png"
fig.savefig(plot_file, dpi=130)
print(f"Plot saved to {plot_file}")
plt.show()
