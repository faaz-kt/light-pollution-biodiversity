# %% [markdown]
# # India: post-hoc square-level looks (EXPLORATORY, after the final tests) - run in Colab
#
# Listed in PLAN_india.md "Changes" (18 Nov 2026, ~19:35 IST) before being run; run 18 Nov ~19:50 IST (Colab cells
# "POST-HOC 1/3" to "3/3"). Output copied to results/india_posthoc_squares.md. Nothing here can confirm anything.
# Needs the finished India run in Drive (bigdata/lpb_india/india/) and Earth Engine (RESOLVE ecoregions).

# %% POST-HOC 1/3: load the saved India run into G (parts A-C reuse their saved outputs; stops before Part D writes)
import hashlib
src = open("/content/drive/MyDrive/bigdata/lpb_india/code/india_pipeline.py", encoding="utf-8").read()
print("pipeline sha256:", hashlib.sha256(src.encode("utf-8")).hexdigest()[:12], "(expected 77d8949d7626)")
src = src.replace('\nRUN = "repro_karnataka"', '\nRUN = "india"', 1)
cut = src.index('\nRESULTS = OUT / "results"')
G = {"__name__": "__main__"}
exec(compile(src[:cut], "india_pipeline.py", "exec"), G)
d = G["d_all"]
print(len(d), "model squares;", sorted(d.columns.tolist()))

# %% POST-HOC 2/3: square level, all of India. Uses step 5's model (G["ols"]) unchanged.
import numpy as np, pandas as pd
from scipy import stats
ols, HAB = G["ols"], G["HABITAT"]
d = G["d_all"].copy()
d["state"] = d["state"].astype(int)
dum = pd.get_dummies(d["state"], prefix="st", drop_first=True, dtype=float)
dd = pd.concat([d, dum], axis=1)
STATE_COLS = list(dum.columns)
sdl = d["light"].std()

# (e1) one model for all of India
m0 = ols(d, "species_rarefied", HAB + ["light"], "block").loc["light"]
m1 = ols(dd, "species_rarefied", HAB + ["light"] + STATE_COLS, "block").loc["light"]
print(f"(e1) all India: {len(d):,} squares, {d['block'].nunique()} blocks, {d['state'].nunique()} states; SD of log10 light {sdl:.3f}")
print(f"  one model, no state levels:     light {m0['coef']/sdl:+.2f} species per 10x [{m0['low95']/sdl:+.2f}, {m0['high95']/sdl:+.2f}]")
print(f"  each state its own level (FE):  light {m1['coef']/sdl:+.2f} species per 10x [{m1['low95']/sdl:+.2f}, {m1['high95']/sdl:+.2f}]")


# (e2) does light's effect change with tree cover / birdwatchers / NO2 inside states? (light x modifier)
def inter_model(name, z, add_main):
    x = dd.copy()
    x["mod_z"] = (z - z.mean()) / z.std()
    x = x[x["mod_z"].notna()].copy()
    x["light_c"] = x["light"] - x["light"].mean()
    x["inter"] = x["light_c"] * x["mod_z"]
    cols = HAB + ["light", "inter"] + (["mod_z"] if add_main else []) + STATE_COLS
    r = ols(x, "species_rarefied", cols, "block")
    s_l, s_i = x["light"].std(), x["inter"].std()
    li, it = r.loc["light"], r.loc["inter"]
    print(f"  {name:<22} light at average {li['coef']/s_l:+.2f} per 10x; change in that per SD of {name}: "
          f"{it['coef']/s_i:+.2f} [{it['low95']/s_i:+.2f}, {it['high95']/s_i:+.2f}], p {it['p']:.3g}  ({len(x):,} squares)")


print("(e2) light x modifier, inside states (state levels included):")
inter_model("tree cover", d["tree"], False)
inter_model("observers (log10)", np.log10(d["observers"]), True)
inter_model("NO2", d["no2"], True)
inter_model("buildings", d["built"], False)

# (f) how tangled are light and buildings in each eligible state?
res = pd.concat([pd.read_csv(G["OUT"] / "results" / "explore_states.csv"),
                 pd.read_csv(G["OUT"] / "results" / "SEALED_holdout_states.csv")])
res = res[res["eligible"]]
rows = []
for code, g in d.groupby("state"):
    if code in set(res["state_code"]):
        rows.append({"state_code": code, "rho_light_built": stats.spearmanr(g["light"], g["built"])[0],
                     "rho_light_tree": stats.spearmanr(g["light"], g["tree"])[0],
                     "share_bright": (g["radiance_mean"] > 5).mean()})
f = res.merge(pd.DataFrame(rows), on="state_code")[["state", "coef_10x", "rho_light_built", "rho_light_tree", "share_bright", "sd_light"]]
print("(f) per state (eligible):")
print(f.sort_values("coef_10x").round(3).to_string(index=False))
for c in ["rho_light_built", "rho_light_tree", "share_bright", "sd_light"]:
    r, p = stats.spearmanr(f["coef_10x"], f[c])
    print(f"  across states, Spearman(light effect, {c}) = {r:+.2f} (p {p:.2f})")

# %% POST-HOC 3/3: (e3) the light x modifiers together; (g) the light effect by natural region
# (RESOLVE Ecoregions 2017, Dinerstein et al. 2017) instead of by state. Same model as the plan (G["analyse"]).
import ee
ee.Initialize(project="civil-clarity-442414-b7")

# (e3) all four modifiers in one model
x = dd.copy()
x = x[x["no2"].notna()].copy()
x["light_c"] = x["light"] - x["light"].mean()
mods = {"tree": x["tree"], "built": x["built"], "no2": x["no2"], "obs": np.log10(x["observers"])}
cols = HAB + ["light"]
for k, z in mods.items():
    x[k + "_z"] = (z - z.mean()) / z.std()
    x["lx_" + k] = x["light_c"] * x[k + "_z"]
    cols += ["lx_" + k]
cols += ["no2_z", "obs_z"] + STATE_COLS
r = ols(x, "species_rarefied", cols, "block")
print(f"(e3) light x all four modifiers together, inside states ({len(x):,} squares):")
for k in mods:
    s = x["lx_" + k].std()
    q = r.loc["lx_" + k]
    print(f"  light x {k:<6} {q['coef']/s:+.2f} [{q['low95']/s:+.2f}, {q['high95']/s:+.2f}] p {q['p']:.3g}")

# (g) natural regions
eco = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
img = ee.Image().int().paint(eco, "ECO_ID").rename("eco_id")
CELL = G["CELL"]
pts = pd.DataFrame({"sq": d["sq"].astype(int), "la": d["lat"] + CELL / 2, "lo": d["lon"] + CELL / 2})
got = []
for i in range(0, len(pts), 3000):
    ch = pts.iloc[i:i + 3000]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(b), float(a)]), {"sq": int(s)})
                               for s, a, b in zip(ch["sq"], ch["la"], ch["lo"])])
    out = img.reduceRegions(collection=fc, reducer=ee.Reducer.first(), scale=1000).getInfo()
    got += [(f["properties"]["sq"], f["properties"].get("first")) for f in out["features"]]
ecomap = pd.DataFrame(got, columns=["sq", "eco_id"])
meta = eco.filterBounds(ee.Geometry.Rectangle([68, 6, 97.5, 37.5]))
names = pd.DataFrame([f["properties"] for f in meta.select(["ECO_ID", "ECO_NAME", "BIOME_NAME"], None, False).getInfo()["features"]])
names = names.drop_duplicates("ECO_ID").rename(columns={"ECO_ID": "eco_id"})
d2 = d.merge(ecomap, on="sq", how="left").merge(names, on="eco_id", how="left")
print(f"(g) squares matched to an ecoregion: {d2['ECO_NAME'].notna().mean():.1%}")
d2.to_csv(G["OUT"] / "results" / "posthoc_square_ecoregions.csv", index=False, columns=["sq", "state", "eco_id", "ECO_NAME", "BIOME_NAME"])


def dl(y, se):
    y, se = np.asarray(y, float), np.asarray(se, float); w = 1 / se ** 2; k = len(y)
    m = np.sum(w * y) / np.sum(w); Q = float(np.sum(w * (y - m) ** 2))
    tau2 = max(0.0, (Q - (k - 1)) / (np.sum(w) - np.sum(w ** 2) / np.sum(w))); ws = 1 / (se ** 2 + tau2)
    return k, Q, float(stats.chi2.sf(Q, k - 1)), max(0.0, (Q - (k - 1)) / Q), float(np.sqrt(tau2)), float(np.sum(ws * y) / np.sum(ws))


def metareg(y, se, xv):
    y, se, xv = np.asarray(y, float), np.asarray(se, float), np.asarray(xv, float); k = len(y)
    X = np.column_stack([np.ones(k), (xv - xv.mean()) / xv.std(ddof=1)]); v = se ** 2; W = np.diag(1 / v)
    A = np.linalg.inv(X.T @ W @ X); b = A @ X.T @ W @ y; QE = float(np.sum((y - X @ b) ** 2 / v))
    P = W - W @ X @ A @ X.T @ W; tau2 = max(0.0, (QE - (k - 2)) / np.trace(P)); Ws = np.diag(1 / (v + tau2))
    As = np.linalg.inv(X.T @ Ws @ X); bs = As @ X.T @ Ws @ y
    s2 = float(np.sum((y - X @ bs) ** 2 / (v + tau2)) / (k - 2)); se_b = float(np.sqrt(s2 * As[1, 1]))
    return float(bs[1]), se_b, float(2 * stats.t.sf(abs(bs[1] / se_b), k - 2))


empty_panel = G["panel_all"].iloc[0:0]
for unit in ["BIOME_NAME", "ECO_NAME"]:
    rows = []
    for name, g in d2.dropna(subset=[unit]).groupby(unit):
        r = G["analyse"](g, empty_panel)
        r.update({"unit": name, "states": g["state"].nunique()})
        rows.append(r)
    t = pd.DataFrame(rows)
    t["eligible"] = (t["n_squares"] >= 150) & (t["n_blocks"] >= 10) & t["coef_10x"].notna()
    t.to_csv(G["OUT"] / "results" / f"posthoc_{unit.lower()}.csv", index=False)
    e = t[t["eligible"]].sort_values("coef_10x")
    print(f"\n(g) by {unit}: {len(t)} units, {len(e)} pass the plan's size rules (150 squares, 10 blocks)")
    print(e[["unit", "n_squares", "n_blocks", "states", "coef_10x", "low95_10x", "high95_10x", "F2_no2_umol_m2", "F3_tree_share", "F4_median_observers"]].round(2).to_string(index=False))
    if len(e) >= 4:
        k, Q, p, I2, tau, mu = dl(e["coef_10x"], e["se_10x"])
        print(f"  differ? Q {Q:.1f} on {k-1} df, p {p:.3g}, I2 {I2:.0%}, tau {tau:.2f}, average {mu:+.2f}")
        for fcol in ["F1_built_m2_per_person", "F2_no2_umol_m2", "F3_tree_share", "F4_median_observers"]:
            o = e.dropna(subset=[fcol])
            s, se_, pp = metareg(o["coef_10x"], o["se_10x"], o[fcol])
            print(f"  {fcol:<24} slope {s:+.2f} (SE {se_:.2f}) p {pp:.3g}  [{len(o)} units]")
