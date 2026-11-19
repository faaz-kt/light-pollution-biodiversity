# %% [markdown]
# # Step 7b: are AVONET "migrants" really migrants here in Karnataka?
#
# AVONET gives each species ONE migration score for the whole world. A species can be migratory in Europe or
# Siberia but have a population that lives in Karnataka all year: the Black Kite and Shikra are good examples.
# If those year-round birds are labelled "migrants", the step 6/7 "migrants rise with light" result could
# really be about **city-loving resident birds**, not migrants.
#
# Check with our own records: for each species, the **reporting rate** (share of visits that recorded it) in the
# monsoon (Jun-Aug) divided by the rate in winter (Nov-Feb).
# - ratio near **1** (or above) = here all year
# - ratio near **0** = only here in winter (a true winter visitor)
#
# Reporting rates are fair even though people birdwatch less in the rain, because each month is divided by
# its own number of visits. Tested first on fake data: a planted all-year species scored 1.01, a planted
# winter-only species 0.00.
#
# **Before running, predict:** what share of "migrant" records come from birds that are here all year?

# %%
# ---------------------------------------------------------------- SETTINGS --
REGION = "karnataka"        # "karnataka" (main study) or "kerala" (replication, see PLAN_step8_kerala.md)
REGIONS = {"karnataka": {"folder": "lpb", "lat": (11.5, 18.5), "lon": (74.0, 78.75)},
           "kerala": {"folder": "lpb_kerala", "lat": (8.0, 13.0), "lon": (74.5, 77.5)}}
(LAT_MIN, LAT_MAX), (LON_MIN, LON_MAX) = REGIONS[REGION]["lat"], REGIONS[REGION]["lon"]   # box around the state
CELL = 0.05
WINTER, MONSOON = [11, 12, 1, 2], [6, 7, 8]
VISITOR_MAX_RATIO = 0.2     # "winter visitor here" = recorded in monsoon less than 1/5 as often as in winter
RESIDENT_MIN_RATIO = 0.5    # "here all year" = recorded in monsoon at least half as often as in winter

import sys
from pathlib import Path
import numpy as np
import pandas as pd

if "google.colab" in sys.modules:
    from google.colab import drive
    drive.mount("/content/drive")
    BASE = Path("/content/drive/MyDrive/bigdata") / REGIONS[REGION]["folder"]
else:
    _options = [Path.home() / "bigdata" / REGIONS[REGION]["folder"],
                Path.home() / "Downloads" / "bigdata" / REGIONS[REGION]["folder"]]
    BASE = next((p for p in _options if p.exists()), _options[0])
CLEAN = BASE / "clean"
print(f"Data folder: {BASE}")

# %%
# One row per species per visit (visit = observer x day x square, as in steps 6-7)
COLS = ["species", "decimalLatitude", "decimalLongitude", "year", "month", "day", "recordedBy"]
rows = []
for p in sorted((CLEAN / "birds_parts").glob("part_*")):
    b = pd.read_parquet(p, columns=COLS) if p.suffix == ".parquet" else pd.read_csv(p, usecols=COLS)
    b = b[b["year"].between(2015, 2025)]
    b["ilat"] = np.floor((b["decimalLatitude"].astype("float64") - LAT_MIN) / CELL + 1e-9).astype("int16")
    b["ilon"] = np.floor((b["decimalLongitude"].astype("float64") - LON_MIN) / CELL + 1e-9).astype("int16")
    b["day"] = b["day"].fillna(0).astype("int8")
    rows.append(b[["ilat", "ilon", "year", "month", "day", "recordedBy", "species"]].drop_duplicates())
d = pd.concat(rows, ignore_index=True)
d["species"] = d["species"].astype(str)
visit_key = ["ilat", "ilon", "year", "month", "day", "recordedBy"]
d = d.drop_duplicates(visit_key + ["species"])

# Reporting rate = share of visits in that month that recorded the species
visits_per_month = d.drop_duplicates(visit_key).groupby("month").size()
det_month = d.groupby(["species", "month"]).size().unstack(fill_value=0).reindex(columns=range(1, 13), fill_value=0)
rate = det_month.div(visits_per_month, axis=1)
season = pd.DataFrame({"rate_winter": rate[WINTER].mean(axis=1), "rate_monsoon": rate[MONSOON].mean(axis=1)})
season["monsoon_vs_winter"] = season["rate_monsoon"] / season["rate_winter"].replace(0, np.nan)
season.index.name = "species"

# %%
sp = pd.read_csv(CLEAN / "step7_species_traits.csv").merge(season, left_on="species", right_index=True, how="left")
sp["local_winter_visitor"] = (sp["monsoon_vs_winter"] < VISITOR_MAX_RATIO).astype(float)
sp.to_csv(CLEAN / "step7b_seasonality.csv", index=False)

mig = sp[sp["migrant"] == 1]
tot = mig["detections"].sum()
res_here = mig[mig["monsoon_vs_winter"] >= RESIDENT_MIN_RATIO]
vis_here = mig[mig["monsoon_vs_winter"] < VISITOR_MAX_RATIO]
print(f"AVONET 'migrants': {len(mig)} species, {tot:,} detections")
print(f"  seen all year here (monsoon >= half of winter): {len(res_here)} species = {res_here['detections'].sum() / tot:.0%} of their detections")
print(f"  true winter visitors here (monsoon < 1/5 of winter): {len(vis_here)} species = {vis_here['detections'].sum() / tot:.0%}")
lv = sp[sp["local_winter_visitor"] == 1]
print(f"Data-based winter visitors (any AVONET label): {len(lv)} species, {lv['detections'].sum() / sp['detections'].sum():.1%} of all detections; "
      f"{int((lv['migrant'] == 1).sum())} of them AVONET migrants")
print()
print("Top 25 AVONET 'migrants' by detections. ratio = monsoon rate / winter rate (1 = all year, 0 = winter only)")
for r in mig.sort_values("detections", ascending=False).head(25).itertuples():
    kind = "water" if r.water == 1 else "land"
    print(f"  {r.species:<27}{kind:<6}{r.monsoon_vs_winter:5.2f}  {r.detections:>7,}")

# %% [markdown]
# **Result (run 17 Nov 2026):** of 195 AVONET "migrants" (1.0 million detections), **22 species are here all
# year and make up 49% of the "migrant" detections**: Black Kite (ratio 0.97; 162,079 detections, the single
# biggest), Pied Bushchat 0.92, Red-rumped Swallow 1.23, Shikra 0.82, Little Swift 1.49, Purple Heron 0.85,
# Black-crowned Night Heron 1.76. Several of these do well in cities (kites scavenge, swifts nest on buildings).
# The other half comes from 151 true winter visitors (Blyth's Reed Warbler 0.00, Barn Swallow 0.02, Common
# Sandpiper 0.11, Wood Sandpiper 0.05, Brown Shrike 0.00, Garganey 0.01).
#
# So the step 6/7 "migrants" results mix two very different kinds of bird. **Next (step 7c):** redo the
# migrant tests with the data-based label (`local_winter_visitor`, 221 species, 9.4% of detections) and with
# "here all year" species kept apart.
