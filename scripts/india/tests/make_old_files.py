"""The files the OLD steps would have fetched from Earth Engine: lights (step 3), habitat (step 5),
buildings by epoch (step 6), plus a fake AVONET sheet (step 6)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import truth
clean, region = Path(sys.argv[1]), sys.argv[2]
boxes = {"karnataka": (11.5, 18.5, 74.0, 78.75), "kerala": (8.0, 13.0, 74.5, 77.5)}
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = boxes[region]
CELL = 0.05
H, W = round((LAT_MAX - LAT_MIN) / CELL), round((LON_MAX - LON_MIN) / CELL)
clean.mkdir(parents=True, exist_ok=True)
rows, hab, epochs = [], [], []
for il in range(H):
    clat = LAT_MIN + (il + 0.5) * CELL
    for jl in range(W):
        clon = LON_MIN + (jl + 0.5) * CELL
        for y in range(2015, 2026):
            rows.append((round(LAT_MIN + il * CELL, 4), round(LON_MIN + jl * CELL, 4), y, truth.radiance(clat, clon, y),
                         "v21" if y <= 2021 else "v22"))
        hab.append((il, jl, truth.built(clat, clon), truth.tree(clat, clon), truth.crop(clat, clon),
                    truth.water(clat, clon), truth.elevation(clat, clon), "JRC GSW v1.4 max_extent (30 m)"))
        for e in (2015, 2020, 2025):
            epochs.append((il, jl, e, truth.built(clat, clon, e)))
pd.DataFrame(rows, columns=["lat", "lon", "year", "radiance", "version"]).to_csv(clean / "nightlights_0.05deg_2015-2025.csv", index=False)
pd.DataFrame(hab, columns=["ilat", "ilon", "built", "tree", "crop", "water", "elevation_m", "water_source"]).to_csv(clean / "habitat_0.05deg.csv", index=False)
pd.DataFrame(epochs, columns=["ilat", "ilon", "epoch", "built"]).to_csv(clean / "built_by_epoch_0.05deg.csv", index=False)
traits = clean.parent / "traits"; traits.mkdir(exist_ok=True)
sp = [f"Genus{i // 6} species{i}" for i in range(180)]
pd.DataFrame({"Species2": sp, "Trophic.Niche": ["Invertivore" if i % 3 else "Omnivore" for i in range(180)],
              "Migration": [3 if i % 5 == 0 else 1 for i in range(180)]}).to_csv(traits / "avonet_ebird.csv", index=False)
print("old-pipeline files written")
