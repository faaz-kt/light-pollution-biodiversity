# %% [markdown]
# # Step 9: is Kerala's "fewer species where brighter" just the coastline?
#
# In Kerala (not Karnataka), step 5 found fewer species in brighter squares even after habitat
# (-7.4 species per SD of light). Unplanned, so exploratory. First suspect: **the coast**. Coastal squares
# are bright and crowded, and part of them is sea. Our water layer (JRC surface water) doesn't count the open
# sea, so a half-sea square looks like a normal square that just has few birds.
#
# Check: measure the **land fraction** of every square (Hansen/UMD global data mask: 1 = land) and
# 1. add it to the step 5 model as one more control, and
# 2. refit using only squares that are almost all land (>= 95%).
# If the light effect shrinks a lot, the coast was the cause. Run for both states.
#
# Note: "land" here means not sea and not lake or river, so the land fraction overlaps a little with the water control.
#
# Tested first on two fake worlds. (A) The coast is bright and has fewer species, light itself does nothing: the
# step 5 model says light is harmful (-1.8 per SD in fake Kerala), but with the land control or inland squares only
# it drops to about zero (-0.2, ranges crossing zero). (B) Light really removes species (planted -5 per SD): the
# effect stays clearly negative in all three versions (-6.8, -5.2, -4.5). So the check can tell the two apart.

# %%
# ---------------------------------------------------------------- SETTINGS --
PROJECT = "civil-clarity-442414-b7"   # Earth Engine project
CELL = 0.05
RUN_REGIONS = ["karnataka", "kerala"]
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
BLOCK = 10
INLAND_MIN_LAND = 0.95        # "inland" = at least 95% of the square is land
HANSEN = ["UMD/hansen/global_forest_change_2024_v1_12", "UMD/hansen/global_forest_change_2023_v1_11"]

import sys
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    ROOT = Path("/content/drive/MyDrive/bigdata")
else:
    _options = [Path.home() / "bigdata", Path.home() / "Downloads" / "bigdata"]
    ROOT = next((p for p in _options if p.exists()), _options[0])


def land_fraction(region):
    """Share of each square that is land (Hansen data mask == 1), cached as land_0.05deg.csv."""
    clean = ROOT / REGIONS[region]["folder"] / "clean"
    out = clean / f"land_{CELL}deg.csv"
    if out.exists():
        return pd.read_csv(out)
    import ee
    ee.Authenticate()
    ee.Initialize(project=PROJECT)
    (lat_min, lat_max), (lon_min, lon_max) = REGIONS[region]["lat"], REGIONS[region]["lon"]
    W, H = round((lon_max - lon_min) / CELL), round((lat_max - lat_min) / CELL)
    grid_spec = {"dimensions": {"width": W, "height": H},
                 "affineTransform": {"scaleX": CELL, "shearX": 0, "translateX": lon_min,
                                     "shearY": 0, "scaleY": -CELL, "translateY": lat_max},
                 "crsCode": "EPSG:4326"}

    def square_mean(image):
        gridded = image.rename("land").reduceResolution(reducer=ee.Reducer.mean(), maxPixels=65535).reproject(
            crs="EPSG:4326", crsTransform=[CELL, 0, lon_min, 0, -CELL, lat_max])
        px = ee.data.computePixels({"expression": gridded, "fileFormat": "NUMPY_NDARRAY", "grid": grid_spec})
        return np.array(px["land"], dtype="float64")

    arr, asset = None, None
    for name in HANSEN:                          # Hansen data mask, 30 m: 1 = land (sea, lakes, rivers are not 1)
        try:
            arr, asset = square_mean(ee.Image(name).select("datamask").eq(1).unmask(0)), name
            break
        except Exception as err:
            print(f"  {name} didn't work ({str(err)[:80]}...)")
    if arr is None:                              # fallback: MODIS land/water mask, 250 m (water_mask 1 = water)
        modis = ee.ImageCollection("MODIS/061/MOD44W").sort("system:time_start", False).first()
        arr, asset = square_mean(modis.select("water_mask").eq(0).unmask(0)), "MODIS/061/MOD44W"
    rows = [(H - 1 - r, c, arr[r, c]) for r in range(H) for c in range(W)]   # row 0 is the NORTH edge
    table = pd.DataFrame(rows, columns=["ilat", "ilon", "land_frac"])
    table["source"] = asset
    table.to_csv(out, index=False)
    print(f"  {region}: saved {out.name} from {asset}")
    return table

# %%
def normal_p(z):
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))

def ols(data, y_col, x_cols, cluster):
    """Same model as step 5: standardised predictors, cluster-robust errors over 0.5-degree blocks."""
    y = data[y_col].to_numpy(float)
    Z = (data[x_cols] - data[x_cols].mean()) / data[x_cols].std()
    X = np.column_stack([np.ones(len(data)), Z.to_numpy(float)])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]))
    groups = data[cluster].to_numpy()
    for g in np.unique(groups):
        s = X[groups == g].T @ resid[groups == g]
        meat += np.outer(s, s)
    G, n, k = len(np.unique(groups)), len(y), X.shape[1]
    var = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(var))
    return pd.DataFrame({"coef": beta, "se": se, "low95": beta - 1.96 * se, "high95": beta + 1.96 * se,
                         "p": [normal_p(b / s) for b, s in zip(beta, se)]}, index=["intercept"] + x_cols)

habitat_vars = ["built", "tree", "crop", "water", "elevation_m"]
CHECK_PLACES = {"karnataka": [("Mangaluru (coast)", 12.87, 74.84), ("Bengaluru (inland)", 12.97, 77.59)],
                "kerala": [("Kochi (coast)", 9.97, 76.27), ("Munnar (inland)", 10.09, 77.06)]}
rows = []
for region in RUN_REGIONS:
    clean = ROOT / REGIONS[region]["folder"] / "clean"
    land = land_fraction(region)
    (lat_min, _), (lon_min, _) = REGIONS[region]["lat"], REGIONS[region]["lon"]
    for name, lat, lon in CHECK_PLACES[region]:      # sanity check: is the map the right way up?
        i, j = int(np.floor((lat - lat_min) / CELL)), int(np.floor((lon - lon_min) / CELL))
        val = land.loc[(land["ilat"] == i) & (land["ilon"] == j), "land_frac"]
        print(f"  {region} {name:<20} land {val.iloc[0]:.0%}" if len(val) else f"  {name}: not in grid")
    d = pd.read_csv(clean / "step5_analysis_table.csv")
    d = d.merge(land[["ilat", "ilon", "land_frac"]], on=["ilat", "ilon"], how="left")
    missing = d[habitat_vars + ["land_frac", "light", "species_rarefied"]].isna().any(axis=1)
    if missing.any():
        print(f"  {region}: {missing.sum()} squares have a missing value and are left out")
        d = d[~missing].copy()
    d["block"] = (d["ilat"] // BLOCK).astype(str) + "_" + (d["ilon"] // BLOCK).astype(str)
    inland = d[d["land_frac"] >= INLAND_MIN_LAND]
    print(f"{region}: {len(d)} squares, {len(inland)} inland; light~land rho = "
          f"{d['light'].corr(d['land_frac'], method='spearman'):+.2f}; "
          f"species~land rho = {d['species_rarefied'].corr(d['land_frac'], method='spearman'):+.2f}")
    for label, data, xs in [("step 5 model", d, habitat_vars + ["light"]),
                            ("+ land fraction", d, habitat_vars + ["land_frac", "light"]),
                            ("inland squares only", inland, habitat_vars + ["light"])]:
        r = ols(data, "species_rarefied", xs, "block").loc["light"]
        rows.append({"region": region, "model": label, "squares": len(data), **r.to_dict()})

res = pd.DataFrame(rows)
for region in RUN_REGIONS:
    res[res["region"] == region].to_csv(ROOT / REGIONS[region]["folder"] / "clean" / "step9_land_check.csv",
                                        index=False)
print()
print("Light effect on species per 200 records (per 1 SD of log-light), after habitat:")
for r in res.itertuples():
    print(f"  {r.region:<10}{r.model:<22}{r.squares:>5} sq  {r.coef:+6.2f}  [{r.low95:+.2f}, {r.high95:+.2f}]  p={r.p:.3g}")

# %% [markdown]
# ## Results (run 18 Nov 2026, Colab; land fraction from UMD/hansen/global_forest_change_2024_v1_12)
#
# Map check: Mangaluru's square is 57% land, Bengaluru's 100%, Kochi's 69%, Munnar's 100%, so the grid is the
# right way up.
#
# | State | Model | Squares | Light effect (species per SD of light) | 95% range | p |
# |---|---|---|---|---|---|
# | Karnataka | step 5 model | 1,020 | -0.23 | -2.20 to +1.75 | 0.82 |
# | Karnataka | + land fraction | 1,020 | -0.40 | -2.44 to +1.64 | 0.70 |
# | Karnataka | inland squares only | 903 | -0.53 | -2.81 to +1.75 | 0.65 |
# | Kerala | step 5 model | 1,054 | -7.40 | -10.07 to -4.74 | 5e-8 |
# | Kerala | + land fraction | 1,054 | -7.23 | -9.95 to -4.52 | 2e-7 |
# | Kerala | inland squares only | 872 | -7.89 | -10.95 to -4.82 | 5e-7 |
#
# **The coastline does not explain Kerala's result.** Adding land fraction or dropping every square with more than
# 5% sea, lake or river changes almost nothing. Coastal squares are not even poorer in species (species vs land
# fraction: rho +0.09 in Kerala, -0.11 in Karnataka). Karnataka stays near zero either way.
#
# What is left (not tested, and this result was found after looking, so it is exploratory):
# - **Light may be a better measure of "how urban" than our building layer.** Kerala's towns are spread thinly
#   along roads, so the building map may miss the urban spread that night lights pick up. Then "light" would be
#   standing in for urbanisation, not acting on its own.
# - **Who goes birding where.** Bright squares may get more short, casual lists; forest squares more expert
#   surveys (e.g. the Kerala Bird Atlas). Rarefaction makes the number of records equal, not the observers' skill.
# - **A real effect of light**, which would then need a reason why Kerala and not Karnataka.
#
# Telling these apart needs a new written plan and data that splits them (e.g. effort or observer-skill
# information, or a better urbanisation map), not more tries on the same data.
