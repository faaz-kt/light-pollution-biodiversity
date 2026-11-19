"""Fake India download: several states (with real-world spelling variants of their names), border squares
shared by two states, records outside India, and some records with no state name."""
import sys, zipfile
import numpy as np
import truth
out_zip, seed = sys.argv[1], int(sys.argv[2])
rng = np.random.default_rng(seed)
CELL = 0.05
# (name variants, lat range, lon range, squares)
states = [(["Karnataka"], (12, 15), (75, 77), 34), (["Kerala"], (9, 11.5), (76, 76.8), 30),
          (["Tamil Nadu"], (9.5, 12.5), (77.5, 79.5), 30), (["Maharashtra"], (17, 20), (73.5, 77), 30),
          (["Gujarat"], (21, 23.5), (70, 73), 26), (["Uttarakhand", "Uttaranchal"], (29.2, 30.8), (78, 80), 26),
          (["Madhya Pradesh"], (22, 25), (76, 80), 26), (["Rajasthan"], (25, 28), (72, 76), 26),
          (["West Bengal"], (22.2, 26), (87.5, 88.6), 26), (["Assam"], (26, 27), (90.5, 94), 26),
          (["Uttar Pradesh"], (26, 28.5), (79, 83), 26), (["Telangana"], (16.5, 19), (78, 80.5), 26),
          (["Haryana"], (28.5, 30), (75.5, 77), 26), (["Andhra Pradesh"], (14, 16.5), (78, 80.5), 26),
          (["Goa"], (15.1, 15.7), (73.8, 74.2), 26), (["Chhattisgarh"], (19.5, 22.5), (81, 83), 26),
          (["Odisha", "Orissa"], (19.5, 21.5), (84, 86.5), 26), (["Delhi", "NCT of Delhi"], (28.45, 28.85), (76.9, 77.3), 26),
          (["Himachal Pradesh"], (31.2, 32.5), (76.2, 78), 26), (["Andaman and Nicobar Islands", "Andaman & Nicobar"], (11, 13), (92.5, 93), 26),
          (["Punjab"], (30, 31.8), (74, 76), 26), (["Bihar"], (25.2, 27), (84, 87.5), 26), (["Sri Lanka x"], (7, 8), (80, 81), 3)]
species = [f"Genus{i // 6} species{i}" for i in range(220)]
base_p = rng.beta(0.6, 6, len(species))
header = ["gbifID", "species", "taxonRank", "stateProvince", "occurrenceStatus", "decimalLatitude",
          "decimalLongitude", "day", "month", "year", "recordedBy", "family", "locality"]
lines = ["\t".join(header)]
gid = 0
for names, (la0, la1), (lo0, lo1), n_cells in states:
    cells = set()
    while len(cells) < n_cells:
        cells.add((round(rng.uniform(la0, la1) / CELL), round(rng.uniform(lo0, lo1) / CELL)))
    for (i, j) in cells:
        clat, clon = (i + 0.5) * CELL, (j + 0.5) * CELL
        rich = 1.0 + 0.8 * truth.tree(clat, clon) - 0.6 * truth.built(clat, clon)
        for v in range(int(rng.integers(26, 70))):
            obs = "" if rng.random() < 0.02 else f"obsr{int(rng.integers(1, 3000))}"
            year = int(rng.integers(2015, 2026)); month = int(rng.integers(1, 13)); day = int(rng.integers(1, 29))
            for s in np.flatnonzero(rng.random(len(species)) < np.clip(base_p * rich, 0, 0.9)):
                gid += 1
                r = rng.random()
                st = "" if r < 0.02 else (names[1] if len(names) > 1 and r < 0.3 else names[0])
                if r > 0.995:
                    st = "Kerala" if names[0] == "Karnataka" else st     # a few mislabelled records
                lat = clat + rng.uniform(-0.024, 0.024); lon = clon + rng.uniform(-0.024, 0.024)
                lines.append("\t".join([str(gid), species[s], "SPECIES", st, "PRESENT", f"{lat:.6f}", f"{lon:.6f}",
                                        str(day), str(month), str(year), obs, "Fam", "x"]))
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(out_zip.split("/")[-1].replace(".zip", ".csv"), "\n".join(lines) + "\n")
print(f"{out_zip}: {len(lines) - 1:,} rows")
