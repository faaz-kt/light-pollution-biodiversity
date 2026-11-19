"""A fake India download with a PLANTED truth about light, per state.
world = "null"   : light does nothing anywhere
        "no2"    : light removes species, more so where NO2 is high (the plan's F2 should be found)
        "random" : the light effect differs between states at random (P1 yes, but no factor should explain it)"""
import sys, zipfile
import numpy as np
import truth_india as truth
out_zip, world, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
SCALE = float(sys.argv[4]) if len(sys.argv) > 4 else 8   # how strongly light acts on sensitive species
rng = np.random.default_rng(seed)
CELL = 0.05
S = [(16, "Karnataka", (12, 15), (75, 77.5)), (17, "Kerala", (8.6, 11.8), (76, 77)), (31, "Tamil Nadu", (9, 12.5), (77.5, 80)),
     (20, "Maharashtra", (17, 20.5), (73.5, 77.5)), (11, "Gujarat", (21, 24), (70, 73.5)), (35, "Uttarakhand", (29, 31), (78, 80.5)),
     (19, "Madhya Pradesh", (22, 25), (76, 80)), (29, "Rajasthan", (25, 28.5), (72, 76)), (36, "West Bengal", (22, 26.5), (87.5, 88.8)),
     (4, "Assam", (25.8, 27.3), (90.5, 94.5)), (34, "Uttar Pradesh", (25.5, 28.5), (79, 83.5)), (32, "Telangana", (16.5, 19.5), (78, 80.5)),
     (12, "Haryana", (28.3, 30.3), (75.5, 77.3)), (2, "Andhra Pradesh", (14, 16.5), (78, 81)), (10, "Goa", (15.1, 15.7), (73.8, 74.2)),
     (7, "Chhattisgarh", (19.5, 23), (81, 83.5)), (26, "Odisha", (19.5, 22), (83.5, 86.5)), (25, "Delhi", (28.45, 28.85), (76.9, 77.3)),
     (13, "Himachal Pradesh", (31, 32.8), (76, 78.3)), (1, "Andaman and Nicobar Islands", (10.5, 13.5), (92.3, 93.1)), (28, "Punjab", (30, 32), (74, 76.5))]
z_no2 = {c: (truth.no2(np.mean(la), 0, 2020) - 2e-5) / 0.8e-5 for c, n, la, lo in S}   # roughly standardised
beta = {}
for c, n, la, lo in S:
    beta[c] = {"null": 0.0, "no2": -0.12 - 0.12 * z_no2[c], "random": rng.normal(-0.12, 0.12)}[world]
species = [f"Genus{i // 6} species{i}" for i in range(220)]
base_p = rng.beta(0.6, 6, len(species))
sensitive = rng.random(len(species)) < 0.5     # light acts on these species only (it changes WHICH birds, not just how many records)
lines = ["\t".join(["species", "taxonRank", "stateProvince", "occurrenceStatus", "decimalLatitude", "decimalLongitude",
                    "day", "month", "year", "recordedBy"])]
for c, name, (la0, la1), (lo0, lo1) in S:
    all_cells = [(i, j) for i in range(round(la0 / CELL), round(la1 / CELL)) for j in range(round(lo0 / CELL), round(lo1 / CELL))]
    pick = rng.choice(len(all_cells), size=min(170, len(all_cells)), replace=False)
    cells = [all_cells[k] for k in pick]
    L = np.array([np.log10(truth.radiance((i + .5) * CELL, (j + .5) * CELL, 2020) + 0.1) for i, j in cells])
    for (i, j), l in zip(cells, L):
        clat, clon = (i + 0.5) * CELL, (j + 0.5) * CELL
        rich = np.exp(0.6 * truth.tree(clat, clon) - 0.8 * truth.built(clat, clon))
        p = np.clip(base_p * rich * np.where(sensitive, np.exp(SCALE * beta[c] * (l - L.mean())), 1.0), 0, 0.9)
        for v in range(int(rng.integers(26, 34))):
            obs = f"obsr{int(rng.integers(1, 5000))}"
            y, m, d = int(rng.integers(2015, 2026)), int(rng.integers(1, 13)), int(rng.integers(1, 29))
            for s in np.flatnonzero(rng.random(len(species)) < p):
                lines.append(f"{species[s]}\tSPECIES\t{name}\tPRESENT\t{clat + rng.uniform(-.024, .024):.6f}\t"
                             f"{clon + rng.uniform(-.024, .024):.6f}\t{d}\t{m}\t{y}\t{obs}")
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(out_zip.split("/")[-1].replace(".zip", ".csv"), "\n".join(lines) + "\n")
print(f"{world}: {len(lines) - 1:,} records; planted beta by state:", {n[:8]: round(beta[c], 2) for c, n, _, _ in S})
