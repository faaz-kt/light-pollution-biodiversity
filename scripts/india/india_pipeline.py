# %% [markdown]
# # India: does the link between night light and birds differ between states?
#
# This notebook does the data side of the locked plan `PLAN_india.md` (locked 18 Nov 2026, 12:47 IST):
#
# - **Part A** reads the GBIF download in pieces and stores each record as a few small whole numbers
#   (square, date, observer number, species number, state number). 50 million records then fit in memory.
# - **Part B** turns records into squares: records, visits, observers, rarefied species (step 4), species per
#   visit per year (step 6), and which state each square belongs to (the state with most of its records).
# - **Part C** gets the satellite layers from Earth Engine in tiles: night lights, the step 5 habitat layers,
#   buildings in 2015/2020/2025, population, and air pollution (NO2).
# - **Part D** fits the step 5 model (and the step 6 over-time model) in every state, measures the four factors,
#   and writes the **explore** half and the **sealed hold-out** half to separate files. Only the explore half is
#   printed or plotted.
#
# The final tests (P1, P2) are in `india_final_tests.py`, run once, after the explore half is frozen.
# Every part saves what it made, so a re-run (or a Colab disconnect) carries on where it stopped.
#
# **Order of runs (plan, "Reproduction check first"):**
# 1. `RUN = "repro_karnataka"` on the original Karnataka download: must give back -0.23 species per SD of light
#    (1,020 squares).
# 2. `RUN = "repro_kerala"` on the original Kerala download: must give back -7.40 per SD (1,054 squares).
# 3. Only if both pass: `RUN = "india"` on the India download.

# %%
# ---------------------------------------------------------------- SETTINGS --
RUN = "repro_karnataka"     # "repro_karnataka", "repro_kerala" (reproduction checks), or "india" (the real run)
REDO = set()                # parts to redo even if saved, e.g. {"B", "D"}
PROJECT = "civil-clarity-442414-b7"   # Earth Engine project

# One national grid of 0.05 degree squares. Its corners are multiples of 0.5 degrees, so the old Karnataka and
# Kerala boxes, their squares and their 0.5 degree blocks line up with it exactly.
CELL = 0.05
LAT_MIN, LAT_MAX = 6.0, 37.5
LON_MIN, LON_MAX = 68.0, 97.5
H, W = round((LAT_MAX - LAT_MIN) / CELL), round((LON_MAX - LON_MIN) / CELL)    # 630 x 590 squares

YEARS = list(range(2015, 2026))
MIN_VISITS = 25             # step 5: squares with fewer visits are too poorly sampled
RAREFY_N = 200              # step 4: species expected in 200 records
BLOCK = 10                  # 10 x 10 squares = 0.5 degree blocks for the error bars
MIN_VISITS_YEAR, MIN_YEARS = 10, 3   # step 6: over-time model
NO2_YEARS = list(range(2019, 2026))  # plan F2: Sentinel-5P NO2, 2019-2025 mean
CHUNK_ROWS = 1_000_000      # rows read at a time in part A
EE_WORKERS = 4              # Earth Engine requests sent at the same time

# Plan: which states, which half (drawn 18 Nov 2026 with seed 20261118, before any data)
MIN_SQUARES, MIN_BLOCKS = 150, 10
STATES = {1: "Andaman and Nicobar", 2: "Andhra Pradesh", 3: "Arunachal Pradesh", 4: "Assam", 5: "Bihar",
          6: "Chandigarh", 7: "Chhattisgarh", 8: "Dadra and Nagar Haveli", 9: "Daman and Diu", 10: "Goa",
          11: "Gujarat", 12: "Haryana", 13: "Himachal Pradesh", 14: "Jammu and Kashmir", 15: "Jharkhand",
          16: "Karnataka", 17: "Kerala", 18: "Lakshadweep", 19: "Madhya Pradesh", 20: "Maharashtra",
          21: "Manipur", 22: "Meghalaya", 23: "Mizoram", 24: "Nagaland", 25: "Delhi", 26: "Odisha",
          27: "Puducherry", 28: "Punjab", 29: "Rajasthan", 30: "Sikkim", 31: "Tamil Nadu", 32: "Telangana",
          33: "Tripura", 34: "Uttar Pradesh", 35: "Uttarakhand", 36: "West Bengal"}     # GADM level-1 numbers
ELIGIBLE = [1, 2, 4, 7, 10, 11, 12, 13, 16, 17, 19, 20, 25, 26, 28, 29, 31, 32, 34, 35, 36]   # >= 300,000 records
HOLDOUT = [7, 36, 25, 34, 35, 4, 31, 11, 29]
SEEN = [16, 17]             # Karnataka and Kerala: always explore, never in P1
# GBIF record counts per state on 18 Nov 2026 (Aves 2015-2025), used to check our state names in part A
GBIF_COUNTS_18NOV = {16: 7816939, 17: 5964349, 31: 5949998, 20: 5930482, 11: 2847521, 35: 2646633,
                     19: 2444557, 29: 2052812, 36: 2007660, 4: 1491171, 34: 1115512, 32: 1045138,
                     12: 898704, 2: 866174, 10: 848581, 7: 784401, 26: 672871, 25: 644154, 13: 496957,
                     1: 442417, 28: 358925}
# Other spellings of state names seen in GBIF records (eBird, iNaturalist, ...)
ALIASES = {"andaman and nicobar islands": 1, "orissa": 26, "pondicherry": 27, "uttaranchal": 35,
           "nct of delhi": 25, "national capital territory of delhi": 25, "new delhi": 25, "delhi nct": 25,
           "ladakh": 14, "jammu and kashmir and ladakh": 14,
           "dadra and nagar haveli and daman and diu": 8, "the dadra and nagar haveli and daman and diu": 8}

RUNS = {   # where each run's GBIF zip is (inside the bigdata folder), and what the old code gave
    "repro_karnataka": {"zips": ["lpb/raw/0008405-261110092616502.zip", "lpb/0008405-261110092616502.zip"],
                        "old_coef_per_sd": -0.22864611, "old_squares": 1020},
    "repro_kerala": {"zips": ["lpb_kerala/raw/*.zip"], "old_coef_per_sd": -7.404706429, "old_squares": 1054},
    "india": {"zips": ["lpb_india/raw/*.zip"]},
}

# %%
import csv
import json
import math
import os
import sys
import time
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import erf, lgamma, sqrt
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
OUT = ROOT / "lpb_india" / RUN
OUT.mkdir(parents=True, exist_ok=True)
REPRO = RUN.startswith("repro")
print(f"Run: {RUN}   output folder: {OUT}")

# Parquet (small, fast) needs pyarrow, which Colab has; without it, tables are saved as pickle files.
try:
    import pyarrow  # noqa: F401
    EXT = ".parquet"
except ImportError:
    EXT = ".pkl"


def save(df, path):
    path = Path(str(path) + EXT)
    df.to_parquet(path, index=False) if EXT == ".parquet" else df.to_pickle(path)


def load(path):
    path = Path(str(path) + EXT)
    return pd.read_parquet(path) if EXT == ".parquet" else pd.read_pickle(path)


def exists(path):
    return Path(str(path) + EXT).exists()


def state_name_key(text):
    """'Andaman & Nicobar Islands ' -> 'andaman and nicobar islands' (lower case, & -> and, single spaces)."""
    s = " ".join(str(text).lower().replace("&", " and ").replace(".", " ").split())
    for prefix in ("state of ", "union territory of "):
        s = s[len(prefix):] if s.startswith(prefix) else s
    return s


NAME_TO_CODE = {state_name_key(n): c for c, n in STATES.items()}
NAME_TO_CODE.update({state_name_key(n): c for n, c in ALIASES.items()})

# %% [markdown]
# ## Part A: GBIF zip -> compact records
#
# Same cleaning as step 2 (drop "absent" records, records without a species-level name, without coordinates or
# without year and month). Coordinates are rounded to float32 exactly as step 2 stored them, so every record
# lands in the same square as before. Each record keeps: square (ilat, ilon), year, month, day (0 = unknown),
# observer number (0 = unknown), species number, state number (0 = unknown).

# %%
REC = OUT / "records"
DONE_A = REC / "_DONE.json"
KEEP = ["species", "taxonRank", "occurrenceStatus", "decimalLatitude", "decimalLongitude",
        "year", "month", "day", "recordedBy", "stateProvince"]


def find_zips():
    found = []
    for pattern in RUNS[RUN]["zips"]:
        if "*" in pattern:
            found += sorted(ROOT.glob(pattern))
        elif (ROOT / pattern).exists():
            found.append(ROOT / pattern)
    if not found:
        raise FileNotFoundError(f"No GBIF zip for {RUN}. Looked for: {RUNS[RUN]['zips']} inside {ROOT}")
    return found[:1] if REPRO else found


if DONE_A.exists() and "A" not in REDO:
    info_a = json.loads(DONE_A.read_text())
    print(f"Part A already done: {info_a['kept']:,} records kept from {info_a['zips']}")
else:
    REC.mkdir(parents=True, exist_ok=True)
    for old in REC.glob("part_*"):
        old.unlink()
    zips = find_zips()
    species_code, observer_code, state_code = {}, {}, {}
    raw_state_counts = Counter()
    totals = Counter()
    start = time.time()
    i = 0
    for zp in zips:
        print(f"Reading {zp} ({zp.stat().st_size / 1e9:.2f} GB)")
        with zipfile.ZipFile(zp) as z:
            inner = [n for n in z.namelist() if n.endswith(".csv")][0]
            with z.open(inner) as f:
                reader = pd.read_csv(f, sep="\t", quoting=csv.QUOTE_NONE, chunksize=CHUNK_ROWS,
                                     usecols=lambda c: c in KEEP,
                                     dtype={"recordedBy": "string", "stateProvince": "string",
                                            "species": "string", "taxonRank": "string",
                                            "occurrenceStatus": "string"},
                                     on_bad_lines="skip", low_memory=False)
                for piece in reader:
                    if i == 0:
                        missing_cols = [c for c in KEEP if c not in piece.columns]
                        if missing_cols and not (REPRO and missing_cols == ["stateProvince"]):
                            raise SystemExit(f"The GBIF file has no column(s) {missing_cols}: stop and check.")
                    totals["read"] += len(piece)
                    # --- the step 2 cleaning, in the same order ---
                    absent = piece["occurrenceStatus"].eq("ABSENT").fillna(False)
                    totals["dropped: absent"] += int(absent.sum())
                    piece = piece[~absent]
                    no_species = piece["species"].isna() | ~piece["taxonRank"].isin(["SPECIES", "SUBSPECIES"]).fillna(False)
                    totals["dropped: no species name"] += int(no_species.sum())
                    piece = piece[~no_species]
                    no_place = piece["decimalLatitude"].isna() | piece["decimalLongitude"].isna()
                    totals["dropped: no coordinates"] += int(no_place.sum())
                    piece = piece[~no_place]
                    no_date = piece["year"].isna() | piece["month"].isna()
                    totals["dropped: no year/month"] += int(no_date.sum())
                    piece = piece[~no_date]
                    # --- square on the national grid (float32 first, as step 2 stored coordinates) ---
                    lat = piece["decimalLatitude"].astype("float32").astype("float64").to_numpy()
                    lon = piece["decimalLongitude"].astype("float32").astype("float64").to_numpy()
                    ilat = np.floor((lat - LAT_MIN) / CELL + 1e-9)
                    ilon = np.floor((lon - LON_MIN) / CELL + 1e-9)
                    inside = (ilat >= 0) & (ilat < H) & (ilon >= 0) & (ilon < W)
                    totals["dropped: outside the India grid"] += int((~inside).sum())
                    piece, ilat, ilon = piece[inside], ilat[inside], ilon[inside]
                    # --- numbers instead of text ---
                    for name in pd.unique(piece["species"]):
                        species_code.setdefault(name, len(species_code) + 1)
                    obs = piece["recordedBy"]
                    for name in pd.unique(obs.dropna()):
                        observer_code.setdefault(name, len(observer_code) + 1)
                    if "stateProvince" in piece.columns:
                        raw = piece["stateProvince"]
                        raw_state_counts.update(raw.fillna("(empty)").value_counts().to_dict())
                        for name in pd.unique(raw.dropna()):
                            state_code.setdefault(name, NAME_TO_CODE.get(state_name_key(name), 0))
                        st = raw.map(state_code).fillna(0).astype("int8").to_numpy()
                    else:
                        st = np.zeros(len(piece), dtype="int8")
                    part = pd.DataFrame({
                        "ilat": ilat.astype("int16"), "ilon": ilon.astype("int16"),
                        "year": piece["year"].astype("int16").to_numpy(),
                        "month": piece["month"].astype("int8").to_numpy(),
                        "day": piece["day"].fillna(0).astype("int8").to_numpy(),
                        "obs": obs.map(observer_code).fillna(0).astype("int32").to_numpy(),
                        "sp": piece["species"].map(species_code).astype("int16").to_numpy(),
                        "state": st,
                    })
                    save(part, REC / f"part_{i:03d}")
                    totals["kept"] += len(part)
                    i += 1
                    print(f"  piece {i:3d}: {totals['read']:>11,} read, {totals['kept']:>11,} kept "
                          f"({(time.time() - start) / 60:.1f} min)")
    pd.DataFrame({"sp": list(species_code.values()), "species": list(species_code.keys())}).to_csv(
        REC / "species_codes.csv", index=False)
    states_seen = pd.DataFrame([(name, n, state_code.get(name, 0)) for name, n in raw_state_counts.items()],
                               columns=["stateProvince", "records", "state"]).sort_values("records", ascending=False)
    states_seen.to_csv(REC / "stateProvince_names.csv", index=False)
    info_a = {"run": RUN, "zips": [str(z) for z in zips], **totals, "species": len(species_code),
              "observers": len(observer_code), "minutes": round((time.time() - start) / 60, 1)}
    DONE_A.write_text(json.dumps(info_a, indent=2))
    print(f"\nRead {totals['read']:,}, kept {totals['kept']:,} records; {len(species_code):,} species, "
          f"{len(observer_code):,} observers.")
    for k, v in totals.items():
        if k.startswith("dropped"):
            print(f"  {k}: {v:,}")

# Check the state names (plan: "the code checks them against GADM before the split is used").
names = pd.read_csv(REC / "stateProvince_names.csv")
unknown = names[names["state"] == 0]
print(f"\nRecords whose state name we could not place: {unknown['records'].sum():,} "
      f"({unknown['records'].sum() / max(names['records'].sum(), 1):.2%}). Most common:")
print(unknown.head(8).to_string(index=False))
if not REPRO:
    ours = names.groupby("state")["records"].sum()
    print("\nRecords per state: ours (from the state names) vs GBIF's map-based count on 18 Nov")
    bad = []
    for code in ELIGIBLE:
        ratio = ours.get(code, 0) / GBIF_COUNTS_18NOV[code]
        flag = "" if 0.9 <= ratio <= 1.1 else "   <-- CHECK"
        bad += [code] if flag else []
        print(f"  {code:2d} {STATES[code]:<22}{ours.get(code, 0):>11,} {GBIF_COUNTS_18NOV[code]:>11,}  "
              f"{ratio:6.1%}{flag}")
    print("All 21 states match within 10%." if not bad else
          f"States to check before going on: {[STATES[c] for c in bad]}")

# %% [markdown]
# ## Part B: records -> squares
#
# - Step 4 measures per square (all years together): records, visits (one observer, one square, one day;
#   records without an observer count as one observer, as in step 4), observers, species, and **rarefied
#   species** (Hurlbert: species expected in 200 records, using every record).
# - Step 6 measure per square and year: visits with a known observer and **species per visit** (each species
#   counted once per visit).
# - **State of a square** (plan): the state holding most of the square's records (ties: lower GADM number).

# %%
SQUARES, SQYEARS = OUT / "squares", OUT / "square_years"


def log_choose(a, k):
    return lgamma(a + 1) - lgamma(k + 1) - lgamma(a - k + 1)


def rarefied_species(counts, n):
    """Step 4's Hurlbert rarefaction, unchanged."""
    N = counts.sum()
    if N < n:
        return np.nan
    total = 0.0
    for Ni in counts:
        if N - Ni < n:
            total += 1.0
        else:
            total += 1.0 - np.exp(log_choose(N - Ni, n) - log_choose(N, n))
    return total


if exists(SQUARES) and exists(SQYEARS) and "B" not in REDO and "A" not in REDO:
    print("Part B already done.")
else:
    start = time.time()
    parts = sorted(REC.glob(f"part_*{EXT}"))
    cols = {c: [] for c in ["ilat", "ilon", "year", "month", "day", "obs", "sp", "state"]}
    for p in parts:
        t = pd.read_parquet(p) if EXT == ".parquet" else pd.read_pickle(p)
        for c in cols:
            cols[c].append(t[c].to_numpy())
    a = {c: np.concatenate(v) for c, v in cols.items()}
    n_rec = len(a["sp"])
    print(f"{n_rec:,} records loaded ({(time.time() - start) / 60:.1f} min)")
    assert a["year"].min() >= 2000 and a["sp"].max() < 4096 and a["obs"].max() < 2 ** 30

    sq = a["ilat"].astype("int64") * W + a["ilon"].astype("int64")           # one number per square
    daycode = ((a["year"].astype("int64") - 2000) * 13 + a["month"]) * 32 + a["day"]   # < 2**14
    visit = (sq << 44) | (daycode << 30) | a["obs"].astype("int64")          # square + date + observer

    records = np.bincount(sq, minlength=H * W)
    vk_all = np.unique(visit)                                                # step 4 visits (unknown observer = one)
    visits = np.bincount(vk_all >> 44, minlength=H * W)
    sp_pairs, sp_counts = np.unique(sq * 4096 + a["sp"], return_counts=True)  # records per species per square
    species = np.bincount(sp_pairs // 4096, minlength=H * W)
    known = a["obs"] > 0
    obs_pairs = np.unique((sq[known] << 30) | a["obs"][known].astype("int64"))
    observers = np.bincount(obs_pairs >> 30, minlength=H * W)

    # rarefied species, square by square (pairs are sorted by square, then species)
    pair_sq = sp_pairs // 4096
    cuts = np.flatnonzero(np.diff(pair_sq)) + 1
    rare = {}
    for s_idx, cnt in zip(np.split(pair_sq, cuts), np.split(sp_counts, cuts)):
        if cnt.sum() >= RAREFY_N:
            rare[int(s_idx[0])] = rarefied_species(cnt, RAREFY_N)

    # majority state
    st_known = a["state"] > 0
    st_pairs, st_counts = np.unique(sq[st_known] * 64 + a["state"][st_known], return_counts=True)
    st = pd.DataFrame({"sq": st_pairs // 64, "state": st_pairs % 64, "n": st_counts})
    st["known"] = st.groupby("sq")["n"].transform("sum")
    st = st.sort_values(["sq", "n", "state"], ascending=[True, False, True]).drop_duplicates("sq")
    st["state_share"] = st["n"] / st["known"]

    present = np.flatnonzero(records)
    squares = pd.DataFrame({"sq": present, "ilat": present // W, "ilon": present % W,
                            "records": records[present], "visits": visits[present],
                            "species": species[present], "observers": observers[present]})
    squares["species_rarefied"] = squares["sq"].map(rare)
    squares = squares.merge(st[["sq", "state", "state_share"]], on="sq", how="left")
    squares["state"] = squares["state"].fillna(0).astype("int8")
    squares["lat"] = (LAT_MIN + squares["ilat"] * CELL).round(4)    # lower-left corner, as in steps 3-5
    squares["lon"] = (LON_MIN + squares["ilon"] * CELL).round(4)
    save(squares, SQUARES)

    # step 6: one row per species per visit (known observers only), then species per visit per square-year
    vk, spk = visit[known], a["sp"][known]
    order = np.lexsort((spk, vk))
    vk, spk = vk[order], spk[order]
    first = np.ones(len(vk), dtype=bool)
    first[1:] = (vk[1:] != vk[:-1]) | (spk[1:] != spk[:-1])
    v_ids, n_species = np.unique(vk[first], return_counts=True)
    v_year = 2000 + (((v_ids >> 30) & (2 ** 14 - 1)) // 32) // 13
    per_visit = pd.DataFrame({"sq": v_ids >> 44, "year": v_year, "n_species": n_species})
    per_visit = per_visit[per_visit["year"].isin(YEARS)]
    sy = per_visit.groupby(["sq", "year"]).agg(visits=("n_species", "size"),
                                               species_per_visit=("n_species", "mean")).reset_index()
    save(sy, SQYEARS)
    del a, sq, daycode, visit, vk, spk
    print(f"Squares with records: {len(squares):,}; with >= {MIN_VISITS} visits: "
          f"{(squares['visits'] >= MIN_VISITS).sum():,}; square-years: {len(sy):,} "
          f"({(time.time() - start) / 60:.1f} min)")

squares = load(SQUARES)
assigned = squares[squares["visits"] >= MIN_VISITS]
print(f"Squares with >= {MIN_VISITS} visits whose records are all from one state: "
      f"{(assigned['state_share'] == 1).mean():.1%}; with no known state: {(assigned['state'] == 0).mean():.1%}")

# %% [markdown]
# ## Part C: Earth Engine layers, in tiles
#
# Each layer is made exactly as in steps 3, 5 and 6 (same datasets, bands and averaging), plus two new ones for
# the plan's factors: population (GHSL 2020) and NO2 (Sentinel-5P, mean of the 2019-2025 yearly means).
# A big region is cut into tiles (5 degrees; 2.5 for the 30 m water map). Every tile is saved as soon as it
# arrives; if Earth Engine says a tile is too big or too slow, it is split into four and tried again.
# Only tiles containing a square with at least 25 visits are asked for.

# %%
EE_DIR = OUT / "earth_engine"
EE_TABLE, EE_RADIANCE = OUT / "ee_squares", OUT / "ee_radiance"
VIIRS_COLLECTIONS = ["NOAA/VIIRS/DNB/ANNUAL_V21", "NOAA/VIIRS/DNB/ANNUAL_V22"]
LAYERS = {"viirs": 5.0, "built": 5.0, "tree": 5.0, "crop": 5.0, "water": 2.5, "elevation_m": 5.0,
          "built2015": 5.0, "built2025": 5.0, "pop": 5.0, **{f"no2_{y}": 5.0 for y in NO2_YEARS}}
SENTINEL = -9999.0          # "no data" marker for the new layers (population, NO2)
FAKE_EE = os.environ.get("LPB_FAKE_EE")   # used only by the smoke tests (a file defining fake_fetch)

viirs_source = {}


def ee_image(layer):
    """The Earth Engine image for one layer and its band names (same recipes as steps 3, 5, 6)."""
    import ee
    if layer == "viirs":                       # step 3
        bands = [f"y{y}" for y in sorted(viirs_source)]
        stack = ee.Image.cat([ee.ImageCollection(viirs_source[y]).filterDate(f"{y}-01-01", f"{y + 1}-01-01")
                              .first().select("average_masked").rename(f"y{y}") for y in sorted(viirs_source)])
        return stack.unmask(0), bands, 1024
    if layer in ("built", "built2015", "built2025"):   # step 5 (2020) and step 6 (2015, 2025)
        epoch = {"built": 2020, "built2015": 2015, "built2025": 2025}[layer]
        return ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{epoch}").select("built_surface").divide(10000), [layer], 65535
    if layer == "tree":                        # step 5
        vcf = ee.ImageCollection("MODIS/061/MOD44B").filterDate("2015-01-01", "2025-01-01").select("Percent_Tree_Cover")
        tree = vcf.map(lambda im: im.updateMask(im.lte(100))).mean().setDefaultProjection(vcf.first().projection())
        return tree.divide(100).unmask(0), [layer], 65535
    if layer == "crop":                        # step 5
        lc = ee.Image("MODIS/061/MCD12Q1/2020_01_01").select("LC_Type1")
        return lc.eq(12).add(lc.eq(14).multiply(0.5)), [layer], 65535
    if layer == "water":                       # step 5 (JRC, as used for Karnataka and Kerala)
        return ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("max_extent").unmask(0), [layer], 65535
    if layer == "elevation_m":                 # step 5
        return ee.Image("CGIAR/SRTM90_V4").select("elevation"), [layer], 65535
    if layer == "pop":                         # plan F1: people per 100 m pixel (GHSL 2020)
        return ee.Image("JRC/GHSL/P2023A/GHS_POP/2020").select("population_count"), [layer], 65535
    if layer.startswith("no2_"):               # plan F2: yearly mean tropospheric NO2 (mol/m2)
        y = int(layer[4:])
        coll = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2").select("tropospheric_NO2_column_number_density")
        img = coll.filterDate(f"{y}-01-01", f"{y + 1}-01-01").mean().setDefaultProjection(coll.first().projection())
        return img, [layer], 65535
    raise ValueError(layer)


def grid_for(r0, c0, h, w):
    """A computePixels grid for rows r0..r0+h-1 and columns c0..c0+w-1 of the national grid (row 0 = north)."""
    return {"dimensions": {"width": w, "height": h},
            "affineTransform": {"scaleX": CELL, "shearX": 0, "translateX": round(LON_MIN + c0 * CELL, 10),
                                "shearY": 0, "scaleY": -CELL, "translateY": round(LAT_MAX - r0 * CELL, 10)},
            "crsCode": "EPSG:4326"}


def fetch(layer, r0, c0, h, w):
    """One request: returns an array (bands, h, w)."""
    grid = grid_for(r0, c0, h, w)
    if FAKE_EE:
        return _fake.fake_fetch(layer, grid)
    import ee
    image, bands, max_px = ee_image(layer)
    if len(bands) == 1:
        image = image.rename(bands)          # name the band after the layer, as step 5's square_means() did
    gridded = image.reduceResolution(reducer=ee.Reducer.mean(), maxPixels=max_px).reproject(
        crs="EPSG:4326", crsTransform=[CELL, 0, LON_MIN, 0, -CELL, LAT_MAX])
    if layer == "pop" or layer.startswith("no2_"):
        gridded = gridded.unmask(SENTINEL)
    px = ee.data.computePixels({"expression": gridded, "fileFormat": "NUMPY_NDARRAY", "grid": grid})
    return np.stack([np.array(px[b], dtype="float64") for b in bands])


SPLIT_WORDS = ("timed out", "timeout", "deadline", "too large", "too many pixels", "memory", "limit exceeded",
               "computation", "payload")


def fetch_robust(layer, r0, c0, h, w, depth=0):
    """fetch(), with retries; a tile that is too big or too slow is split into four."""
    for attempt in range(5):
        try:
            return fetch(layer, r0, c0, h, w)
        except Exception as err:
            msg = str(err).lower()
            if any(word in msg for word in SPLIT_WORDS) and min(h, w) >= 4 and depth < 4:
                print(f"    {layer} tile ({r0},{c0}) {h}x{w} too big/slow for Earth Engine: splitting into four")
                h1, w1 = h // 2, w // 2
                out = None
                for (rr, cc, hh, ww) in [(r0, c0, h1, w1), (r0, c0 + w1, h1, w - w1),
                                         (r0 + h1, c0, h - h1, w1), (r0 + h1, c0 + w1, h - h1, w - w1)]:
                    piece = fetch_robust(layer, rr, cc, hh, ww, depth + 1)
                    if out is None:
                        out = np.full((piece.shape[0], h, w), np.nan)
                    out[:, rr - r0:rr - r0 + hh, cc - c0:cc - c0 + ww] = piece
                return out
            wait = 2 ** attempt * 5
            print(f"    {layer} tile ({r0},{c0}) failed ({str(err)[:90]}); retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"{layer} tile ({r0},{c0}) kept failing")


def layer_array(layer, needed_rows_cols):
    """The whole national array for one layer (bands, H, W); NaN where no tile was needed."""
    n = int(round(LAYERS[layer] / CELL))
    folder = EE_DIR / layer
    folder.mkdir(parents=True, exist_ok=True)
    tiles = sorted({(r // n * n, c // n * n) for r, c in needed_rows_cols})
    todo = [(r0, c0) for r0, c0 in tiles if not (folder / f"{r0}_{c0}.npy").exists()]
    if todo:
        print(f"  {layer}: {len(todo)} of {len(tiles)} tiles to fetch")

        def job(rc):
            r0, c0 = rc
            arr = fetch_robust(layer, r0, c0, min(n, H - r0), min(n, W - c0))
            np.save(folder / f"{r0}_{c0}.npy", arr)
            return rc
        with ThreadPoolExecutor(max_workers=1 if FAKE_EE else EE_WORKERS) as pool:
            for k, fut in enumerate(as_completed([pool.submit(job, rc) for rc in todo]), 1):
                fut.result()
                if k % 10 == 0 or k == len(todo):
                    print(f"    {k}/{len(todo)} tiles")
    full = None
    for r0, c0 in tiles:
        arr = np.load(folder / f"{r0}_{c0}.npy")
        if full is None:
            full = np.full((arr.shape[0], H, W), np.nan)
        full[:, r0:r0 + arr.shape[1], c0:c0 + arr.shape[2]] = arr
    return full


if exists(EE_TABLE) and exists(EE_RADIANCE) and not (REDO & {"A", "B", "C"}):
    print("Part C already done.")
else:
    if FAKE_EE:
        import importlib.util
        _spec = importlib.util.spec_from_file_location("fake_ee", FAKE_EE)
        _fake = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_fake)
        viirs_source = {y: "fake" for y in YEARS}
    else:
        import ee
        from datetime import datetime, timezone
        ee.Authenticate()
        ee.Initialize(project=PROJECT)
        for coll_id in VIIRS_COLLECTIONS:          # which years are in which collection (later one wins), as step 3
            starts = ee.ImageCollection(coll_id).aggregate_array("system:time_start").getInfo()
            for y in sorted({datetime.fromtimestamp(t / 1000, tz=timezone.utc).year for t in starts}):
                if y in YEARS:
                    viirs_source[y] = coll_id
        print(f"VIIRS years: {sorted(viirs_source)}")
    need = squares[squares["visits"] >= MIN_VISITS]
    rows = (H - 1 - need["ilat"]).to_numpy()          # array row 0 = north edge
    cols_ = need["ilon"].to_numpy()
    needed = list(zip(rows.tolist(), cols_.tolist()))
    print(f"Earth Engine values for {len(needed):,} squares")
    table = pd.DataFrame({"sq": need["sq"].to_numpy()})
    radiance = None
    for layer in LAYERS:
        arr = layer_array(layer, needed)
        vals = arr[:, rows, cols_]
        if layer == "viirs":
            radiance = vals                                      # (years, squares)
            table["radiance_mean"] = vals.mean(axis=0)            # mean over the available years, as step 4
        else:
            v = vals[0]
            if layer == "pop" or layer.startswith("no2_"):
                v = np.where(v <= SENTINEL + 1, np.nan, v)
            table[layer] = v
    no2_cols = [f"no2_{y}" for y in NO2_YEARS]
    enough = table[no2_cols].notna().sum(axis=1) >= 5             # at least 5 of the 7 years
    table["no2"] = table[no2_cols].mean(axis=1).where(enough)
    save(table, EE_TABLE)
    years_ = sorted(viirs_source)
    rad = pd.DataFrame({"sq": np.repeat(table["sq"].to_numpy(), len(years_)),
                        "year": np.tile(years_, len(table)),
                        "radiance": radiance.T.reshape(-1)})
    rad["version"] = rad["year"].map({y: viirs_source[y].split("_")[-1].lower() for y in years_})
    save(rad, EE_RADIANCE)
    print("Part C done.")

# %% [markdown]
# ## Part D: the models, state by state
#
# - **Across space (step 5, the plan's main measure):** rarefied species ~ buildings + trees + farmland + water +
#   elevation + light, all standardised, cluster-robust errors over 0.5 degree blocks. Light's coefficient is
#   reported per SD (as in step 5) and **per 10x brighter** (per SD divided by the SD of log10 light).
# - **Over time (step 6, secondary):** species per visit, square and year fixed effects, light (log10) and
#   buildings (interpolated between 2015, 2020, 2025), weighted by visits.
# - **Eligibility (plan):** a state needs >= 150 squares in the model and >= 10 blocks.
# - **Factors (plan, P2):** F1 built-up area per person, F2 NO2, F3 tree cover, F4 median observers per square,
#   all over the state's squares in the model.

# %%
ee_table = load(EE_TABLE)
d_all = squares.merge(ee_table, on="sq", how="left")
d_all = d_all[(d_all["visits"] >= MIN_VISITS) & d_all["species_rarefied"].notna()
              & d_all["radiance_mean"].notna()].copy()
d_all["light"] = np.log10(d_all["radiance_mean"] + 0.1)
d_all["block"] = (d_all["ilat"] // BLOCK).astype(str) + "_" + (d_all["ilon"] // BLOCK).astype(str)
HABITAT = ["built", "tree", "crop", "water", "elevation_m"]
gaps = d_all[HABITAT + ["light"]].isna().any(axis=1)
if gaps.any():
    print(f"{gaps.sum()} squares have a missing habitat value and are left out")
    d_all = d_all[~gaps].copy()
print(f"Squares in the model (>= {MIN_VISITS} visits, >= {RAREFY_N} records): {len(d_all):,}")


def normal_p(z):
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))


def ols(data, y_col, x_cols, cluster):
    """Step 5's model, unchanged: standardised predictors, cluster-robust standard errors."""
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


def demean_two_way(df, cols, w, a="square", b="year", tol=1e-10, max_iter=500):
    """Step 6's weighted 'within' transformation, unchanged."""
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
    """Step 6's two-way fixed-effects model, unchanged."""
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


# Over-time table: species per visit per square-year + light that year + buildings that year
sy = load(SQYEARS).merge(load(EE_RADIANCE), on=["sq", "year"], how="left")
sy = sy.merge(ee_table[["sq", "built2015", "built", "built2025"]], on="sq", how="left")
sy = sy.merge(squares[["sq", "ilat", "ilon", "state"]], on="sq", how="left")
sy["light"] = np.log10(sy["radiance"] + 0.1)
yrs = sy["year"].to_numpy()
b15, b20, b25 = (sy[c].to_numpy(float) for c in ["built2015", "built", "built2025"])
sy["built_year"] = np.where(yrs <= 2020, b15 + (b20 - b15) * (yrs - 2015) / 5, b20 + (b25 - b20) * (yrs - 2020) / 5)
sy["block"] = (sy["ilat"] // BLOCK).astype(str) + "_" + (sy["ilon"] // BLOCK).astype(str)
sy["square"] = sy["ilat"].astype(str) + "_" + sy["ilon"].astype(str)
panel_all = sy[(sy["visits"] >= MIN_VISITS_YEAR) & sy["light"].notna()].copy()
panel_all = panel_all[panel_all.groupby("square")["year"].transform("size") >= MIN_YEARS]


def analyse(unit_squares, unit_panel):
    """Everything the plan needs for one state (or, in a reproduction run, the whole download)."""
    out = {"n_squares": len(unit_squares), "n_blocks": unit_squares["block"].nunique()}
    if out["n_squares"] >= 10 and out["n_blocks"] >= 2:        # the bare minimum to fit; eligibility is separate
        m = ols(unit_squares, "species_rarefied", HABITAT + ["light"], "block").loc["light"]
        sd = unit_squares["light"].std()
        out.update({"coef_sd": m["coef"], "se_sd": m["se"], "low95_sd": m["low95"], "high95_sd": m["high95"],
                    "p": m["p"], "sd_light": sd, "coef_10x": m["coef"] / sd, "se_10x": m["se"] / sd,
                    "low95_10x": m["low95"] / sd, "high95_10x": m["high95"] / sd})
    if len(unit_panel) >= 30 and unit_panel["block"].nunique() >= 2:
        tab, n_sy, n_sq = twfe(unit_panel, "species_per_visit", ["light", "built_year"])
        r = tab.loc["light"]
        out.update({"time_coef_10x": r["coef"], "time_se_10x": r["se"], "time_p": r["p"],
                    "time_square_years": n_sy, "time_squares": n_sq,
                    "time_blocks": unit_panel["block"].nunique()})
    # plan factors
    lat_mid = np.radians(unit_squares["lat"] + CELL / 2)
    area = (CELL * 111_320) ** 2 * np.cos(lat_mid)              # m2 per square
    ok = unit_squares["pop"].notna()
    people = (unit_squares.loc[ok, "pop"] * area[ok] / 1e4).sum()   # pop = people per 100 m x 100 m pixel
    built_m2 = (unit_squares.loc[ok, "built"] * area[ok]).sum()
    out.update({"F1_built_m2_per_person": built_m2 / people if people > 0 else np.nan,
                "F2_no2_umol_m2": unit_squares["no2"].mean() * 1e6,
                "F3_tree_share": unit_squares["tree"].mean(),
                "F4_median_observers": unit_squares["observers"].median(),
                "mean_state_share": unit_squares["state_share"].mean()})
    return out


RESULTS = OUT / "results"
RESULTS.mkdir(exist_ok=True)

if REPRO:
    res = analyse(d_all, panel_all)
    target, target_n = RUNS[RUN]["old_coef_per_sd"], RUNS[RUN]["old_squares"]
    passed = abs(res["coef_sd"] - target) < 0.01 and res["n_squares"] == target_n
    print(f"\nREPRODUCTION CHECK ({RUN}):")
    print(f"  squares in the model: {res['n_squares']:,} (old code: {target_n:,})")
    print(f"  light, per SD:  {res['coef_sd']:+.4f} (old code: {target:+.4f})  "
          f"95% range {res['low95_sd']:+.2f} to {res['high95_sd']:+.2f}")
    print(f"  light, per 10x brighter: {res['coef_10x']:+.3f} (SD of log10 light = {res['sd_light']:.3f})")
    if "time_coef_10x" in res:
        print(f"  over time (species per visit, per 10x brighter): {res['time_coef_10x']:+.3f} "
              f"(+/- {1.96 * res['time_se_10x']:.3f})")
    print("  => " + ("PASSED: the new code reproduces the old result." if passed else
                     "FAILED: the new code does NOT reproduce the old result. Stop and find out why."))
    expected = 16 if RUN == "repro_karnataka" else 17
    print(f"  (state names: {(d_all['state'] == expected).mean():.1%} of model squares are assigned to "
          f"{STATES[expected]})")
    pd.DataFrame([{"run": RUN, "passed": passed, "old_coef_per_sd": target, **res}]).to_csv(
        RESULTS / "reproduction_check.csv", index=False)
else:
    rows = []
    for code in ELIGIBLE:
        unit = d_all[d_all["state"] == code]
        r = analyse(unit, panel_all[panel_all["state"] == code])
        r.update({"state_code": code, "state": STATES[code],
                  "half": "seen" if code in SEEN else ("holdout" if code in HOLDOUT else "explore")})
        r["eligible"] = bool(r["n_squares"] >= MIN_SQUARES and r["n_blocks"] >= MIN_BLOCKS
                             and pd.notna(r.get("coef_10x")))
        rows.append(r)
    res = pd.DataFrame(rows)
    for c in ["coef_sd", "se_sd", "low95_sd", "high95_sd", "p", "sd_light", "coef_10x", "se_10x", "low95_10x",
              "high95_10x", "time_coef_10x", "time_se_10x", "time_p", "time_square_years", "time_squares",
              "time_blocks"]:
        if c not in res:
            res[c] = np.nan                      # a model that could not be fitted anywhere still gets its column
    first = ["state_code", "state", "half", "eligible", "n_squares", "n_blocks"]
    res = res[first + [c for c in res.columns if c not in first]]
    # Eligibility is not a light result, so it is shown for every state (plan: checked using no light results)
    print("\nEligibility (>= 150 squares and >= 10 blocks):")
    print(res[first].to_string(index=False))
    explore = res[res["half"] != "holdout"]
    sealed = res[res["half"] == "holdout"]
    explore.to_csv(RESULTS / "explore_states.csv", index=False)
    sealed.to_csv(RESULTS / "SEALED_holdout_states.csv", index=False)     # not opened until the final tests
    print(f"\nSaved explore_states.csv ({len(explore)} states) and SEALED_holdout_states.csv "
          f"({len(sealed)} states, not shown) in {RESULTS}")
    show = explore[explore["eligible"]].sort_values("coef_10x")
    print("\nEXPLORE HALF: light per 10x brighter, after habitat (species per 200 records)")
    for r in show.itertuples():
        print(f"  {r.state:<22}{r.n_squares:>5} sq {r.n_blocks:>3} bl  {r.coef_10x:+6.2f} "
              f"[{r.low95_10x:+6.2f}, {r.high95_10x:+6.2f}]   per SD {r.coef_sd:+5.2f}   "
              f"F1 {r.F1_built_m2_per_person:6.1f}  F2 {r.F2_no2_umol_m2:6.1f}  F3 {r.F3_tree_share:.2f}  "
              f"F4 {r.F4_median_observers:4.0f}")

    import matplotlib.pyplot as plt
    if len(show):
        fig, axes = plt.subplots(1, 5, figsize=(22, 5), gridspec_kw={"width_ratios": [1.6, 1, 1, 1, 1]})
        axes[0].errorbar(show["coef_10x"], range(len(show)), xerr=1.96 * show["se_10x"], fmt="o", color="#c4652f")
        axes[0].axvline(0, color="black", lw=0.8)
        axes[0].set_yticks(range(len(show)), show["state"])
        axes[0].set_xlabel("species per 10x brighter (95% range)")
        axes[0].set_title("Explore half: light after habitat")
        for ax, f, lab in zip(axes[1:], ["F1_built_m2_per_person", "F2_no2_umol_m2", "F3_tree_share",
                                         "F4_median_observers"],
                              ["F1 built m2 per person", "F2 NO2 (umol/m2)", "F3 tree cover", "F4 observers/square"]):
            ax.errorbar(show[f], show["coef_10x"], yerr=1.96 * show["se_10x"], fmt="o", color="#7a9cc6")
            for r in show.itertuples():
                ax.annotate(r.state[:10], (getattr(r, f), r.coef_10x), fontsize=7)
            ax.axhline(0, color="black", lw=0.8)
            ax.set_xlabel(lab)
        fig.tight_layout()
        fig.savefig(RESULTS / "explore_states.png", dpi=130)
        print(f"Plot saved: {RESULTS / 'explore_states.png'}")
        plt.show()
