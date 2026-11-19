# %% [markdown]
# # Step 6: change over time + which kinds of birds?
#
# Step 5 found that across space, the "fewer species where it's bright" pattern is explained by habitat
# (buildings, farmland). But light and buildings are so tangled across space that a modest light effect
# can't be ruled out. Two sharper questions, done together:
#
# 1. **Change over time (2015-2025).** Karnataka's night lights nearly doubled, much faster than buildings.
#    Compare each square **with its own past**: did squares that got brighter than expected change, after
#    accounting for their new buildings? Comparing a square with itself cancels everything fixed about it
#    (forest, lakes, altitude, how good the birding is). This is a "two-way fixed effects" model.
# 2. **Species traits.** Light should matter for particular birds, not all equally:
#    - **night birds** (owls, nightjars, frogmouths, stone-curlews, night herons): their world is the dark,
#    - **insect-eaters**: lights pull insects in (food?) but also kill them (less food?),
#    - **migrants**: many migrate at night and lights disorient them.
#    For each group we measure its **share** of the species seen on a birdwatching visit. A share is fair
#    even if visits get longer or shorter: both the group and the total change together.
#
# **Trait data:** AVONET (Tobias et al. 2022, Ecology Letters, doi:10.1111/ele.13898; data CC BY 4.0,
# doi:10.6084/m9.figshare.16586228). Buildings over time: GHSL built-up surface 2015, 2020, 2025.
#
# **Before running, predict** for each group: when a square gets brighter, does its share go up, down,
# or stay the same? (Night birds? Insect-eaters? Migrants?)

# %%
# ---------------------------------------------------------------- SETTINGS --
PROJECT = "civil-clarity-442414-b7"   # Earth Engine project (only for the buildings-over-time layer)
CELL = 0.05
REGION = "karnataka"        # "karnataka" (main study) or "kerala" (replication, see PLAN_step8_kerala.md)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]   # box around the state
YEARS = list(range(2015, 2026))
MIN_VISITS_YEAR = 10        # a square-year needs at least this many visits to be used
MIN_YEARS = 3               # and a square needs at least this many usable years for the time model
MIN_VISITS_TOTAL = 25       # for the across-space (pooled) model, as in steps 4-5
BLOCK = 10                  # 0.5° neighbourhoods for honest error bars, as in step 5
AVONET_URL = "https://ndownloader.figshare.com/files/34480856"   # AVONET Supplementary dataset 1.xlsx

# Night birds, by family (and two night-heron genera). Families are as named in GBIF / Catalogue of Life.
NOCTURNAL_FAMILIES = {"Strigidae", "Tytonidae", "Caprimulgidae", "Podargidae", "Burhinidae"}
NOCTURNAL_GENERA = {"Nycticorax", "Gorsachius"}

# %%
import sys
import time
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
TRAITS_DIR = BASE / "traits"
TRAITS_DIR.mkdir(parents=True, exist_ok=True)
print(f"Data folder: {BASE}")

# %%
# PART 1: species traits. Download AVONET once (21 MB), keep the eBird-taxonomy sheet as a small CSV.
avonet_csv = TRAITS_DIR / "avonet_ebird.csv"
if not avonet_csv.exists():
    xlsx = TRAITS_DIR / "AVONET_Supplementary_dataset_1.xlsx"
    if not xlsx.exists():
        import requests
        print("Downloading AVONET (21 MB) ...")
        r = requests.get(AVONET_URL, timeout=300)
        r.raise_for_status()
        xlsx.write_bytes(r.content)
    sheets = pd.ExcelFile(xlsx).sheet_names
    sheet = next(s for s in sheets if "ebird" in s.lower())
    av = pd.read_excel(xlsx, sheet_name=sheet)
    av.to_csv(avonet_csv, index=False)
    print(f"Saved AVONET sheet '{sheet}' ({len(av):,} species) to {avonet_csv.name}")
av = pd.read_csv(avonet_csv)
name_col = next(c for c in av.columns if c.lower().startswith("species"))
av = av.rename(columns={name_col: "avonet_name"})
av["key"] = av["avonet_name"].str.strip().str.lower()
print(f"AVONET columns used: {name_col}, Trophic.Niche, Migration")

# %%
# PART 2: read the bird table (step 2) and make "visits": one observer, one square, one day.
COLS = ["species", "family", "decimalLatitude", "decimalLongitude", "year", "month", "day", "recordedBy"]
parts = sorted((CLEAN / "birds_parts").glob("part_*"))
rows = []
start = time.time()
for i, p in enumerate(parts):
    b = pd.read_parquet(p, columns=COLS) if p.suffix == ".parquet" else pd.read_csv(p, usecols=COLS)
    b["ilat"] = np.floor((b["decimalLatitude"].astype("float64") - LAT_MIN) / CELL + 1e-9).astype("int16")
    b["ilon"] = np.floor((b["decimalLongitude"].astype("float64") - LON_MIN) / CELL + 1e-9).astype("int16")
    b["day"] = b["day"].fillna(0).astype("int8")
    b = b[b["year"].isin(YEARS)]
    keep = ["ilat", "ilon", "year", "month", "day", "recordedBy", "species", "family"]
    rows.append(b[keep].drop_duplicates())          # one row per species per visit
    print(f"  piece {i + 1}/{len(parts)} ({(time.time() - start) / 60:.1f} min)")
det = pd.concat(rows, ignore_index=True).drop_duplicates(
    subset=["ilat", "ilon", "year", "month", "day", "recordedBy", "species"])
for c in ["recordedBy", "species", "family"]:
    det[c] = det[c].astype("category")              # saves a lot of memory
print(f"Species-detections (one per species per visit): {len(det):,}")

# %%
# PART 3: give every species its traits, and check how many records we could match.
species = pd.DataFrame({"species": det["species"].cat.categories})
species["key"] = species["species"].str.strip().str.lower()
fam = det.drop_duplicates("species").set_index("species")["family"].astype(str)
species["family"] = species["species"].map(fam)
species = species.merge(av[["key", "avonet_name", "Trophic.Niche", "Migration"]], on="key", how="left")
species["genus"] = species["species"].str.split().str[0]
species["nocturnal"] = (species["family"].isin(NOCTURNAL_FAMILIES) |
                        species["genus"].isin(NOCTURNAL_GENERA)).astype(float)
species["insectivore"] = np.where(species["Trophic.Niche"].isna(), np.nan,
                                  (species["Trophic.Niche"] == "Invertivore").astype(float))
species["migrant"] = np.where(species["Migration"].isna(), np.nan, (species["Migration"] == 3).astype(float))
species["matched"] = species["avonet_name"].notna()
species.to_csv(CLEAN / "step6_species_traits.csv", index=False)

counts = det["species"].value_counts()
species["detections"] = species["species"].map(counts).fillna(0)
share_matched = species.loc[species["matched"], "detections"].sum() / species["detections"].sum()
print(f"Species matched to AVONET: {species['matched'].sum()} of {len(species)} "
      f"({share_matched:.1%} of all detections)")
print("Most-detected species NOT matched (name differences between taxonomies):")
print(species[~species["matched"]].nlargest(8, "detections")[["species", "detections"]].to_string(index=False))
print()
print(f"Night-bird species: {int(species['nocturnal'].sum())}, e.g. "
      f"{', '.join(species[species['nocturnal'] == 1].nlargest(5, 'detections')['species'])}")
print(f"Insect-eaters: {int(species['insectivore'].sum())}, migrants: {int(species['migrant'].sum())}")

# %%
# PART 4: per visit, how many species, and how many of each group? Then per square-year.
tr = species.set_index("species")
for g in ["nocturnal", "insectivore", "migrant"]:
    det[g] = det["species"].map(tr[g]).astype("float32")
det["has_avonet"] = det["species"].map(tr["matched"]).astype(bool)

visit_key = ["ilat", "ilon", "year", "month", "day", "recordedBy"]
v = det.groupby(visit_key, observed=True).agg(
    n_species=("species", "size"),
    n_matched=("has_avonet", "sum"),
    n_nocturnal=("nocturnal", "sum"),
    n_insectivore=("insectivore", "sum"),
    n_migrant=("migrant", "sum"),
).reset_index()
print(f"Visits: {len(v):,}")

sy = v.groupby(["ilat", "ilon", "year"]).agg(
    visits=("n_species", "size"),
    species_per_visit=("n_species", "mean"),
    det_all=("n_species", "sum"), det_matched=("n_matched", "sum"),
    det_nocturnal=("n_nocturnal", "sum"), det_insectivore=("n_insectivore", "sum"),
    det_migrant=("n_migrant", "sum"),
).reset_index()
# Shares in PERCENT of detections. Night birds use all detections (family-based, no AVONET needed);
# insect-eaters and migrants use only AVONET-matched detections.
sy["pct_nocturnal"] = 100 * sy["det_nocturnal"] / sy["det_all"]
sy["pct_insectivore"] = 100 * sy["det_insectivore"] / sy["det_matched"]
sy["pct_migrant"] = 100 * sy["det_migrant"] / sy["det_matched"]

# %%
# PART 5: light per square-year (step 3) and buildings per year (GHSL 2015/2020/2025, straight lines between).
lights = pd.read_csv(sorted(CLEAN.glob("nightlights_*deg_2015-*.csv"))[-1])
lights["ilat"] = np.rint((lights["lat"] - LAT_MIN) / CELL).astype("int16")
lights["ilon"] = np.rint((lights["lon"] - LON_MIN) / CELL).astype("int16")
sy = sy.merge(lights[["ilat", "ilon", "year", "radiance", "version"]], on=["ilat", "ilon", "year"], how="left")
sy["light"] = np.log10(sy["radiance"] + 0.1)   # +1 = ten times brighter

built_file = CLEAN / f"built_by_epoch_{CELL}deg.csv"
if not built_file.exists():
    import ee
    ee.Authenticate()
    ee.Initialize(project=PROJECT)
    W, H = round((LON_MAX - LON_MIN) / CELL), round((LAT_MAX - LAT_MIN) / CELL)
    grid = {"dimensions": {"width": W, "height": H},
            "affineTransform": {"scaleX": CELL, "shearX": 0, "translateX": LON_MIN,
                                "shearY": 0, "scaleY": -CELL, "translateY": LAT_MAX},
            "crsCode": "EPSG:4326"}
    out = []
    for epoch in [2015, 2020, 2025]:
        img = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{epoch}").select("built_surface").divide(10000).rename("b")
        img = img.reduceResolution(reducer=ee.Reducer.mean(), maxPixels=65535).reproject(
            crs="EPSG:4326", crsTransform=[CELL, 0, LON_MIN, 0, -CELL, LAT_MAX])
        px = np.array(ee.data.computePixels({"expression": img, "fileFormat": "NUMPY_NDARRAY",
                                             "grid": grid})["b"], dtype="float64")
        for r in range(H):
            for c in range(W):
                out.append((H - 1 - r, c, epoch, px[r, c]))
        print(f"  got buildings {epoch}")
    pd.DataFrame(out, columns=["ilat", "ilon", "epoch", "built"]).to_csv(built_file, index=False)
built = pd.read_csv(built_file).pivot_table(index=["ilat", "ilon"], columns="epoch", values="built")
yrs = sy["year"].to_numpy()
b15, b20, b25 = (sy.set_index(["ilat", "ilon"]).index.map(built[e]).to_numpy(float) for e in [2015, 2020, 2025])
sy["built"] = np.where(yrs <= 2020, b15 + (b20 - b15) * (yrs - 2015) / 5, b20 + (b25 - b20) * (yrs - 2020) / 5)

sy["block"] = (sy["ilat"] // BLOCK).astype(str) + "_" + (sy["ilon"] // BLOCK).astype(str)
sy["square"] = sy["ilat"].astype(str) + "_" + sy["ilon"].astype(str)
sy.to_csv(CLEAN / "step6_square_year.csv", index=False)
print(f"Saved step6_square_year.csv ({len(sy):,} square-years)")

# %%
# PART 6: the two-way fixed-effects (TWFE) model, written out.
# y[square, year] = (square's own level) + (that year's level everywhere) + b_light*light + b_built*built + error
# "Square's own level" absorbs everything fixed about a square; "year's level" absorbs changes everywhere at
# once (eBird growing, the 2021->2022 satellite processing switch, COVID). So b_light only comes from squares
# that brightened MORE or LESS than the average square that year.

def normal_p(z):
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))

def demean_two_way(df, cols, w, a="square", b="year", tol=1e-10, max_iter=500):
    """Weighted 'within' transformation: remove square and year averages (repeat until stable)."""
    out = df[cols].astype(float).copy()
    for _ in range(max_iter):
        before = out.to_numpy().copy()
        for g in (a, b):
            means = (out.mul(w, axis=0)).groupby(df[g]).transform("sum").div(w.groupby(df[g]).transform("sum"), axis=0)
            out = out - means
        if np.abs(out.to_numpy() - before).max() < tol:
            break
    return out

def twfe(df, y, xs, weight="visits", cluster="block"):
    d = df.dropna(subset=[y] + xs).copy()
    w = d[weight].astype(float)
    dm = demean_two_way(d, [y] + xs, w)
    X, Y, sw = dm[xs].to_numpy(), dm[y].to_numpy(), np.sqrt(w.to_numpy())
    Xw, Yw = X * sw[:, None], Y * sw
    XtX_inv = np.linalg.inv(Xw.T @ Xw)
    beta = XtX_inv @ Xw.T @ Yw
    e = Yw - Xw @ beta
    groups = d[cluster].to_numpy()
    meat = np.zeros((len(xs), len(xs)))
    for g in np.unique(groups):
        s = Xw[groups == g].T @ e[groups == g]
        meat += np.outer(s, s)
    G = len(np.unique(groups))
    se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv * G / (G - 1)))
    return pd.DataFrame({"coef": beta, "se": se, "low95": beta - 1.96 * se, "high95": beta + 1.96 * se,
                         "p": [normal_p(b / s) for b, s in zip(beta, se)]}, index=xs), len(d), d["square"].nunique()

panel = sy[(sy["visits"] >= MIN_VISITS_YEAR) & sy["light"].notna()].copy()
good = panel.groupby("square")["year"].transform("size") >= MIN_YEARS
panel = panel[good]
print(f"Time model uses {len(panel):,} square-years from {panel['square'].nunique()} squares")
print(f"Light change inside squares, 2015->2025 median: x{10 ** panel.groupby('square')['light'].agg(lambda s: s.max() - s.min()).median():.2f}")

RESPONSES = {"species_per_visit": "all species (per visit)",
             "pct_nocturnal": "night birds (% of detections)",
             "pct_insectivore": "insect-eaters (%)",
             "pct_migrant": "migrants (%)"}
results = []
for y, label in RESPONSES.items():
    tab, n, ns = twfe(panel, y, ["light", "built"])
    r = tab.loc["light"]
    results.append({"analysis": "over time (within squares)", "response": label, "n": n, **r.to_dict()})
    print(f"{label:<32} light: {r['coef']:+.3f} per 10x brighter (95% {r['low95']:+.3f} to {r['high95']:+.3f}), p={r['p']:.3g}")

# %%
# PART 7: the same groups ACROSS SPACE (all years pooled), with the step 5 habitat controls.
habitat = pd.read_csv(CLEAN / f"habitat_{CELL}deg.csv")
pooled = sy.groupby(["ilat", "ilon"]).agg(
    visits=("visits", "sum"), det_all=("det_all", "sum"), det_matched=("det_matched", "sum"),
    det_nocturnal=("det_nocturnal", "sum"), det_insectivore=("det_insectivore", "sum"),
    det_migrant=("det_migrant", "sum"),
    species_per_visit=("species_per_visit", "mean"), radiance=("radiance", "mean")).reset_index()
pooled["pct_nocturnal"] = 100 * pooled["det_nocturnal"] / pooled["det_all"]
pooled["pct_insectivore"] = 100 * pooled["det_insectivore"] / pooled["det_matched"]
pooled["pct_migrant"] = 100 * pooled["det_migrant"] / pooled["det_matched"]
pooled["light"] = np.log10(pooled["radiance"] + 0.1)
pooled = pooled.merge(habitat.drop(columns=["water_source"], errors="ignore"), on=["ilat", "ilon"], how="left")
pooled = pooled[pooled["visits"] >= MIN_VISITS_TOTAL].dropna(subset=["light", "built", "tree"])
pooled["block"] = (pooled["ilat"] // BLOCK).astype(str) + "_" + (pooled["ilon"] // BLOCK).astype(str)

def ols_raw(df, y, xs, weight="visits", cluster="block"):
    """Weighted OLS with an intercept and cluster-robust errors; coefficients in the predictors' own units."""
    d = df.dropna(subset=[y] + xs)
    xs = [x for x in xs if d[x].std() > 1e-9]       # a predictor that never varies can't be estimated
    w = np.sqrt(d[weight].astype(float).to_numpy())
    X = np.column_stack([np.ones(len(d)), d[xs].to_numpy(float)]) * w[:, None]
    Y = d[y].to_numpy(float) * w
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    e = Y - X @ beta
    groups = d[cluster].to_numpy()
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in np.unique(groups):
        s = X[groups == g].T @ e[groups == g]
        meat += np.outer(s, s)
    G = len(np.unique(groups))
    se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv * G / (G - 1)))
    return pd.DataFrame({"coef": beta, "se": se, "low95": beta - 1.96 * se, "high95": beta + 1.96 * se,
                         "p": [normal_p(b / s) for b, s in zip(beta, se)]}, index=["intercept"] + xs), len(d)

controls = ["built", "tree", "crop", "water", "elevation_m"]
print(f"Across-space model uses {len(pooled):,} squares (habitat as in step 5)")
for y, label in RESPONSES.items():
    tab, n = ols_raw(pooled, y, ["light"] + controls)
    r = tab.loc["light"]
    results.append({"analysis": "across space (habitat controlled)", "response": label, "n": n, **r.to_dict()})
    print(f"{label:<32} light: {r['coef']:+.3f} per 10x brighter (95% {r['low95']:+.3f} to {r['high95']:+.3f}), p={r['p']:.3g}")

res = pd.DataFrame(results)
res.to_csv(CLEAN / "step6_results.csv", index=False)

# %%
# PART 8: plot. Each row = a bird group; dot = effect of a square being 10x brighter, bar = 95% range.
fig, axes = plt.subplots(1, 3, figsize=(17, 5), gridspec_kw={"width_ratios": [1.2, 1.2, 1]})
for ax, analysis, color in zip(axes[:2], ["over time (within squares)", "across space (habitat controlled)"],
                               ["#c4652f", "#4a7ab8"]):
    sub = res[res["analysis"] == analysis].iloc[::-1]
    pos = range(len(sub))
    ax.errorbar(sub["coef"], pos, xerr=[sub["coef"] - sub["low95"], sub["high95"] - sub["coef"]],
                fmt="o", color=color, ecolor="grey", capsize=3)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(list(pos), sub["response"])
    ax.set_xlabel("change when a square is 10x brighter")
    ax.set_title(analysis)

# Right: night-bird share over the years in squares that brightened most vs least
change = panel.sort_values("year").groupby("square")["light"].agg(lambda s: s.iloc[-1] - s.iloc[0])  # last - first year
q = change.quantile([0.25, 0.75])
for label, squares, color in [("brightened least (bottom 25%)", change[change <= q[0.25]].index, "#5a8f5a"),
                              ("brightened most (top 25%)", change[change >= q[0.75]].index, "#c4652f")]:
    s = panel[panel["square"].isin(squares)]
    yearly = s.groupby("year").apply(lambda g: 100 * g["det_nocturnal"].sum() / g["det_all"].sum())
    axes[2].plot(yearly.index, yearly.values, "o-", color=color, label=label)
axes[2].set_xlabel("year")
axes[2].set_ylabel("night birds, % of detections")
axes[2].set_title("Night birds: brightening vs stable squares")
axes[2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(CLEAN / "step6_time_and_traits.png", dpi=130)
print(f"Saved step6_results.csv, step6_square_year.csv, step6_species_traits.csv, step6_time_and_traits.png in {CLEAN}")
plt.show()

# %% [markdown]
# **How to read this:**
# - **Left (over time):** the strongest test here. A dot left of 0 with its whole bar = when a square got
#   brighter than the average square did that year, that group's share fell, beyond what new buildings explain.
# - **Middle (across space):** the step 5 comparison, now per group: bright vs dark squares with the same habitat.
# - **If both agree**, that's much more convincing than either alone. If they disagree, say so honestly.
# - **Caveats:** shares are about *what birdwatchers record*: night birds are under-recorded because few people
#   birdwatch at night, and that could itself change with light (lit areas are easier to visit at night).
#   AVONET's "migrant" is global, not Karnataka-specific. Species whose names differ between taxonomies are
#   left out of the insect-eater/migrant shares (the match rate is printed above).
