"""
Step 1: LOOK at the bird data for Karnataka before analysing anything.

What this script does (about 5 minutes, mostly waiting for GBIF's servers):
  1. Asks GBIF how many bird records exist in Karnataka (no download, just counts).
  2. Counts records per YEAR, per SOURCE (dataset) and per SPECIES.
  3. Builds a "where are the records" map: Karnataka is cut into small squares
     (0.25 degrees, about 27 km) and GBIF tells us how many records fall in each one.
  4. Downloads a small SAMPLE (300 records) so you can open it in Excel and see
     what a single record looks like.

Why not just download everything? Karnataka has ~8 million bird records. GBIF's
normal search can only page through the first 100,000, so the full data has to
come from a GBIF "download" (free account). That is step 1b, later. Counting is
enough to understand the data first.

Everything is cached in bigdata/lpb/step1/, so running it again is fast (delete a file
there to force a fresh download).

Run:  python step1_gbif_pull.py
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- SETTINGS --
GBIF = "https://api.gbif.org/v1"
REGION_GID = "IND.16_1"     # GADM code for Karnataka (checked on GBIF's geocode service)
REGION_NAME = "Karnataka"
TAXON_KEY = 212             # GBIF's key for the class Aves = all birds
TAXON_NAME = "birds"

# Rough box around Karnataka, used only for the map grid.
LAT_MIN, LAT_MAX = 11.5, 18.5
LON_MIN, LON_MAX = 74.0, 78.75
CELL = 0.25                 # grid square size in degrees (~27 km)

SAMPLE_SIZE = 300           # records to download as an example (max 300 per request)
TOP_SPECIES = 20            # how many most-recorded species to list
PAUSE = 0.2                 # seconds between requests, to be polite to GBIF
TIMEOUT = 60                # seconds before giving up on one request
TRIES = 3                   # attempts per request

import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    BASE = Path("/content/drive/MyDrive/bigdata/lpb")
else:
    # Laptop: the data folder can be C:\Users\<you>\bigdata\lpb or Downloads\bigdata\lpb (first one found).
    _options = [Path.home() / "bigdata" / "lpb", Path.home() / "Downloads" / "bigdata" / "lpb"]
    BASE = next((p for p in _options if p.exists()), _options[0])
RAW = BASE / "step1"          # cached counts and the sample
REPORTS = BASE / "step1"      # overview plot and report
RAW.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# Every request includes these two filters: "in Karnataka" and "is a bird".
FILTERS = {"gadmGid": REGION_GID, "taxonKey": TAXON_KEY}

session = requests.Session()


def ask_gbif(path, params):
    """Send one request to GBIF and return the JSON answer. Retries on failure."""
    for attempt in range(1, TRIES + 1):
        try:
            r = session.get(f"{GBIF}/{path}", params=params, timeout=TIMEOUT)
            r.raise_for_status()
            time.sleep(PAUSE)
            return r.json()
        except requests.RequestException as err:
            print(f"   request failed ({err}); try {attempt}/{TRIES}")
            time.sleep(5 * attempt)
    raise RuntimeError(f"GBIF did not answer: {path} {params}")


def count(extra=None):
    """How many records match? limit=0 means 'just tell me the number'."""
    params = {**FILTERS, "limit": 0, **(extra or {})}
    return ask_gbif("occurrence/search", params)["count"]


def facet(field, limit):
    """Counts per value of one field (e.g. per year). Returns a DataFrame: value, records."""
    params = {**FILTERS, "limit": 0, "facet": field, "facetLimit": limit}
    answer = ask_gbif("occurrence/search", params)
    rows = answer["facets"][0]["counts"] if answer["facets"] else []
    return pd.DataFrame([(row["name"], row["count"]) for row in rows], columns=["value", "records"])


def cached(name, make):
    """Load bigdata/lpb/step1/<name> if it exists, otherwise make it and save it."""
    path = RAW / name
    if path.exists():
        print(f"   (using cached {path.name})")
        return pd.read_csv(path)
    table = make()
    table.to_csv(path, index=False)
    return table


# ------------------------------------------------------------ 1. TOTAL --
print(f"1. Total {TAXON_NAME} records in {REGION_NAME} ...")
total = count()
print(f"   {total:,} records")

# ------------------------------------------------- 2. YEARS, SOURCES --
print("2. Records per year, per source, per species ...")
years = cached("counts_by_year.csv", lambda: facet("year", 300))
years = years.rename(columns={"value": "year"}).astype({"year": int}).sort_values("year")


def make_sources():
    table = facet("datasetKey", 50)
    # Turn the dataset's code (a long ID) into its name, e.g. "EOD - eBird Observation Dataset".
    table["name"] = [ask_gbif(f"dataset/{key}", {}).get("title", "?") for key in table["value"]]
    return table


sources = cached("counts_by_source.csv", make_sources)


def make_species():
    # facetLimit 3000 is more than the number of bird species in India (~1,300),
    # so this list holds every species with at least one record.
    table = facet("speciesKey", 3000).rename(columns={"value": "speciesKey"})
    # Look up names only for the most-recorded ones (one request each).
    names = []
    for key in table["speciesKey"].head(TOP_SPECIES):
        info = ask_gbif(f"species/{key}", {})
        names.append((info.get("canonicalName", "?"), info.get("vernacularName", "")))
    names += [("", "")] * (len(table) - len(names))
    table["scientific_name"] = [n[0] for n in names]
    table["common_name"] = [n[1] for n in names]
    return table


species = cached("counts_by_species.csv", make_species).fillna("")
print(f"   {len(species):,} species recorded; {len(sources)} sources")

# ------------------------------------------------------- 3. GRID MAP --
print("3. Records per grid square (the slow part, ~500 requests) ...")
lat_edges = np.arange(LAT_MIN, LAT_MAX, CELL)
lon_edges = np.arange(LON_MIN, LON_MAX, CELL)
grid_file = RAW / "counts_by_cell.csv"

# Restart-safe: squares already counted (from an earlier, interrupted run) are kept.
done = pd.read_csv(grid_file) if grid_file.exists() else pd.DataFrame(columns=["lat", "lon", "records"])
done_keys = {(round(a, 4), round(b, 4)) for a, b in zip(done["lat"], done["lon"])}
todo = [(lat, lon) for lat in lat_edges for lon in lon_edges if (round(lat, 4), round(lon, 4)) not in done_keys]

new_rows = []
for i, (lat, lon) in enumerate(todo, 1):
    # "a,b" asks GBIF for a range: latitude between a and b.
    n = count({"decimalLatitude": f"{lat},{lat + CELL}", "decimalLongitude": f"{lon},{lon + CELL}"})
    new_rows.append({"lat": round(lat, 4), "lon": round(lon, 4), "records": n})
    if i % 50 == 0 or i == len(todo):
        print(f"   {i}/{len(todo)} squares")
        done = pd.concat([done, pd.DataFrame(new_rows)], ignore_index=True)
        done.to_csv(grid_file, index=False)   # save progress as we go
        new_rows = []
cells = pd.read_csv(grid_file)

# ------------------------------------------------------- 4. SAMPLE --
print(f"4. Downloading {SAMPLE_SIZE} example records ...")
sample_file = RAW / "sample_records.csv"
if sample_file.exists():
    sample = pd.read_csv(sample_file)
    print("   (using cached sample_records.csv)")
else:
    answer = ask_gbif("occurrence/search", {**FILTERS, "limit": SAMPLE_SIZE})
    sample = pd.DataFrame(answer["results"])
    # Keep the columns that matter for this project (all others are dropped).
    keep = ["gbifID", "species", "vernacularName", "eventDate", "year", "month", "day",
            "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
            "individualCount", "recordedBy", "basisOfRecord", "datasetName", "locality"]
    sample = sample[[c for c in keep if c in sample.columns]]
    sample.to_csv(sample_file, index=False)

# ---------------------------------------------------------- PLOTS --
print("Making plots ...")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: records per year. Log scale, because the numbers grow ~100x.
recent = years[years["year"] >= 1990]
axes[0].bar(recent["year"], recent["records"], color="#4a7ab8")
axes[0].set_yscale("log")
axes[0].set_xlabel("year")
axes[0].set_ylabel("records (log scale)")
axes[0].set_title(f"Records of {TAXON_NAME} in {REGION_NAME} per year")

# Right: map of records per square. Also log colours: a few city squares hold
# millions, most hold hundreds; on a normal scale everything else would look empty.
pivot = cells.pivot(index="lat", columns="lon", values="records").sort_index()
shown = np.log10(pivot.where(pivot > 0))         # empty squares stay blank
im = axes[1].pcolormesh(np.append(pivot.columns, pivot.columns[-1] + CELL),
                        np.append(pivot.index, pivot.index[-1] + CELL),
                        shown.values, cmap="viridis", shading="flat")
fig.colorbar(im, ax=axes[1], label="log10(records)  (3 = 1,000; 6 = 1,000,000)")
axes[1].plot(77.59, 12.97, "r*", markersize=12, label="Bengaluru")
axes[1].plot(76.64, 12.30, "m*", markersize=10, label="Mysuru")
axes[1].legend(loc="lower left")
axes[1].set_xlabel("longitude")
axes[1].set_ylabel("latitude")
axes[1].set_aspect("equal")
axes[1].set_title(f"Where the records are ({CELL}° squares)")

fig.tight_layout()
plot_file = REPORTS / "step1_overview.png"
fig.savefig(plot_file, dpi=130)

# --------------------------------------------------------- REPORT --
top_cells = cells.sort_values("records", ascending=False)
share_top5 = top_cells["records"].head(5).sum() / cells["records"].sum()
nonzero = (cells["records"] > 0).sum()

lines = [
    f"# Step 1 overview: {TAXON_NAME} in {REGION_NAME} (GBIF)",
    "",
    f"- Total records: **{total:,}**",
    f"- Species with at least one record: **{len(species):,}**",
    f"- Years covered: {years['year'].min()}-{years['year'].max()}; "
    f"records since 2015: {years.loc[years['year'] >= 2015, 'records'].sum():,}",
    f"- Grid squares with any record: {nonzero} of {len(cells)}",
    f"- **The 5 busiest squares hold {share_top5:.0%} of all records** (sampling bias!)",
    "",
    "## Sources",
    "| records | dataset |",
    "|---|---|",
    *[f"| {r.records:,} | {r.name} |" for r in sources.itertuples()],
    "",
    f"## Top {TOP_SPECIES} species",
    "| records | species | common name |",
    "|---|---|---|",
    *[f"| {r.records:,} | {r.scientific_name} | {r.common_name} |"
      for r in species.head(TOP_SPECIES).itertuples()],
    "",
    "## Busiest squares (lower-left corner)",
    "| lat | lon | records |",
    "|---|---|---|",
    *[f"| {r.lat} | {r.lon} | {r.records:,} |" for r in top_cells.head(10).itertuples()],
    "",
    f"Plot: `{plot_file.name}`. Example records: `{sample_file.name}` (same folder).",
]
report_file = REPORTS / "step1_overview.md"
report_file.write_text("\n".join(lines), encoding="utf-8")

print("\n".join(lines[:9]))
print(f"\nSaved {report_file} and {plot_file}")
plt.show()
