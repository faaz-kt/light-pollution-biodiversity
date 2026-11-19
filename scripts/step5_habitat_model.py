# %% [markdown]
# # Step 5: is it the LIGHT, or just the CITY?
#
# Step 4 found: at equal birdwatching effort, brighter squares have fewer bird species (rho -0.30).
# But bright places are also cities: more buildings, fewer trees. And the darkest squares include the
# Western Ghats forests, which are naturally rich in birds. So "light" and "habitat" are tangled.
#
# **What this does:**
# 1. Earth Engine measures the **habitat** of every 5.5 km square: buildings, tree cover, farmland,
#    water, elevation. (Saved, so later runs skip this part.)
# 2. A **model** asks: once we know a square's habitat, does knowing its night brightness still help
#    predict how many species it has? If yes, and in the negative direction, that's evidence for a light
#    effect on its own. If light adds nothing, the step 4 pattern was really about cities and forests.
# 3. A simple **rural-only check**: among squares with almost no buildings, are brighter ones still poorer?
#
# **Data:** GHSL built-up surface 2020 (JRC, 100 m); MODIS tree cover MOD44B 2015-2024 (250 m);
# MODIS land cover MCD12Q1 2020 (500 m, farmland); JRC Global Surface Water v1.4 (30 m); SRTM elevation (90 m).
#
# **Before running, predict:** after accounting for habitat, will light's effect get stronger, weaker,
# or disappear?

# %%
# ---------------------------------------------------------------- SETTINGS --
PROJECT = "civil-clarity-442414-b7"   # Earth Engine project (only needed the first time)
CELL = 0.05                           # same squares as steps 3 and 4
REGION = "karnataka"        # "karnataka" (main study) or "kerala" (replication, see PLAN_step8_kerala.md)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]   # box around the state
MIN_VISITS = 25                       # same quality filters as step 4
BLOCK = 10                            # 10 x 10 squares (0.5°, ~55 km) = one "neighbourhood" for honest
                                      # error bars: nearby squares are similar, so they aren't independent
RURAL_MAX_BUILT = 0.02                # "rural" = less than 2% of the square covered by buildings

# %%
import sys
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
CLEAN = BASE / "clean"
HABITAT_FILE = CLEAN / f"habitat_{CELL}deg.csv"
print(f"Data folder: {CLEAN}")

# %%
# PART 1: habitat per square from Earth Engine (skipped if already saved).
WIDTH = round((LON_MAX - LON_MIN) / CELL)
HEIGHT = round((LAT_MAX - LAT_MIN) / CELL)
GRID = {
    "dimensions": {"width": WIDTH, "height": HEIGHT},
    "affineTransform": {"scaleX": CELL, "shearX": 0, "translateX": LON_MIN,
                        "shearY": 0, "scaleY": -CELL, "translateY": LAT_MAX},
    "crsCode": "EPSG:4326",
}


def square_means(image, name, max_pixels=65535):
    """Average of the image inside every square, as a HEIGHT x WIDTH numpy array (row 0 = north)."""
    import ee
    transform = [CELL, 0, LON_MIN, 0, -CELL, LAT_MAX]
    gridded = (image.rename(name)
               .reduceResolution(reducer=ee.Reducer.mean(), maxPixels=max_pixels)
               .reproject(crs="EPSG:4326", crsTransform=transform))
    pixels = ee.data.computePixels({"expression": gridded, "fileFormat": "NUMPY_NDARRAY", "grid": GRID})
    print(f"  got {name}")
    return np.array(pixels[name], dtype="float64")


if HABITAT_FILE.exists():
    print(f"Habitat already saved, loading {HABITAT_FILE.name}")
    habitat = pd.read_csv(HABITAT_FILE)
else:
    import ee
    ee.Authenticate()
    ee.Initialize(project=PROJECT)
    print("Asking Earth Engine for habitat layers ...")
    layers = {}

    # Buildings: m² of built surface per 100 m pixel. A 100 m pixel is 10,000 m², so /10000 = fraction.
    ghsl = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2020").select("built_surface")
    layers["built"] = square_means(ghsl.divide(10000), "built")

    # Tree cover %, averaged over 2015-2024. Values above 100 are codes (e.g. water), not percentages.
    # .mean() of a collection forgets the map projection, so we put the original one back.
    vcf = ee.ImageCollection("MODIS/061/MOD44B").filterDate("2015-01-01", "2025-01-01").select("Percent_Tree_Cover")
    tree = vcf.map(lambda im: im.updateMask(im.lte(100))).mean().setDefaultProjection(vcf.first().projection())
    layers["tree"] = square_means(tree.divide(100).unmask(0), "tree")

    # Farmland: MODIS land cover 2020, class 12 = cropland, 14 = cropland/natural mosaic (counted as half).
    lc = ee.Image("MODIS/061/MCD12Q1/2020_01_01").select("LC_Type1")
    crop = lc.eq(12).add(lc.eq(14).multiply(0.5))
    layers["crop"] = square_means(crop, "crop")

    # Water: fraction of the square where surface water was ever seen (lakes, tanks, rivers, reservoirs).
    try:
        gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("max_extent").unmask(0)
        layers["water"] = square_means(gsw, "water")
        water_source = "JRC GSW v1.4 max_extent (30 m)"
    except Exception as err:                      # 30 m over all of Karnataka is heavy; fall back if needed
        print(f"  JRC water too heavy ({str(err)[:80]}...), using MODIS land cover water class instead")
        layers["water"] = square_means(lc.eq(17), "water")
        water_source = "MODIS MCD12Q1 2020 class 17 (500 m)"

    # Elevation in metres (90 m SRTM).
    srtm = ee.Image("CGIAR/SRTM90_V4").select("elevation")
    layers["elevation_m"] = square_means(srtm, "elevation_m")

    rows = []
    for r in range(HEIGHT):
        for c in range(WIDTH):
            rows.append({"ilat": HEIGHT - 1 - r, "ilon": c,     # row 0 is the NORTH edge
                         **{k: v[r, c] for k, v in layers.items()}})
    habitat = pd.DataFrame(rows)
    habitat["water_source"] = water_source
    habitat.to_csv(HABITAT_FILE, index=False)
    print(f"Saved {HABITAT_FILE.name} ({len(habitat):,} squares). Water from: {water_source}")

# %%
# PART 2: put habitat next to birds + light (from step 4), and sanity-check it.
cells = pd.read_csv(CLEAN / "step4_square_all_years.csv")
d = cells.merge(habitat, on=["ilat", "ilon"], how="left")
d = d[(d["visits"] >= MIN_VISITS) & d["species_rarefied"].notna() & d["radiance_mean"].notna()].copy()
d["light"] = np.log10(d["radiance_mean"] + 0.1)     # log: going 1 -> 10 is like going 10 -> 100
print(f"Squares in the analysis: {len(d):,}")

def show(label, lat, lon):
    row = d[(d["lat"].round(2) == lat) & (d["lon"].round(2) == lon)]
    if len(row):
        r = row.iloc[0]
        print(f"  {label:<26} built {r['built']:.0%}  trees {r['tree']:.0%}  crop {r['crop']:.0%}  "
              f"water {r['water']:.0%}  elev {r['elevation_m']:.0f} m  light {r['radiance_mean']:.1f}")

print("\nSanity check (do these look right?):")
show("Bengaluru centre", 12.95, 77.55)
show("Bandipur forest area", 11.65, 76.6)
show("Agumbe, Western Ghats", 13.5, 75.05)
show("Ballari steel plant area", 15.15, 76.65)

predictors = ["light", "built", "tree", "crop", "water", "elevation_m"]
print("\nHow tangled are they? (Spearman rho between predictors)")
print(d[predictors].corr(method="spearman").round(2).to_string())

# %%
# PART 3: the model. Ordinary least squares (OLS), written out so you can see every step.
# species_rarefied = b0 + b1*light + b2*built + ... + error
# All predictors are standardised (z-scores: mean 0, sd 1), so the coefficients are comparable:
# "how many species change when this predictor goes up by one typical step".

def normal_p(z):
    """Two-sided p-value from a z statistic (normal approximation)."""
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))

def ols(data, y_col, x_cols, cluster):
    """OLS with cluster-robust standard errors (squares in the same 0.5° block may be correlated)."""
    y = data[y_col].to_numpy(float)
    Z = (data[x_cols] - data[x_cols].mean()) / data[x_cols].std()
    X = np.column_stack([np.ones(len(data)), Z.to_numpy(float)])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    # "Sandwich" variance, adding up the errors block by block instead of square by square
    meat = np.zeros((X.shape[1], X.shape[1]))
    groups = data[cluster].to_numpy()
    for g in np.unique(groups):
        s = X[groups == g].T @ resid[groups == g]
        meat += np.outer(s, s)
    G, n, k = len(np.unique(groups)), len(y), X.shape[1]
    var = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(var))
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
    table = pd.DataFrame({"coef": beta, "se": se,
                          "low95": beta - 1.96 * se, "high95": beta + 1.96 * se,
                          "p": [normal_p(b / s) for b, s in zip(beta, se)]},
                         index=["intercept"] + x_cols)
    return table, r2, G

d["block"] = (d["ilat"] // BLOCK).astype(str) + "_" + (d["ilon"] // BLOCK).astype(str)
habitat_vars = ["built", "tree", "crop", "water", "elevation_m"]

m0, r2_0, G = ols(d, "species_rarefied", habitat_vars, "block")
m1, r2_1, _ = ols(d, "species_rarefied", habitat_vars + ["light"], "block")
mL, r2_L, _ = ols(d, "species_rarefied", ["light"], "block")

print(f"{len(d):,} squares in {G} neighbourhood blocks\n")
print(f"Light alone:            R² = {r2_L:.3f}   light coef = {mL.loc['light', 'coef']:+.2f} species per SD")
print(f"Habitat only:           R² = {r2_0:.3f}")
print(f"Habitat + light:        R² = {r2_1:.3f}   (light adds {r2_1 - r2_0:+.3f})")
print("\nFull model (species per 1 SD change in each predictor, with 95% range):")
print(m1.round(3).to_string())

lc_ = m1.loc["light"]
verdict = ("light still predicts FEWER species after habitat" if lc_["high95"] < 0 else
           "light predicts MORE species after habitat" if lc_["low95"] > 0 else
           "no clear light effect once habitat is included (95% range crosses 0)")
print(f"\n=> {verdict}: {lc_['coef']:+.2f} species per SD of log-light "
      f"(95% range {lc_['low95']:+.2f} to {lc_['high95']:+.2f}, p = {lc_['p']:.3g})")

# %%
# PART 4: rural-only check. Take only squares with almost no buildings. Light there comes from villages,
# highways, industry, so it is much less tied to "city". Is light still linked to fewer species?
rural = d[d["built"] < RURAL_MAX_BUILT]
rho_rural = rural["light"].corr(rural["species_rarefied"], method="spearman")
mr, r2_r, Gr = ols(rural, "species_rarefied", ["tree", "crop", "water", "elevation_m", "light"], "block") \
    if len(rural) > 30 else (None, None, None)
print(f"Rural squares (<{RURAL_MAX_BUILT:.0%} built): {len(rural):,}")
print(f"  light vs species, raw rho = {rho_rural:+.2f}")
if mr is not None:
    lr = mr.loc["light"]
    print(f"  light coef after habitat = {lr['coef']:+.2f} (95% range {lr['low95']:+.2f} to {lr['high95']:+.2f})")

# %%
# PART 5: plots and saving
fig, axes = plt.subplots(1, 3, figsize=(17, 5.2))

coefs = m1.drop("intercept").sort_values("coef")
colors = ["#c4652f" if name == "light" else "#7a9cc6" for name in coefs.index]
axes[0].errorbar(coefs["coef"], range(len(coefs)), xerr=1.96 * coefs["se"], fmt="none", ecolor="grey")
axes[0].scatter(coefs["coef"], range(len(coefs)), color=colors, zorder=3, s=40)
axes[0].axvline(0, color="black", lw=0.8)
axes[0].set_yticks(range(len(coefs)), coefs.index)
axes[0].set_xlabel("species per 1 SD (95% range)")
axes[0].set_title("What predicts species? (habitat + light)")

# Partial effect of light: species left unexplained by habitat, against light left unexplained by habitat
def residual(data, y, xs):
    Z = (data[xs] - data[xs].mean()) / data[xs].std()
    X = np.column_stack([np.ones(len(data)), Z.to_numpy(float)])
    beta = np.linalg.lstsq(X, data[y].to_numpy(float), rcond=None)[0]
    return data[y].to_numpy(float) - X @ beta

ry = residual(d, "species_rarefied", habitat_vars)
rx = residual(d, "light", habitat_vars)
axes[1].scatter(rx, ry, s=8, alpha=0.5, color="#7a9cc6")
slope = np.polyfit(rx, ry, 1)
xs = np.linspace(rx.min(), rx.max(), 50)
axes[1].plot(xs, np.polyval(slope, xs), color="#c4652f", lw=2)
axes[1].axhline(0, color="black", lw=0.5)
axes[1].set_xlabel("light, beyond what habitat predicts")
axes[1].set_ylabel("species, beyond what habitat predicts")
axes[1].set_title("Light's own effect, habitat removed")

axes[2].scatter(rural["radiance_mean"].clip(lower=0.01), rural["species_rarefied"], s=10, alpha=0.6,
                color="#5a8f5a")
axes[2].set_xscale("log")
axes[2].set_xlabel("night brightness (log)")
axes[2].set_ylabel("species per 200 records")
axes[2].set_title(f"Rural squares only (<{RURAL_MAX_BUILT:.0%} built), rho = {rho_rural:+.2f}")

fig.tight_layout()
fig.savefig(CLEAN / "step5_model.png", dpi=130)
d.to_csv(CLEAN / "step5_analysis_table.csv", index=False)
m1.to_csv(CLEAN / "step5_model_coefficients.csv")
print(f"Saved step5_model.png, step5_analysis_table.csv, step5_model_coefficients.csv in {CLEAN}")
plt.show()

# %% [markdown]
# **How to read this:**
# - **Left:** each dot is a predictor's effect on species, with its 95% range. If the orange dot (light)
#   and its whole bar sit left of 0, light is linked to fewer species *even comparing squares with the
#   same buildings, trees, farmland, water and elevation*.
# - **Middle:** the same idea as a picture: the part of light that habitat can't explain, against the
#   part of species richness that habitat can't explain.
# - **Right:** rural squares only, where light is not mainly "city".
# - **Error bars are "cluster-robust":** squares within ~55 km of each other are treated as related, so we
#   don't pretend to have more independent data than we do.
# - **Still not proof of cause.** Light could stand in for things not measured here (noise, roads, people,
#   pollution). Stronger designs come later: changes over time (squares that got brighter 2015-2025), and
#   species traits (are nocturnal / insect-eating birds hit hardest?).
