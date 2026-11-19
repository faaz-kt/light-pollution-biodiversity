# %% [markdown]
# # Step 7c: migrants again, with a label that fits Karnataka
#
# Step 7b showed that AVONET's "migrant" label is worldwide: half of the "migrant" records in Karnataka come from
# species that live here all year (Black Kite, Shikra, Little Swift...). So steps 6-7 mixed two kinds of bird.
#
# Here the groups come from **our own records** (step 7b: monsoon reporting rate / winter reporting rate):
# - **winter visitors** = recorded in the monsoon less than 1/5 as often as in winter (221 species). They are
#   only here Nov-Feb, so they are tested on **winter visits only**, as a share of birds of the same kind:
#   *winter visitors among landbirds* and *winter visitors among waterbirds*.
# - **year-round "migrants"** = species AVONET calls migrants but which we record in the monsoon at least half as
#   often as in winter (22 species), as a share of all records, all year.
# - **Black Kite** on its own: the biggest of them (162,000 records), a famous city scavenger.
#
# The plot also shows step 7's AVONET-label winter results in grey, so you can see what changed.
#
# **Before running, predict:** with the city-loving residents taken out, does "migrants rise with light" get
# stronger, disappear, or flip?

# %%
# ---------------------------------------------------------------- SETTINGS --
CELL = 0.05
LAT_MIN, LAT_MAX = 11.5, 18.5
LON_MIN, LON_MAX = 74.0, 78.75
YEARS = list(range(2015, 2026))
MIN_VISITS_YEAR = 10        # usable square-year (all-year tests): at least this many visits
MIN_VISITS_WINTER = 5       # usable square-year (winter tests)
MIN_YEARS = 3               # squares need at least this many usable years for the time model
MIN_VISITS_TOTAL = 25       # across-space model
BLOCK = 10                  # 0.5° neighbourhoods for honest error bars
WINTER_MONTHS = [11, 12, 1, 2]
RESIDENT_MIN_RATIO = 0.5    # "here all year" = monsoon reporting rate at least half the winter rate (as step 7b)
KITE = "Milvus migrans"

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
    BASE = Path("/content/drive/MyDrive/bigdata/lpb")
else:
    _options = [Path.home() / "bigdata" / "lpb", Path.home() / "Downloads" / "bigdata" / "lpb"]
    BASE = next((p for p in _options if p.exists()), _options[0])
CLEAN = BASE / "clean"
print(f"Data folder: {BASE}")

# %%
# PART 1: species groups from step 7b (traits + monsoon/winter ratio for every species)
species = pd.read_csv(CLEAN / "step7b_seasonality.csv")
species["water"] = species["water"].fillna(0)
species["land"] = 1 - species["water"]
species["visitor"] = species["local_winter_visitor"].fillna(0)
species["visitor_land"] = species["visitor"] * species["land"]
species["visitor_water"] = species["visitor"] * species["water"]
species["yearround_migrant"] = ((species["migrant"] == 1) &
                                (species["monsoon_vs_winter"] >= RESIDENT_MIN_RATIO)).astype(float)
species["black_kite"] = (species["species"] == KITE).astype(float)

GROUPS = ["land", "water", "visitor_land", "visitor_water", "yearround_migrant", "black_kite"]
total = species["detections"].sum()
for g in GROUPS[2:]:
    sub = species[species[g] == 1]
    top = ", ".join(sub.nlargest(5, "detections")["species"])
    print(f"{g:<18} {len(sub):>3} species, {sub['detections'].sum() / total:5.1%} of records; e.g. {top}")

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
# PART 3: per visit, then per square-year (all visits / winter visits), then shares within fair "wholes"
v = det.groupby(visit_key).agg(n_species=("species", "size"),
                               **{f"n_{g}": (g, "sum") for g in GROUPS}).reset_index()
v["winter"] = v["month"].isin(WINTER_MONTHS)
print(f"Visits: {len(v):,} (winter: {v['winter'].sum():,})")

def add_shares(t):
    t["pct_visitor_in_land"] = 100 * t["det_visitor_land"] / t["det_land"].replace(0, np.nan)
    t["pct_visitor_in_water"] = 100 * t["det_visitor_water"] / t["det_water"].replace(0, np.nan)
    t["pct_yearround_migrant"] = 100 * t["det_yearround_migrant"] / t["det_all"]
    t["pct_black_kite"] = 100 * t["det_black_kite"] / t["det_all"]
    return t

def square_year(visits):
    sy = visits.groupby(["ilat", "ilon", "year"]).agg(
        visits=("n_species", "size"), det_all=("n_species", "sum"),
        **{f"det_{g}": (f"n_{g}", "sum") for g in GROUPS}).reset_index()
    return add_shares(sy)

sy_all = square_year(v)
sy_win = square_year(v[v["winter"]])

# Light and buildings per square-year (files from steps 3 and 6; no Earth Engine needed)
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
sy_win.to_csv(CLEAN / "step7c_square_year_winter.csv", index=False)

# %%
# PART 4: models (same as steps 6-7) + Benjamini-Hochberg correction
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

# Which group is tested on which visits: winter visitors in winter only; year-round birds all year
TESTS = [("pct_visitor_in_land", "winter visitors among landbirds", "winter only"),
         ("pct_visitor_in_water", "winter visitors among waterbirds", "winter only"),
         ("pct_yearround_migrant", "year-round 'migrants' (all records)", "all year"),
         ("pct_black_kite", "Black Kite (all records)", "all year")]
controls = ["built_2020", "tree", "crop", "water_frac", "elevation_m"]
data = {"all year": (sy_all, MIN_VISITS_YEAR), "winter only": (sy_win, MIN_VISITS_WINTER)}
models = {}
for season, (sy, min_v) in data.items():
    models[season] = (panel_of(sy, min_v), pooled_of(sy))
    pnl, pld = models[season]
    print(f"{season}: time model {len(pnl):,} square-years / {pnl['square'].nunique()} squares; "
          f"space model {len(pld):,} squares")

results = []
for y, label, season in TESTS:
    pnl, pld = models[season]
    for analysis, fit, d in [("over time", lambda: twfe(pnl, y, ["light", "built"]), pnl),
                             ("across space", lambda: ols_space(pld, y, ["light"] + controls), pld)]:
        if d[y].notna().sum() < 30 or d[y].std() < 1e-9:     # too little data, or group absent: skip, say so
            print(f"  skipped {label} / {analysis}: not enough data")
            continue
        coef, se, n = fit()
        results.append({"season": season, "analysis": analysis, "group": label, "n": n, "coef": coef, "se": se,
                        "low95": coef - 1.96 * se, "high95": coef + 1.96 * se, "p": normal_p(coef / se)})

res = pd.DataFrame(results)
p_values = res["p"].to_numpy()
k = len(p_values)
order = np.argsort(p_values)
q_sorted = p_values[order] * k / np.arange(1, k + 1)
q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
res["q"] = 0.0
res.loc[res.index[order], "q"] = np.minimum(q_sorted, 1)
res.to_csv(CLEAN / "step7c_results.csv", index=False)

base_all = add_shares(sy_all[[c for c in sy_all.columns if c.startswith("det_")]].sum().to_frame().T).iloc[0]
base_win = add_shares(sy_win[[c for c in sy_win.columns if c.startswith("det_")]].sum().to_frame().T).iloc[0]
print()
print(f"{k} tests. Effect = change in the group's % share when a square is 10x brighter.")
print(f"{'group':<38}{'visits':<13}{'analysis':<14}{'effect':>8}   95% range         p       q")
for r in res.itertuples():
    star = " *" if r.q < 0.05 else ""
    print(f"{r.group:<38}{r.season:<13}{r.analysis:<14}{r.coef:+8.2f}   [{r.low95:+.2f}, {r.high95:+.2f}]"
          f"   {r.p:.3f}   {r.q:.3f}{star}")
print()
print("* = still convincing after correcting for the number of tests (q < 0.05)")
print("Baseline shares: " + ", ".join(f"{label} {(base_win if season == 'winter only' else base_all)[y]:.1f}%"
                                      for y, label, season in TESTS))

# %%
# PART 5: plot. Left = over time, right = across space. Grey = step 7 (AVONET label, winter only) for comparison.
old = {}
old_file = CLEAN / "step7_results.csv"
if old_file.exists():
    o = pd.read_csv(old_file)
    o = o[o["season"] == "winter only"]
    rename = {"migrants among landbirds": "winter visitors among landbirds",
              "migrants among waterbirds": "winter visitors among waterbirds"}
    for r in o[o["group"].isin(rename)].itertuples():
        old[(rename[r.group], r.analysis)] = r
labels = [t[1] for t in TESTS][::-1]
colors = {"winter visitors among landbirds": "#d99a2b", "winter visitors among waterbirds": "#2f7fc4",
          "year-round 'migrants' (all records)": "#8c564b", "Black Kite (all records)": "#444444"}
fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
for ax, analysis in zip(axes, ["over time", "across space"]):
    for r in res[res["analysis"] == analysis].itertuples():
        ypos = labels.index(r.group)
        c = colors[r.group]
        ax.errorbar(r.coef, ypos + 0.1, xerr=[[r.coef - r.low95], [r.high95 - r.coef]], fmt="o", color=c,
                    ecolor=c, capsize=3, label="new: local label" if ypos == len(labels) - 1 else None)
        o = old.get((r.group, analysis))
        if o is not None:
            ax.errorbar(o.coef, ypos - 0.15, xerr=[[o.coef - o.low95], [o.high95 - o.coef]], fmt="s",
                        color="#aaaaaa", ecolor="#aaaaaa", capsize=3, mfc="white",
                        label="step 7: AVONET label" if ypos == len(labels) - 1 else None)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("change in % share when a square is 10x brighter")
    ax.set_title(analysis)
axes[0].legend(loc="lower right", fontsize=8)
fig.tight_layout()
fig.savefig(CLEAN / "step7c_local_migrants.png", dpi=130)
print(f"Saved step7c_results.csv, step7c_square_year_winter.csv, step7c_local_migrants.png in {CLEAN}")
plt.show()

# %% [markdown]
# **How to read this:**
# - **Winter visitors among landbirds / waterbirds** (coloured dots) use only birds that really are migrants
#   here. Grey squares are step 7's version with AVONET's label: if the coloured dot moves to zero, step 7's
#   result came from the year-round residents; if it stays, real migrants are involved.
# - **Year-round "migrants"** and **Black Kite**: if these rise with light, the old result was partly about
#   city-adapted resident birds.
# - Still records-based: shares describe what birdwatchers *record*, not true numbers of birds.

# %% [markdown]
# **Result (run 17 Nov 2026), 8 tests:**
# - **Winter visitors among waterbirds:** +1.9 over time (95% range -4.1 to +7.9) and +2.1 across space
#   (-2.3 to +6.4): no clear effect. Step 7's strongest result (AVONET "migrants among waterbirds" rising over
#   time, +5.1 in winter) mostly came from **resident herons** AVONET calls migrants (Purple Heron,
#   Black-crowned Night Heron), not from real migrants.
# - **Winter visitors among landbirds** (Barn Swallow, Indian Golden Oriole, Ashy Drongo, Brown Shrike, leaf
#   warblers...; baseline 11.9% of winter landbird records): +4.1 over time (-0.0 to +8.2) and +1.4 across space
#   (+0.04 to +2.7). Same direction in both analyses and a bit larger than with AVONET's label, each p about
#   0.05, but **not convincing after correction** (q = 0.14). A lead, consistent with lights attracting
#   night-migrating birds, not a finding.
# - **Year-round "migrants"** (22 species, 6.8% of records): a bigger share in brighter places (+1.0, +0.5 to
#   +1.6, q = 0.003, the only test that survives), but not clearly over time (+1.0, -0.4 to +2.3). A
#   pattern across space only can come from city habitat or birdwatcher habits, not necessarily light.
# - **Black Kite alone:** no clear effect (+0.3 both ways), so the year-round result is not just the kite.
#
# Lesson worth reporting: a worldwide trait label (AVONET "migrant") can create or hide local effects; check
# labels against local data before testing them.
