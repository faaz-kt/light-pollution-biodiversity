# %% [markdown]
# # Step 7: sharper trait groups. Is the "migrants" result about light, or about city lakes?
#
# Step 6 found two leads: **night birds** are a smaller share of records where it's brighter, and
# **migrants** a larger share. Two things to fix and test:
#
# 1. **Better name matching.** 38 species (6.4% of detections, e.g. Spotted Dove, Cattle Egret, Shikra)
#    didn't match AVONET because their names changed between taxonomies (*Spilopelia* vs *Streptopelia*,
#    *Tachyspiza* vs *Accipiter*...). Now we try all three AVONET taxonomies (eBird, BirdLife, BirdTree) and a
#    hand-made synonym table, and print anything still unmatched.
# 2. **Split migrants into waterbirds and landbirds**, fairly:
#    - **waterbird share** = the lake check: if brighter places gain waterbirds overall, lakes and tanks in
#      growing towns could explain step 6, not light;
#    - **migrants among landbirds** and **migrants among waterbirds** compare migrants only with similar birds,
#      so one group growing can't push the other's share down (shares always add up to 100%, which can fake
#      effects: found while testing this step on synthetic data).
#    A rise in migrants *among landbirds* fits the known effect of lights **attracting night-migrating birds**.
#    Plus a **winter-only** version (Nov-Feb visits), so changes in *when* people birdwatch can't fake it.
#
# Many tests at once = more chance of a fluke, so p-values are also corrected (Benjamini-Hochberg "q").
#
# **Before running, predict:** will migrants rise among landbirds, among waterbirds, or both?

# %%
# ---------------------------------------------------------------- SETTINGS --
CELL = 0.05
REGION = "karnataka"        # "karnataka" (main study) or "kerala" (replication, see PLAN_step8_kerala.md)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]   # box around the state
YEARS = list(range(2015, 2026))
MIN_VISITS_YEAR = 10        # usable square-year: at least this many visits
MIN_VISITS_WINTER = 5       # ... for the winter-only test (fewer visits happen in 4 months)
MIN_YEARS = 3               # squares need at least this many usable years for the time model
MIN_VISITS_TOTAL = 25       # across-space model, as in steps 4-6
BLOCK = 10                  # 0.5° neighbourhoods for honest error bars
WINTER_MONTHS = [11, 12, 1, 2]
AVONET_URL = "https://ndownloader.figshare.com/files/34480856"

NOCTURNAL_FAMILIES = {"Strigidae", "Tytonidae", "Caprimulgidae", "Podargidae", "Burhinidae"}
NOCTURNAL_GENERA = {"Nycticorax", "Gorsachius"}
WATER_HABITATS = {"Wetland", "Riverine", "Coastal", "Marine"}

# Names in GBIF (Catalogue of Life 2026) -> older names that AVONET (2021) may use. Tried in order, in all
# three AVONET sheets. Built by hand from the step 6 unmatched list (check any you're unsure of!).
SYNONYMS = {
    "Acritillas indica": ["Iole indica"],
    "Ardea coromanda": ["Bubulcus coromandus", "Bubulcus ibis"],
    "Ardea ibis": ["Bubulcus ibis"],
    "Botaurus cinnamomeus": ["Ixobrychus cinnamomeus"],
    "Botaurus flavicollis": ["Ixobrychus flavicollis", "Dupetor flavicollis"],
    "Botaurus sinensis": ["Ixobrychus sinensis"],
    "Butorides atricapilla": ["Butorides striata", "Butorides striatus"],
    "Chaetornis striata": ["Schoenicola striatus", "Schoenicola striata"],
    "Coracina melanoptera": ["Lalage melanoptera"],
    "Coracina melaschistos": ["Lalage melaschistos"],
    "Corvus culminatus": ["Corvus macrorhynchos"],
    "Ducula cuprea": ["Ducula badia"],
    "Grus virgo": ["Anthropoides virgo"],
    "Icthyophaga humilis": ["Ichthyophaga humilis", "Haliaeetus humilis"],
    "Icthyophaga ichthyaetus": ["Ichthyophaga ichthyaetus", "Haliaeetus ichthyaetus"],
    "Icthyophaga leucogaster": ["Haliaeetus leucogaster"],
    "Iduna aedon": ["Arundinax aedon", "Acrocephalus aedon"],
    "Ketupa nipalensis": ["Bubo nipalensis"],
    "Ketupa zeylonensis": ["Bubo zeylonensis"],
    "Locustella certhiola": ["Helopsaltes certhiola"],
    "Lonchura oryzivora": ["Padda oryzivora"],
    "Lophospiza trivirgata": ["Accipiter trivirgatus"],
    "Luscinia brunnea": ["Larvivora brunnea"],
    "Luscinia calliope": ["Calliope calliope"],
    "Luscinia pectoralis": ["Calliope pectoralis"],
    "Monticola cinclorhynchus": ["Monticola cinclorhyncha"],
    "Muscicapa latirostris": ["Muscicapa dauurica"],
    "Muscicapa ruficauda": ["Ficedula ruficauda"],
    "Myiomela major": ["Sholicola major", "Myomela major", "Brachypteryx major"],
    "Plocealauda affinis": ["Mirafra affinis"],
    "Plocealauda erythroptera": ["Mirafra erythroptera"],
    "Saxicoloides fulicatus": ["Copsychus fulicatus"],
    "Spilopelia chinensis": ["Streptopelia chinensis"],
    "Spilopelia senegalensis": ["Streptopelia senegalensis"],
    "Tachymarptis melba": ["Apus melba"],
    "Tachyspiza badia": ["Accipiter badius"],
    "Tachyspiza brevipes": ["Accipiter brevipes"],
    "Tachyspiza virgata": ["Accipiter virgatus"],
    "Tyto javanica": ["Tyto alba"],
}

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
    _options = [Path.home() / "bigdata" / REGIONS[REGION]["folder"],
                Path.home() / "Downloads" / "bigdata" / REGIONS[REGION]["folder"]]
    BASE = next((p for p in _options if p.exists()), _options[0])
CLEAN = BASE / "clean"
TRAITS_DIR = BASE / "traits"
TRAITS_DIR.mkdir(parents=True, exist_ok=True)
print(f"Data folder: {BASE}")

# %%
# PART 1: all three AVONET sheets in one small table (cached as CSV after the first run).
TRAIT_COLS = ["Trophic.Niche", "Migration", "Habitat", "Primary.Lifestyle"]
all_csv = TRAITS_DIR / "avonet_all_sheets.csv"
if not all_csv.exists():
    xlsx = TRAITS_DIR / "AVONET_Supplementary_dataset_1.xlsx"
    if not xlsx.exists():
        import requests
        print("Downloading AVONET (21 MB) ...")
        r = requests.get(AVONET_URL, timeout=300)
        r.raise_for_status()
        xlsx.write_bytes(r.content)
    frames = []
    for sheet in pd.ExcelFile(xlsx).sheet_names:
        low = sheet.lower()
        tax = "eBird" if "ebird" in low else "BirdLife" if "birdlife" in low else "BirdTree" if "birdtree" in low else None
        if tax is None:
            continue
        s = pd.read_excel(xlsx, sheet_name=sheet)
        name_col = next(c for c in s.columns if c.lower().startswith("species"))
        f = s[[name_col] + [c for c in TRAIT_COLS if c in s.columns]].rename(columns={name_col: "avonet_name"})
        f["taxonomy"] = tax
        frames.append(f)
        print(f"  sheet {sheet}: {len(f):,} species")
    pd.concat(frames, ignore_index=True).to_csv(all_csv, index=False)
av = pd.read_csv(all_csv)
av["key"] = av["avonet_name"].str.strip().str.lower()
# One lookup per taxonomy, tried in this order
lookup = {t: av[av["taxonomy"] == t].drop_duplicates("key").set_index("key") for t in ["eBird", "BirdLife", "BirdTree"]}

def find_traits(name):
    """Try the name itself, then its synonyms, in each AVONET taxonomy. Returns (row, how) or (None, None)."""
    for i, candidate in enumerate([name] + SYNONYMS.get(name, [])):
        k = candidate.strip().lower()
        for tax, table in lookup.items():
            if k in table.index:
                return table.loc[k], f"{'exact' if i == 0 else 'synonym'} ({tax}: {candidate})"
    return None, None

# %%
# PART 2: bird table -> one row per species per visit (as in step 6).
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
    rows.append(b[keep].drop_duplicates())
    print(f"  piece {i + 1}/{len(parts)} ({(time.time() - start) / 60:.1f} min)")
det = pd.concat(rows, ignore_index=True).drop_duplicates(
    subset=["ilat", "ilon", "year", "month", "day", "recordedBy", "species"])
for c in ["recordedBy", "species", "family"]:
    det[c] = det[c].astype("category")
print(f"Species-detections: {len(det):,}")

# %%
# PART 3: traits for every species, with a record of HOW each was matched.
species = pd.DataFrame({"species": det["species"].cat.categories})
fam = det.drop_duplicates("species").set_index("species")["family"].astype(str)
species["family"] = species["species"].map(fam)
species["genus"] = species["species"].str.split().str[0]
found = [find_traits(s) for s in species["species"]]
species["matched_how"] = [how for _, how in found]
for col in TRAIT_COLS:
    species[col] = [row[col] if row is not None and col in row.index else np.nan for row, _ in found]
species["matched"] = species["matched_how"].notna()

m = species["matched"]
species["nocturnal"] = (species["family"].isin(NOCTURNAL_FAMILIES) | species["genus"].isin(NOCTURNAL_GENERA)).astype(float)
species["water"] = np.where(m, (species["Habitat"].isin(WATER_HABITATS) |
                                (species["Primary.Lifestyle"] == "Aquatic")).astype(float), np.nan)
species["insectivore"] = np.where(m, (species["Trophic.Niche"] == "Invertivore").astype(float), np.nan)
species["migrant"] = np.where(m, (species["Migration"] == 3).astype(float), np.nan)
species["resident"] = np.where(m, (species["Migration"] == 1).astype(float), np.nan)
species["land"] = 1 - species["water"]
species["migrant_water"] = species["migrant"] * species["water"]
species["migrant_land"] = species["migrant"] * species["land"]

counts = det["species"].value_counts()
species["detections"] = species["species"].map(counts).fillna(0).astype(int)
share = species.loc[m, "detections"].sum() / species["detections"].sum()
print(f"Matched to AVONET: {m.sum()} of {len(species)} species = {share:.2%} of detections "
      f"(step 6: 538 species, 93.6%)")
print(f"  by synonym: {species['matched_how'].str.startswith('synonym', na=False).sum()} species")
left = species[~m].sort_values("detections", ascending=False)
print(f"Still unmatched ({len(left)}):", ", ".join(f"{s} ({d:,})" for s, d in zip(left["species"], left["detections"])) or "none")
for g in ["water", "migrant_water", "migrant_land"]:
    top = species[species[g] == 1].nlargest(4, "detections")["species"]
    print(f"  {g:<15} {int(species[g].sum()):>3} species, e.g. {', '.join(top)}")
species.to_csv(CLEAN / "step7_species_traits.csv", index=False)

# %%
# PART 4: per visit, then per square-year: all visits, and winter visits only.
GROUPS = ["nocturnal", "insectivore", "migrant", "water", "land", "migrant_water", "migrant_land"]
tr = species.set_index("species")
for g in GROUPS:
    det[g] = det["species"].map(tr[g]).astype("float32")
det["has_avonet"] = det["species"].map(tr["matched"]).astype(bool)

visit_key = ["ilat", "ilon", "year", "month", "day", "recordedBy"]
v = det.groupby(visit_key, observed=True).agg(
    n_species=("species", "size"), n_matched=("has_avonet", "sum"),
    **{f"n_{g}": (g, "sum") for g in GROUPS}).reset_index()
v["winter"] = v["month"].isin(WINTER_MONTHS)
print(f"Visits: {len(v):,} (winter: {v['winter'].sum():,})")

def add_shares(t):
    """Shares in percent. Each group is compared within a fair 'whole', so groups can't push each other around:
    night birds of all detections; insect-eaters, migrants, waterbirds of AVONET-matched detections;
    migrants AMONG LANDBIRDS of landbird detections; migrants AMONG WATERBIRDS of waterbird detections."""
    t["pct_nocturnal"] = 100 * t["det_nocturnal"] / t["det_all"]
    for g in ["insectivore", "migrant", "water"]:
        t[f"pct_{g}"] = 100 * t[f"det_{g}"] / t["det_matched"]
    t["pct_migrant_in_land"] = 100 * t["det_migrant_land"] / t["det_land"].replace(0, np.nan)
    t["pct_migrant_in_water"] = 100 * t["det_migrant_water"] / t["det_water"].replace(0, np.nan)
    return t

def square_year(visits):
    sy = visits.groupby(["ilat", "ilon", "year"]).agg(
        visits=("n_species", "size"), det_all=("n_species", "sum"), det_matched=("n_matched", "sum"),
        **{f"det_{g}": (f"n_{g}", "sum") for g in GROUPS}).reset_index()
    return add_shares(sy)

sy_all = square_year(v)
sy_win = square_year(v[v["winter"]])

# %%
# PART 5: light and buildings per square-year (built_by_epoch file from step 6; no Earth Engine needed).
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
sy_all.to_csv(CLEAN / "step7_square_year.csv", index=False)

# %%
# PART 6: models (same as step 6) + Benjamini-Hochberg correction for many tests.
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

LABELS = {"pct_nocturnal": "night birds", "pct_insectivore": "insect-eaters", "pct_migrant": "migrants (all)",
          "pct_water": "waterbirds (lake check)", "pct_migrant_in_land": "migrants among landbirds",
          "pct_migrant_in_water": "migrants among waterbirds"}
controls = ["built_2020", "tree", "crop", "water_frac", "elevation_m"]
results = []
for season, sy, min_v in [("all year", sy_all, MIN_VISITS_YEAR), ("winter only", sy_win, MIN_VISITS_WINTER)]:
    pnl, pld = panel_of(sy, min_v), pooled_of(sy)
    print(f"{season}: time model {len(pnl):,} square-years / {pnl['square'].nunique()} squares; "
          f"space model {len(pld):,} squares")
    responses = LABELS if season == "all year" else {k: LABELS[k] for k in
                                                       ["pct_migrant", "pct_water", "pct_migrant_in_land", "pct_migrant_in_water"]}
    for y, label in responses.items():
        for analysis, fit, data in [("over time", lambda: twfe(pnl, y, ["light", "built"]), pnl),
                                    ("across space", lambda: ols_space(pld, y, ["light"] + controls), pld)]:
            if data[y].notna().sum() < 30:            # too little data for this test: skip it, say so
                print(f"  skipped {label} / {season} / {analysis}: not enough data")
                continue
            coef, se, n = fit()
            results.append({"season": season, "analysis": analysis, "group": label, "n": n, "coef": coef, "se": se,
                            "low95": coef - 1.96 * se, "high95": coef + 1.96 * se, "p": normal_p(coef / se)})

res = pd.DataFrame(results)
# Benjamini-Hochberg: sort the p-values; q = p x (number of tests) / (its rank), then make q never decrease.
p_values = res["p"].to_numpy()
k = len(p_values)
order = np.argsort(p_values)
q_sorted = p_values[order] * k / np.arange(1, k + 1)
q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
res["q"] = 0.0
res.loc[res.index[order], "q"] = np.minimum(q_sorted, 1)
res.to_csv(CLEAN / "step7_results.csv", index=False)

tot = sy_all[[c for c in sy_all.columns if c.startswith("det_")]].sum()
baseline = add_shares(tot.to_frame().T).iloc[0]
baseline = {lab: baseline[y] for y, lab in LABELS.items()}
print()
print(f"{k} tests. Effect = change in the group's % share when a square is 10x brighter.")
print(f"{'group':<32}{'season':<13}{'analysis':<14}{'effect':>8}   95% range         p       q")
for r in res.itertuples():
    star = " *" if r.q < 0.05 else ""
    print(f"{r.group:<32}{r.season:<13}{r.analysis:<14}{r.coef:+8.2f}   [{r.low95:+.2f}, {r.high95:+.2f}]"
          f"   {r.p:.3f}   {r.q:.3f}{star}")
print()
print("* = still convincing after correcting for the number of tests (q < 0.05)")
print("Baseline shares (% of detections):", ", ".join(f"{k} {v:.1f}" for k, v in baseline.items()))

# %%
# PART 7: plot. Rows = groups; left = over time, right = across space; filled = all year, open = winter only.
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
order_groups = list(LABELS.values())[::-1]
colors = {"night birds": "#5b3f8c", "insect-eaters": "#7a9cc6", "migrants (all)": "#c4652f",
          "waterbirds (lake check)": "#5a8f5a", "migrants among landbirds": "#d99a2b",
          "migrants among waterbirds": "#2f7fc4"}
for ax, analysis in zip(axes, ["over time", "across space"]):
    for season, offset, filled in [("all year", 0.12, True), ("winter only", -0.12, False)]:
        sub = res[(res["analysis"] == analysis) & (res["season"] == season)]
        for r in sub.itertuples():
            ypos = order_groups.index(r.group) + offset
            c = colors[r.group]
            ax.errorbar(r.coef, ypos, xerr=[[r.coef - r.low95], [r.high95 - r.coef]], fmt="o", color=c,
                        mfc=c if filled else "white", ecolor=c, capsize=3)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(order_groups)), order_groups)
    ax.set_xlabel("change in % share when a square is 10x brighter")
    ax.set_title(f"{analysis} (filled = all year, open = winter only)")
fig.tight_layout()
fig.savefig(CLEAN / "step7_traits_refined.png", dpi=130)
print(f"Saved step7_results.csv, step7_species_traits.csv, step7_square_year.csv, step7_traits_refined.png in {CLEAN}")
plt.show()

# %% [markdown]
# **How to read this:**
# - **Waterbirds (lake check):** if waterbirds become a bigger share where/when it's brighter, wetlands in
#   growing towns could explain the step 6 migrant result.
# - **Migrants among landbirds / among waterbirds:** each compares migrants only with birds of the same kind,
#   so more lakes can't fake it. A rise *among landbirds* points towards light itself (night-migrating birds
#   are known to be drawn to lights).
# - **Winter only** (open dots) removes changes in the season people birdwatch.
# - **q** is the p-value corrected for running many tests; trust q < 0.05 much more than p < 0.05.
# - Still records-based: shares describe what birdwatchers *record*, not true numbers of birds.

# %% [markdown]
# **Result (run 17 Nov 2026):**
# - **Name matching fixed:** 576 of 576 species now have traits (step 6: 538), 18 of them through the synonym
#   table (e.g. Cattle Egret, Shikra, Jerdon's Bushlark) and 9 through the BirdTree sheet.
# - **20 tests; 3 survive the correction (q < 0.05).** Effects in percentage points per 10x brighter:
#   - migrants among waterbirds, over time: **+3.9** (95% range +1.8 to +6.0), q = 0.007; winter only +5.1
#     (+1.5 to +8.6), q = 0.044. Baseline: 16.1% of waterbird records are migrants.
#   - migrants among landbirds, across space: **+1.5** (+0.4 to +2.6), q = 0.044. Baseline 13.5%.
# - **Lake check:** waterbirds as a share of all records show no clear change with light (over time +0.7,
#   -7.1 to +8.4; across space +1.5, -2.7 to +5.7). Wide ranges, but no sign that "more lakes" explains it.
# - **Night birds:** same as step 6 (-0.41 over time, -0.48 across space; baseline 1.1%), but with 20 tests
#   they no longer pass the correction (q = 0.18 and 0.06). Still a lead, not a finding.
# - **Big caveat, found in step 7b:** about half of AVONET's "migrant" records in Karnataka come from species
#   that live here all year (Black Kite, Shikra, Little Swift...). The migrant results need redoing with a
#   local, data-based migrant label before they can be interpreted (step 7c).
