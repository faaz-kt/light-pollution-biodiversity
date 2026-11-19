# %% [markdown]
# # Step 8: night migrants vs day migrants (the test written down in PLAN_step8_kerala.md)
#
# Many birds migrate **at night** (warblers, flycatchers, thrushes, orioles, shrikes...) and are known to be
# drawn towards artificial light. Others migrate **by day** (swallows, raptors, storks, wagtails, bee-eaters...),
# so lights at night shouldn't pull them in.
#
# So if light really matters, winter visitors that migrate at night should be a bigger share where it is brighter,
# and day migrants should not. Other explanations ("cities have more water", "birdwatchers visit cities in winter")
# would push both groups the same way. **The primary test** is the night share of migrants:
# night-migrant records / (night + day migrant records). It rises only if night migrants gain *relative to* day
# migrants.
#
# Everything here (groups, tests, decision rule) was fixed in the plan on 17 Nov 2026 **before** this ran.
# The same script runs on Karnataka (first look) and then, unchanged except for `REGION`, on Kerala.
#
# **Faaz's prediction:** night migrants rise with light; day migrants don't. If both rise equally, or night
# migrants show nothing, the idea is wrong.

# %%
# ---------------------------------------------------------------- SETTINGS --
REGION = "karnataka"        # "karnataka" (first look) or "kerala" (the real test)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
CELL = 0.05
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]
YEARS = list(range(2015, 2026))
MIN_VISITS_YEAR = 10        # usable square-year (all-year test): at least this many visits
MIN_VISITS_WINTER = 5       # usable square-year (winter tests)
MIN_YEARS = 3               # squares need at least this many usable years for the time model
MIN_VISITS_TOTAL = 25       # across-space model
BLOCK = 10                  # 0.5° neighbourhoods for honest error bars
WINTER_MONTHS = [11, 12, 1, 2]

# From the plan (by family, decided before seeing results). Everything else counts as neither.
NIGHT_MIGRANT_FAMILIES = {"Acrocephalidae", "Locustellidae", "Phylloscopidae", "Sylviidae", "Muscicapidae",
                          "Turdidae", "Oriolidae", "Laniidae", "Monarchidae", "Pittidae", "Cuculidae", "Rallidae",
                          "Caprimulgidae"}
DAY_MIGRANT_FAMILIES = {"Hirundinidae", "Apodidae", "Accipitridae", "Pandionidae", "Falconidae", "Ciconiidae",
                        "Gruidae", "Meropidae", "Motacillidae", "Sturnidae", "Columbidae"}

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
    _options = [Path.home() / "bigdata" / REGIONS[REGION]["folder"],
                Path.home() / "Downloads" / "bigdata" / REGIONS[REGION]["folder"]]
    BASE = next((p for p in _options if p.exists()), _options[0])
CLEAN = BASE / "clean"
print(f"Region: {REGION}. Data folder: {BASE}")

# %%
# PART 1: groups for every species (traits + monsoon/winter ratio from step 7b, run on this region's own data)
species = pd.read_csv(CLEAN / "step7b_seasonality.csv")
visitor = species["local_winter_visitor"].fillna(0) == 1
species["night_mig"] = (visitor & species["family"].isin(NIGHT_MIGRANT_FAMILIES)).astype(float)
species["day_mig"] = (visitor & species["family"].isin(DAY_MIGRANT_FAMILIES)).astype(float)
species["insect"] = species["insectivore"].fillna(0)
species["night_mig_insect"] = species["night_mig"] * species["insect"]
species["night_bird"] = species["nocturnal"].fillna(0)
species["group"] = np.select([species["night_mig"] == 1, species["day_mig"] == 1, visitor],
                             ["night migrant", "day migrant", "visitor, neither"], "not a winter visitor")
species[["species", "family", "monsoon_vs_winter", "detections", "group"]].to_csv(
    CLEAN / "step8_species_groups.csv", index=False)

GROUPS = ["night_mig", "day_mig", "insect", "night_mig_insect", "night_bird"]
vis = species[visitor]
for name in ["night migrant", "day migrant", "visitor, neither"]:
    sub = vis[vis["group"] == name]
    top = ", ".join(sub.nlargest(6, "detections")["species"])
    print(f"{name:<17} {len(sub):>3} species, {sub['detections'].sum() / vis['detections'].sum():5.1%} of "
          f"winter-visitor records; e.g. {top}")

# %%
# PART 2: bird table -> one row per species per visit (visit = observer x day x square, as before)
COLS = ["species", "decimalLatitude", "decimalLongitude", "year", "month", "day", "recordedBy"]
parts = sorted((CLEAN / "birds_parts").glob("part_*"))
rows = []
start = time.time()
for i, p in enumerate(parts):
    b = pd.read_parquet(p, columns=COLS) if p.suffix == ".parquet" else pd.read_csv(p, usecols=COLS)
    b["ilat"] = np.floor((b["decimalLatitude"].astype("float64") - LAT_MIN) / CELL + 1e-9).astype("int16")
    b["ilon"] = np.floor((b["decimalLongitude"].astype("float64") - LON_MIN) / CELL + 1e-9).astype("int16")
    b["day"] = b["day"].fillna(0).astype("int8")
    b = b[b["year"].isin(YEARS)]
    rows.append(b[["ilat", "ilon", "year", "month", "day", "recordedBy", "species"]].drop_duplicates())
    print(f"  piece {i + 1}/{len(parts)} ({(time.time() - start) / 60:.1f} min)")
det = pd.concat(rows, ignore_index=True)
det["species"] = det["species"].astype(str)
visit_key = ["ilat", "ilon", "year", "month", "day", "recordedBy"]
det = det.drop_duplicates(visit_key + ["species"])
tr = species.set_index("species")
for g in GROUPS:
    det[g] = det["species"].map(tr[g]).fillna(0).astype("float32")
print(f"Species-detections: {len(det):,}")

# %%
# PART 3: per visit, then per square-year (all visits / winter visits), then shares
v = det.groupby(visit_key).agg(n_species=("species", "size"),
                               **{f"n_{g}": (g, "sum") for g in GROUPS}).reset_index()
v["winter"] = v["month"].isin(WINTER_MONTHS)
print(f"Visits: {len(v):,} (winter: {v['winter'].sum():,})")

def add_shares(t):
    migrants = t["det_night_mig"] + t["det_day_mig"]
    t["pct_night_of_migrants"] = 100 * t["det_night_mig"] / migrants.replace(0, np.nan)     # P1
    t["pct_night_mig"] = 100 * t["det_night_mig"] / t["det_all"]                            # S1
    t["pct_day_mig"] = 100 * t["det_day_mig"] / t["det_all"]                                # S2
    t["pct_night_of_insect"] = 100 * t["det_night_mig_insect"] / t["det_insect"].replace(0, np.nan)   # S3
    t["pct_night_bird"] = 100 * t["det_night_bird"] / t["det_all"]                          # S4
    return t

def square_year(visits):
    sy = visits.groupby(["ilat", "ilon", "year"]).agg(
        visits=("n_species", "size"), det_all=("n_species", "sum"),
        **{f"det_{g}": (f"n_{g}", "sum") for g in GROUPS}).reset_index()
    return add_shares(sy)

sy_all = square_year(v)
sy_win = square_year(v[v["winter"]])

# Light and buildings per square-year (files from steps 3 and 6 for this region)
lights = pd.read_csv(sorted(CLEAN.glob("nightlights_*deg_2015-*.csv"))[-1])
lights["ilat"] = np.rint((lights["lat"] - LAT_MIN) / CELL).astype("int16")
lights["ilon"] = np.rint((lights["lon"] - LON_MIN) / CELL).astype("int16")
built = pd.read_csv(CLEAN / f"built_by_epoch_{CELL}deg.csv").pivot_table(
    index=["ilat", "ilon"], columns="epoch", values="built")

def add_light_built(sy):
    sy = sy.merge(lights[["ilat", "ilon", "year", "radiance"]], on=["ilat", "ilon", "year"], how="left")
    sy["light"] = np.log10(sy["radiance"] + 0.1)
    yrs = sy["year"].to_numpy()
    idx = sy.set_index(["ilat", "ilon"]).index
    b15, b20, b25 = (idx.map(built[e]).to_numpy(float) for e in [2015, 2020, 2025])
    sy["built"] = np.where(yrs <= 2020, b15 + (b20 - b15) * (yrs - 2015) / 5, b20 + (b25 - b20) * (yrs - 2020) / 5)
    sy["block"] = (sy["ilat"] // BLOCK).astype(str) + "_" + (sy["ilon"] // BLOCK).astype(str)
    sy["square"] = sy["ilat"].astype(str) + "_" + sy["ilon"].astype(str)
    return sy

sy_all, sy_win = add_light_built(sy_all), add_light_built(sy_win)
sy_win.to_csv(CLEAN / "step8_square_year_winter.csv", index=False)

# %%
# PART 4: models (same as steps 6-7c)
def normal_p(z):
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))

def demean_two_way(df, cols, w, a="square", b="year", tol=1e-10, max_iter=500):
    out = df[cols].astype(float).copy()
    for _ in range(max_iter):
        before = out.to_numpy().copy()
        for g in (a, b):
            means = out.mul(w, axis=0).groupby(df[g]).transform("sum").div(w.groupby(df[g]).transform("sum"), axis=0)
            out = out - means
        if np.abs(out.to_numpy() - before).max() < tol:
            break
    return out

def cluster_fit(X, Y, groups):
    """Least squares + cluster-robust errors. X, Y already weighted."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    e = Y - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in np.unique(groups):
        s = X[groups == g].T @ e[groups == g]
        meat += np.outer(s, s)
    G = len(np.unique(groups))
    return beta, np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv * G / (G - 1)))

def twfe(df, y, xs):
    d = df.dropna(subset=[y] + xs)
    w = d["visits"].astype(float)
    dm = demean_two_way(d, [y] + xs, w)
    sw = np.sqrt(w.to_numpy())
    beta, se = cluster_fit(dm[xs].to_numpy() * sw[:, None], dm[y].to_numpy() * sw, d["block"].to_numpy())
    return beta[0], se[0], len(d)

def ols_space(df, y, xs):
    d = df.dropna(subset=[y] + xs)
    xs = [x for x in xs if d[x].std() > 1e-9]
    sw = np.sqrt(d["visits"].astype(float).to_numpy())
    X = np.column_stack([np.ones(len(d)), d[xs].to_numpy(float)]) * sw[:, None]
    beta, se = cluster_fit(X, d[y].to_numpy(float) * sw, d["block"].to_numpy())
    return beta[1], se[1], len(d)          # index 1 = light (first predictor)

def panel_of(sy, min_visits):
    p = sy[(sy["visits"] >= min_visits) & sy["light"].notna()]
    return p[p.groupby("square")["year"].transform("size") >= MIN_YEARS]

habitat = pd.read_csv(CLEAN / f"habitat_{CELL}deg.csv").drop(columns=["water_source"], errors="ignore")
habitat = habitat.rename(columns={"built": "built_2020", "water": "water_frac"})

def pooled_of(sy):
    det_cols = [c for c in sy.columns if c.startswith("det_")]
    p = sy.groupby(["ilat", "ilon"]).agg(visits=("visits", "sum"), radiance=("radiance", "mean"),
                                         **{c: (c, "sum") for c in det_cols}).reset_index()
    p = add_shares(p)
    p["light"] = np.log10(p["radiance"] + 0.1)
    p = p.merge(habitat, on=["ilat", "ilon"], how="left")
    p["block"] = (p["ilat"] // BLOCK).astype(str) + "_" + (p["ilon"] // BLOCK).astype(str)
    return p[p["visits"] >= MIN_VISITS_TOTAL].dropna(subset=["light", "built_2020", "tree"])

TESTS = [("P1", "pct_night_of_migrants", "night share of migrants", "winter only"),
         ("S1", "pct_night_mig", "night migrants (% of all)", "winter only"),
         ("S2", "pct_day_mig", "day migrants (% of all)", "winter only"),
         ("S3", "pct_night_of_insect", "night migrants (% of insect-eaters)", "winter only"),
         ("S4", "pct_night_bird", "night birds (% of all, all year)", "all year")]
controls = ["built_2020", "tree", "crop", "water_frac", "elevation_m"]
data = {"all year": (sy_all, MIN_VISITS_YEAR), "winter only": (sy_win, MIN_VISITS_WINTER)}
models = {}
for season, (sy, min_v) in data.items():
    models[season] = (panel_of(sy, min_v), pooled_of(sy))
    pnl, pld = models[season]
    print(f"{season}: time model {len(pnl):,} square-years / {pnl['square'].nunique()} squares; "
          f"space model {len(pld):,} squares")

results = []
for tid, y, label, season in TESTS:
    pnl, pld = models[season]
    for analysis, fit, d in [("over time", lambda: twfe(pnl, y, ["light", "built"]), pnl),
                             ("across space", lambda: ols_space(pld, y, ["light"] + controls), pld)]:
        if d[y].notna().sum() < 30 or d[y].std() < 1e-9:     # too little data: skip, say so (as in the plan)
            print(f"  skipped {tid} {label} / {analysis}: not enough data")
            continue
        coef, se, n = fit()
        results.append({"test": tid, "group": label, "season": season, "analysis": analysis, "n": n,
                        "coef": coef, "se": se, "low95": coef - 1.96 * se, "high95": coef + 1.96 * se,
                        "p": normal_p(coef / se)})
res = pd.DataFrame(results)

# Benjamini-Hochberg over the secondary tests only (S1-S4), as the plan says
sec = res["test"] != "P1"
p_values = res.loc[sec, "p"].to_numpy()
k = len(p_values)
order = np.argsort(p_values)
q_sorted = p_values[order] * k / np.arange(1, k + 1)
q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
res["q"] = np.nan
res.loc[res.index[sec][order], "q"] = np.minimum(q_sorted, 1)
res.insert(0, "region", REGION)
res.to_csv(CLEAN / "step8_results.csv", index=False)

# %%
# PART 5: print, decide (the plan's rule for P1), plot
base_win = add_shares(sy_win[[c for c in sy_win.columns if c.startswith("det_")]].sum().to_frame().T).iloc[0]
base_all = add_shares(sy_all[[c for c in sy_all.columns if c.startswith("det_")]].sum().to_frame().T).iloc[0]
print()
print(f"Region: {REGION}. Effect = change in percentage points when a square is 10x brighter.")
print(f"{'test':<5}{'group':<38}{'analysis':<14}{'effect':>8}   95% range          p       q")
for r in res.itertuples():
    q = "" if np.isnan(r.q) else f"{r.q:.3f}" + (" *" if r.q < 0.05 else "")
    print(f"{r.test:<5}{r.group:<38}{r.analysis:<14}{r.coef:+8.2f}   [{r.low95:+.2f}, {r.high95:+.2f}]"
          f"   {r.p:.3f}   {q}")
print("q = corrected for the 8 secondary tests; * = q < 0.05")
print("Baselines: " + ", ".join(f"{tid} {(base_all if s == 'all year' else base_win)[y]:.1f}%"
                                for tid, y, _, s in TESTS))

p1 = res[res["test"] == "P1"]
if len(p1) == 0:
    verdict = "NO DATA for P1"
elif (p1["coef"] > 0).all() and (p1["low95"] > 0).any():
    verdict = "SUPPORTED: night share of migrants rises with light in every analysis, clearly in at least one"
elif (p1["coef"] <= 0).all():
    verdict = "WRONG: night share of migrants does not rise with light"
else:
    verdict = "INCONCLUSIVE: mixed or too uncertain"
print()
print(f"Plan's decision rule for P1 ({REGION}): {verdict}")
if REGION == "karnataka":
    print("(Karnataka is the first look, not independent evidence. Kerala is the real test.)")

labels = [t[2] for t in TESTS][::-1]
colors = {"night share of migrants": "#6a3d9a", "night migrants (% of all)": "#1f4e9c",
          "day migrants (% of all)": "#e08a1e", "night migrants (% of insect-eaters)": "#2a9d8f",
          "night birds (% of all, all year)": "#555555"}
fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
for ax, analysis in zip(axes, ["over time", "across space"]):
    for r in res[res["analysis"] == analysis].itertuples():
        ypos = labels.index(r.group)
        ax.errorbar(r.coef, ypos, xerr=[[r.coef - r.low95], [r.high95 - r.coef]], fmt="o",
                    color=colors[r.group], ecolor=colors[r.group], capsize=3, ms=8 if r.test == "P1" else 6)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("change in % share when a square is 10x brighter")
    ax.set_title(f"{REGION}: {analysis}")
fig.suptitle(f"P1: {verdict}", fontsize=10)
fig.tight_layout()
fig.savefig(CLEAN / "step8_night_day_migrants.png", dpi=130)
print(f"Saved step8_results.csv, step8_species_groups.csv, step8_square_year_winter.csv, "
      f"step8_night_day_migrants.png in {CLEAN}")
plt.show()
