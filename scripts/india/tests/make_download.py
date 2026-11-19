"""A fake GBIF SIMPLE_CSV download (tab-separated, zipped), with the messy bits real ones have."""
import sys, zipfile, io
import numpy as np
import truth

out_zip, region, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
rng = np.random.default_rng(seed)
CELL = 0.05
boxes = {"karnataka": (11.5, 18.5, 74.0, 78.75, "Karnataka"), "kerala": (8.0, 13.0, 74.5, 77.5, "Kerala")}
lat0, lat1, lon0, lon1, sname = boxes[region]
n_sp = 180
fams = ["Strigidae", "Muscicapidae", "Corvidae", "Ardeidae", "Accipitridae", "Columbidae", "Sturnidae"]
species = [f"Genus{i // 6} species{i}" for i in range(n_sp)]
family = [fams[i % len(fams)] for i in range(n_sp)]
base_p = rng.beta(0.6, 6, n_sp)
cells = set()
while len(cells) < 380:
    cells.add((int(rng.integers(0, round((lat1 - lat0) / CELL))), int(rng.integers(0, round((lon1 - lon0) / CELL)))))
header = ["gbifID", "datasetKey", "occurrenceID", "kingdom", "order", "family", "species", "taxonRank",
          "locality", "stateProvince", "occurrenceStatus", "individualCount", "decimalLatitude",
          "decimalLongitude", "coordinateUncertaintyInMeters", "eventDate", "day", "month", "year",
          "basisOfRecord", "recordedBy", "issue"]
lines = ["\t".join(header)]
gid = 0
for (i, j) in sorted(cells):
    clat, clon = lat0 + (i + 0.5) * CELL, lon0 + (j + 0.5) * CELL
    light = np.log10(truth.radiance(clat, clon, 2020) + 0.1)
    rich = 1.0 + 0.8 * truth.tree(clat, clon) - 0.6 * truth.built(clat, clon) - 0.08 * light
    n_vis = int(rng.integers(3, 90))
    for v in range(n_vis):
        obs = "" if rng.random() < 0.03 else f"obsr{int(rng.integers(1, 400))}"
        year = int(rng.integers(2015, 2026)); month = int(rng.integers(1, 13)); day = int(rng.integers(1, 29))
        p = np.clip(base_p * rich * rng.uniform(0.6, 1.4), 0, 0.95)
        seen = np.flatnonzero(rng.random(n_sp) < p)
        for s in seen:
            reps = 2 if rng.random() < 0.03 else 1                  # duplicate records happen
            for _ in range(reps):
                gid += 1
                lat = clat + rng.uniform(-0.0249, 0.0249); lon = clon + rng.uniform(-0.0249, 0.0249)
                if rng.random() < 0.01:                              # exactly on a grid line
                    lat = round(lat0 + i * CELL, 2); lon = round(lon0 + j * CELL, 2)
                r = rng.random()
                status = "ABSENT" if r < 0.005 else "PRESENT"
                rank, spname = ("GENUS", "") if 0.005 <= r < 0.015 else ("SPECIES" if rng.random() < 0.9 else "SUBSPECIES", species[s])
                latt, lonn = (f"{lat:.6f}", f"{lon:.6f}") if not 0.015 <= r < 0.017 else ("", "")
                mon = "" if 0.017 <= r < 0.019 else str(month)
                dd = "" if 0.019 <= r < 0.03 else str(day)
                st = "" if rng.random() < 0.03 else sname
                loc = 'Lake "big' if rng.random() < 0.001 else "somewhere"
                lines.append("\t".join([str(gid), "ds1", f"o{gid}", "Animalia", "Passeriformes", family[s], spname,
                                        rank, loc, st, status, "1", latt, lonn, "30", f"{year}-{month:02d}-{day:02d}",
                                        dd, mon, str(year), "HUMAN_OBSERVATION", obs, ""]))
inner = out_zip.split("/")[-1].replace(".zip", ".csv")
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(inner, "\n".join(lines) + "\n")
print(f"{out_zip}: {len(lines) - 1:,} rows")
