# %% [markdown]
# # Step 4: put birds and night lights on the same map squares
#
# **What this does:** for every 5.5 km square (0.05°) of Karnataka and every year 2015-2025, count:
# - **records**: bird sightings
# - **species**: how many different species were seen
# - **observers**: how many different birdwatchers
# - **visits**: one birdwatcher in that square on one day = 1 visit (our measure of *effort*)
#
# and attach the square's **night brightness** that year (from step 3).
#
# Then a **first look**: do brighter squares have more or fewer species? And, the trap we expect:
# are brighter squares simply *visited more*? (More visits = more species found, whatever the light.)
#
# **Before running, predict:** across Karnataka, do you think bright squares will show MORE species
# or FEWER species than dark ones in the raw numbers? And after comparing squares with similar effort?

# %%
# ---------------------------------------------------------------- SETTINGS --
CELL = 0.05                 # must match step 3
REGION = "karnataka"        # "karnataka" (main study) or "kerala" (replication, see PLAN_step8_kerala.md)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]   # box around the state
MIN_VISITS = 25             # squares with fewer visits are too poorly sampled to compare
# Rarefaction: compare every square at the SAME number of records. "If we picked RAREFY_N of this
# square's sightings at random, how many species would we expect?" Squares with fewer records are left out.
# (Comparing squares by "visits" alone wasn't enough: in a test on fake data with NO light effect,
# busy squares still looked richer, because one visit there produces more records.)
RAREFY_N = 200

# %%
import sys
import time
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

parts = sorted((CLEAN / "birds_parts").glob("part_*"))
lights_file = sorted(CLEAN.glob("nightlights_*deg_2015-*.csv"))[-1]
print(f"Bird pieces: {len(parts)}  |  lights: {lights_file.name}")
if not parts:
    raise SystemExit("No bird pieces found: run step 2 first.")


def square_index(values, origin):
    """Which square a coordinate falls in, as a whole number (0, 1, 2 ... from the box edge).
    Whole numbers avoid tiny decimal errors when we match birds to lights."""
    return np.floor((values.astype("float64") - origin) / CELL + 1e-9).astype("int32")


# %%
# Go through the bird pieces one at a time (to save memory) and keep only the UNIQUE combinations
# we need. E.g. if a square had 5,000 House Crow records in 2023, that's one (square, year, species) row.
COLUMNS = ["species", "decimalLatitude", "decimalLongitude", "year", "month", "day", "recordedBy"]
species_rows, visit_rows, record_counts, abundance_rows = [], [], [], []
start = time.time()

for i, part in enumerate(parts):
    if part.suffix == ".parquet":
        b = pd.read_parquet(part, columns=COLUMNS)
    else:
        b = pd.read_csv(part, usecols=COLUMNS)
    b["ilat"] = square_index(b["decimalLatitude"], LAT_MIN)
    b["ilon"] = square_index(b["decimalLongitude"], LON_MIN)
    inside = b["ilat"].between(0, round((LAT_MAX - LAT_MIN) / CELL) - 1) & \
             b["ilon"].between(0, round((LON_MAX - LON_MIN) / CELL) - 1)
    b = b[inside]
    key = ["ilat", "ilon", "year"]
    record_counts.append(b.groupby(key).size().rename("records"))
    species_rows.append(b[key + ["species"]].drop_duplicates())
    # records per species per square (all years together), needed for rarefaction
    abundance_rows.append(b.groupby(["ilat", "ilon", "species"]).size())
    # A visit = one observer, one square, one day. Missing day -> treated as its own "day".
    b["day"] = b["day"].fillna(0)
    visit_rows.append(b[key + ["recordedBy", "month", "day"]].drop_duplicates())
    print(f"  piece {i + 1}/{len(parts)} done ({(time.time() - start) / 60:.1f} min)")

key = ["ilat", "ilon", "year"]
records = pd.concat(record_counts).groupby(level=key).sum()
species_cy = pd.concat(species_rows).drop_duplicates()     # unique (square, year, species)
visits_cy = pd.concat(visit_rows).drop_duplicates()        # unique (square, year, observer, date)

per_year = pd.DataFrame({
    "records": records,
    "species": species_cy.groupby(key).size(),
    "observers": visits_cy.groupby(key)["recordedBy"].nunique(),
    "visits": visits_cy.groupby(key).size(),
}).reset_index()

# %%
# Attach the night lights. Convert the lights' corner coordinates to the same whole-number squares.
lights = pd.read_csv(lights_file)
lights["ilat"] = np.rint((lights["lat"] - LAT_MIN) / CELL).astype("int32")
lights["ilon"] = np.rint((lights["lon"] - LON_MIN) / CELL).astype("int32")
per_year = per_year.merge(lights[["ilat", "ilon", "year", "radiance", "version"]],
                          on=["ilat", "ilon", "year"], how="left")
per_year["lat"] = (LAT_MIN + per_year["ilat"] * CELL).round(4)   # lower-left corner, as in step 3
per_year["lon"] = (LON_MIN + per_year["ilon"] * CELL).round(4)

no_light = per_year["radiance"].isna().sum()
print(f"Square-years with birds: {len(per_year):,}  (without a light value: {no_light})")

# Also one row per square with all years pooled (more data per square, simpler first look).
species_cell = species_cy.groupby(["ilat", "ilon"])["species"].nunique()
observers_cell = visits_cy.groupby(["ilat", "ilon"])["recordedBy"].nunique()
cells = per_year.groupby(["ilat", "ilon", "lat", "lon"]).agg(
    records=("records", "sum"), visits=("visits", "sum"),
).reset_index()
idx = cells.set_index(["ilat", "ilon"]).index
cells["species"] = idx.map(species_cell)
cells["observers"] = idx.map(observers_cell)
mean_light = lights.groupby(["ilat", "ilon"])["radiance"].mean().rename("radiance_mean")
cells = cells.merge(mean_light, left_on=["ilat", "ilon"], right_index=True, how="left")

# Rarefied species (Hurlbert 1971): expected species in RAREFY_N records drawn at random from a square.
# For each species with N_i of the square's N records, the chance it is MISSED in n draws is
# C(N - N_i, n) / C(N, n); expected species = sum over species of (1 - that chance).
# lgamma works with logarithms of huge factorials so the numbers don't overflow.
from math import lgamma

def log_choose(a, k):
    return lgamma(a + 1) - lgamma(k + 1) - lgamma(a - k + 1)

def rarefied_species(counts, n):
    N = counts.sum()
    if N < n:
        return np.nan
    total = 0.0
    for Ni in counts:
        if N - Ni < n:
            total += 1.0                     # can't miss it: too common
        else:
            total += 1.0 - np.exp(log_choose(N - Ni, n) - log_choose(N, n))
    return total

abundance = pd.concat(abundance_rows).groupby(level=["ilat", "ilon", "species"]).sum()
rare = abundance.groupby(level=["ilat", "ilon"]).apply(lambda s: rarefied_species(s.values, RAREFY_N))
cells["species_rarefied"] = idx.map(rare.rename(f"species_in_{RAREFY_N}"))

per_year.to_csv(CLEAN / "step4_square_year.csv", index=False)
cells.to_csv(CLEAN / "step4_square_all_years.csv", index=False)
print(f"Saved step4_square_year.csv ({len(per_year):,} rows) and "
      f"step4_square_all_years.csv ({len(cells):,} squares) in {CLEAN}")

# %%
# FIRST LOOK. Spearman correlation: +1 = perfectly "more light, more X", -1 = "more light, less X", 0 = none.
# (Spearman uses ranks, so a few super-bright city squares can't dominate it.)
ok = cells[(cells["visits"] >= MIN_VISITS) & cells["radiance_mean"].notna()].copy()
print(f"Squares with at least {MIN_VISITS} visits: {len(ok):,} of {len(cells):,}\n")

def rho(df, a, b):
    return df[a].corr(df[b], method="spearman")

print(f"Light vs species (raw):  rho = {rho(ok, 'radiance_mean', 'species'):+.2f}")
print(f"Light vs visits (effort): rho = {rho(ok, 'radiance_mean', 'visits'):+.2f}")
print(f"Visits vs species:        rho = {rho(ok, 'visits', 'species'):+.2f}")
fair = ok[ok["species_rarefied"].notna()]
print(f"\nFair comparison (every square judged at {RAREFY_N} records; {len(fair):,} squares have enough):")
print(f"Light vs species per {RAREFY_N} records: rho = {rho(fair, 'radiance_mean', 'species_rarefied'):+.2f}")
print(f"Check, visits vs species per {RAREFY_N} records: rho = {rho(fair, 'visits', 'species_rarefied'):+.2f}"
      "  (should be much weaker than +0.9 if rarefaction removed most of the effort effect)")
print("\nWas your prediction right? (This is a first look, not the final answer: see the notes below.)")

# %%
# Plots
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
x = ok["radiance_mean"].clip(lower=0.01)    # log scale can't show 0, so tiny floor for dark squares

sc = axes[0].scatter(x, ok["species"], c=np.log10(ok["visits"]), s=8, cmap="viridis", alpha=0.7)
axes[0].set_xscale("log")
axes[0].set_xlabel("night brightness (nW/sr/cm², log scale)")
axes[0].set_ylabel("bird species recorded, 2015-2025")
axes[0].set_title("Raw: species vs light")
fig.colorbar(sc, ax=axes[0], label="log10(visits)")

axes[1].scatter(x, ok["visits"], s=8, color="#c4652f", alpha=0.6)
axes[1].set_xscale("log")
axes[1].set_yscale("log")
axes[1].set_xlabel("night brightness (log)")
axes[1].set_ylabel("visits (log)")
axes[1].set_title("The trap: brighter squares get more visits")

fx = fair["radiance_mean"].clip(lower=0.01)
axes[2].scatter(fx, fair["species_rarefied"], s=8, color="#7a9cc6", alpha=0.5, label="squares")
# median in 10 brightness groups with equal numbers of squares, to show the overall trend
groups = pd.qcut(fair["radiance_mean"].rank(method="first"), 10, labels=False)
med = fair.groupby(groups).agg(light=("radiance_mean", "median"), species=("species_rarefied", "median"))
axes[2].plot(med["light"].clip(lower=0.01), med["species"], "o-", color="#08306b", lw=2, label="median")
axes[2].set_xscale("log")
axes[2].set_xlabel("night brightness (log)")
axes[2].set_ylabel(f"expected species in {RAREFY_N} records")
axes[2].set_title("Fairer: every square judged at equal records")
axes[2].legend()

fig.tight_layout()
fig.savefig(CLEAN / "step4_first_look.png", dpi=130)
print(f"Plot saved to {CLEAN / 'step4_first_look.png'}")
plt.show()

# %% [markdown]
# **How to read this (and why it's not the final answer yet):**
# - Left: if bright squares show MORE species, it's probably because they're visited more (middle plot),
#   not because light helps birds. That's the sampling-bias trap.
# - Right: every square judged at the same number of records. A median line going DOWN to the right
#   would hint that brighter squares have fewer species at equal effort. Flat = no sign of a light effect.
# - Still to handle in later steps: light goes together with cities (habitat loss, noise, heat), so a
#   light effect and a city effect are mixed up; neighbouring squares aren't independent; and records
#   aren't a perfect measure of effort either. Next we'll use a proper model (e.g. species ~ light + effort
#   + habitat).
