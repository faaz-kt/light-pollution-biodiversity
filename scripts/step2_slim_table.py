# %% [markdown]
# # Step 2: make a slim, clean table from the big GBIF download
#
# **What this does:** the GBIF file has 7.8 million rows and ~50 columns (4.4 GB unzipped), too big
# to load at once. We read it **in pieces of 500,000 rows**, keep only the ~15 columns we need, drop
# records we can't use, and save each piece as a small file. Together they make our working table.
#
# **Runs in two places, no changes needed:**
# - **Google Colab**: reads the zip from `My Drive/bigdata/lpb/`, saves results there too.
# - **Your laptop (VS Code)**: finds the zip in `bigdata\lpb`, `Downloads` or the project's `data\raw`.
#
# **Data:** Karnataka: GBIF.org (15 November 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.t3hgj6.
# Kerala (replication): the DOI is saved by step 1b in `bigdata/lpb_kerala/raw/gbif_download_info.json`.
#
# **Before running, predict:** out of 7.8 million records, how many do you think we'll have to throw
# away (no species name, no location, or "absent" records)? 1%? 10%? 30%?

# %%
# ---------------------------------------------------------------- SETTINGS --
REGION = "karnataka"          # "karnataka" (main study) or "kerala" (replication)
FOLDERS = {"karnataka": "lpb", "kerala": "lpb_kerala"}
# Karnataka's zip has GBIF's own name; for other regions, step 1b saved the zip in raw/ (found automatically)
ZIP_NAME = {"karnataka": "0008405-261110092616502.zip"}.get(REGION)
CHUNK_ROWS = 500_000          # rows per piece; lower this if the computer runs out of memory
MAX_UNCERTAINTY_M = 10_000    # flag records whose location is uncertain by more than 10 km

# Columns to keep. Everything else in the GBIF file is dropped.
KEEP = [
    "gbifID",                           # GBIF's ID for the record (to trace it back)
    "datasetKey",                       # which dataset (eBird, iNaturalist, ...)
    "order", "family", "species",       # what bird
    "taxonRank",                        # SPECIES / SUBSPECIES / GENUS ... (only species-level kept)
    "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters",    # how precise the location is
    "eventDate", "year", "month", "day",
    "individualCount",                  # how many birds were counted (often empty)
    "recordedBy",                       # observer ID (eBird: obsr...) -> needed for effort later
    "occurrenceStatus",                 # PRESENT or ABSENT
    "basisOfRecord",                    # human observation, specimen, ...
]

# %%
import csv
import json
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd

# Where are we? Colab has a module called google.colab; a laptop doesn't.
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    BASE = Path("/content/drive/MyDrive/bigdata") / FOLDERS[REGION]
else:
    # Laptop: the data folder can be C:\Users\<you>\bigdata\<folder> or Downloads\bigdata\<folder> (first found).
    _options = [Path.home() / "bigdata" / FOLDERS[REGION], Path.home() / "Downloads" / "bigdata" / FOLDERS[REGION]]
    BASE = next((p for p in _options if p.exists()), _options[0])
if ZIP_NAME:
    candidates = [BASE / "raw" / ZIP_NAME, BASE / ZIP_NAME, Path.home() / "Downloads" / ZIP_NAME]
else:
    candidates = sorted((BASE / "raw").glob("*.zip"))

zip_path = next((p for p in candidates if p.exists()), None)
if zip_path is None:
    raise FileNotFoundError("Couldn't find the GBIF zip. Looked in:\n" + "\n".join(map(str, candidates)))

OUT = BASE / "clean" / "birds_parts"    # one small file per piece
OUT.mkdir(parents=True, exist_ok=True)

# Parquet is a compact, fast table format. It needs the 'pyarrow' package (Colab has it).
# Without it, we save compressed CSV instead: slower and bigger, but works everywhere.
try:
    import pyarrow  # noqa: F401
    EXT = ".parquet"
except ImportError:
    EXT = ".csv.gz"

print(f"Running in: {'Colab' if IN_COLAB else 'laptop'}")
print(f"Reading:    {zip_path} ({zip_path.stat().st_size / 1e6:.0f} MB)")
print(f"Saving to:  {OUT}  (format {EXT})")

# %%
def clean(piece):
    """Drop unusable records from one piece. Returns (kept table, counts of what was dropped)."""
    dropped = {}

    absent = piece["occurrenceStatus"].eq("ABSENT")        # "species looked for but NOT seen"
    dropped["absent"] = int(absent.sum())
    piece = piece[~absent]

    no_species = piece["species"].isna() | ~piece["taxonRank"].isin(["SPECIES", "SUBSPECIES"])
    dropped["no species name"] = int(no_species.sum())     # e.g. "Accipiter sp." or just a family
    piece = piece[~no_species]

    no_place = piece["decimalLatitude"].isna() | piece["decimalLongitude"].isna()
    dropped["no coordinates"] = int(no_place.sum())
    piece = piece[~no_place]

    no_date = piece["year"].isna() | piece["month"].isna()
    dropped["no year/month"] = int(no_date.sum())
    piece = piece[~no_date]

    # Don't drop imprecise locations yet: just flag them, and decide later in the analysis.
    piece = piece.assign(imprecise=piece["coordinateUncertaintyInMeters"].gt(MAX_UNCERTAINTY_M))

    # Smaller number types = less memory (float32 still gives ~1 m precision for coordinates).
    piece = piece.astype({"decimalLatitude": "float32", "decimalLongitude": "float32",
                          "year": "int16", "month": "int8"})
    return piece, dropped


# %%
# Read the zip piece by piece. GBIF's file is TAB-separated and uses no quote marks,
# so QUOTE_NONE stops a stray " in a locality name from merging thousands of rows.
for old in OUT.glob("part_*"):   # remove pieces from an earlier run, so nothing is counted twice
    old.unlink()

start = time.time()
totals = {"read": 0, "kept": 0}
dropped_total = {}

with zipfile.ZipFile(zip_path) as z:
    inner = [n for n in z.namelist() if n.endswith(".csv")][0]
    with z.open(inner) as f:
        reader = pd.read_csv(f, sep="\t", quoting=csv.QUOTE_NONE, chunksize=CHUNK_ROWS,
                             usecols=lambda c: c in KEEP, dtype={"recordedBy": "string"},
                             on_bad_lines="skip", low_memory=False)
        for i, piece in enumerate(reader):
            part_file = OUT / f"part_{i:03d}{EXT}"
            totals["read"] += len(piece)
            kept, dropped = clean(piece)
            totals["kept"] += len(kept)
            for k, v in dropped.items():
                dropped_total[k] = dropped_total.get(k, 0) + v
            if EXT == ".parquet":
                kept.to_parquet(part_file, index=False)
            else:
                kept.to_csv(part_file, index=False)
            print(f"  piece {i:2d}: {totals['read']:>10,} read, {totals['kept']:>10,} kept "
                  f"({(time.time() - start) / 60:.1f} min)")

print(f"\nDone in {(time.time() - start) / 60:.1f} min.")
print(f"Read {totals['read']:,} records, kept {totals['kept']:,} "
      f"({totals['kept'] / max(totals['read'], 1):.1%}).")
for k, v in dropped_total.items():
    print(f"  dropped, {k}: {v:,}")
print("Was your prediction close?")

# %%
# Quick look at the slim table: load everything back (it's small now) and summarise.
parts = sorted(OUT.glob(f"part_*{EXT}"))
birds = pd.concat((pd.read_parquet(p) if EXT == ".parquet" else pd.read_csv(p) for p in parts),
                  ignore_index=True)

summary = {
    "records": len(birds),
    "species": birds["species"].nunique(),
    "observers": birds["recordedBy"].nunique(),
    "imprecise locations (>10 km)": int(birds["imprecise"].sum()),
    "memory used (MB)": round(birds.memory_usage(deep=True).sum() / 1e6),
}
for k, v in summary.items():
    print(f"{k:>30}: {v:,}")

print("\nTop 10 species:")
print(birds["species"].value_counts().head(10).to_string())
print("\nRecords per year:")
print(birds["year"].value_counts().sort_index().to_string())

# Save the summary next to the data, so we remember what the slim table holds.
info_file = BASE / "raw" / "gbif_download_info.json"
doi = json.loads(info_file.read_text())["doi"] if info_file.exists() else "10.15468/dl.t3hgj6"
lines = [f"# Step 2 summary, {REGION} (GBIF DOI {doi})", ""]
lines += [f"- {k}: {v:,}" for k, v in summary.items()]
lines += [f"- read: {totals['read']:,}"] + [f"- dropped, {k}: {v:,}" for k, v in dropped_total.items()]
(BASE / "clean" / "step2_summary.md").write_text("\n".join(lines), encoding="utf-8")
print(f"\nSummary saved to {BASE / 'clean' / 'step2_summary.md'}")
