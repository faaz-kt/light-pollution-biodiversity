# %% [markdown]
# # India: which places drive the outlier states? (post-hoc, EXPLORATORY) - run in Colab after india_posthoc_squares.py
#
# Listed in PLAN_india.md "Changes" (18 Nov 2026, ~19:45 IST) before being run; run as Colab cell "POST-HOC 4".
# Needs the notebook variables from india_posthoc_squares.py (G, d2, ols, HAB, metareg, ee). Output copied to
# results/india_posthoc_places.md; the moving-window table to results/india_posthoc_moving_window.csv (map:
# scripts/india/india_posthoc_map.py). City centres below are approximate and only used to name places.

# %%
CITIES = [  # name, lat, lon, big (metro, about 1 M people or more); approximate city centres
("Delhi",28.61,77.21,1),("Chandigarh",30.73,76.78,1),("Ludhiana",30.90,75.85,1),("Amritsar",31.63,74.87,1),
("Shimla",31.10,77.17,0),("Dharamshala",32.22,76.32,0),("Manali",32.24,77.19,0),("Dehradun",30.32,78.03,1),
("Rishikesh",30.09,78.27,0),("Nainital",29.38,79.46,0),("Ramnagar (Corbett)",29.39,79.13,0),
("Jaipur",26.91,75.79,1),("Jodhpur",26.24,73.02,1),("Udaipur",24.59,73.71,0),("Bikaner",28.02,73.31,0),
("Bharatpur",27.22,77.49,0),("Ajmer",26.45,74.64,0),("Kota",25.18,75.83,1),("Agra",27.18,78.01,1),
("Lucknow",26.85,80.95,1),("Kanpur",26.45,80.33,1),("Varanasi",25.32,82.97,1),("Prayagraj",25.44,81.85,1),
("Gorakhpur",26.76,83.37,0),("Bareilly",28.37,79.43,0),
("Kolkata",22.57,88.36,1),("Siliguri",26.73,88.40,0),("Darjeeling",27.04,88.26,0),("Durgapur",23.52,87.31,0),
("Bhubaneswar",20.30,85.82,1),("Puri",19.81,85.83,0),("Raipur",21.25,81.63,1),("Bilaspur",22.08,82.15,0),
("Jagdalpur",19.07,82.03,0),("Ranchi",23.34,85.31,1),("Patna",25.59,85.14,1),
("Guwahati",26.14,91.74,1),("Tezpur",26.63,92.80,0),("Kaziranga",26.58,93.42,0),("Jorhat",26.75,94.20,0),("Dibrugarh",27.47,94.91,0),
("Mumbai",19.08,72.88,1),("Pune",18.52,73.86,1),("Nashik",20.00,73.79,1),("Nagpur",21.15,79.09,1),
("Aurangabad",19.88,75.34,1),("Kolhapur",16.70,74.24,0),("Ahmedabad",23.02,72.57,1),("Surat",21.17,72.83,1),
("Vadodara",22.31,73.18,1),("Rajkot",22.30,70.80,1),("Bhuj",23.24,69.67,0),("Jamnagar",22.47,70.06,0),("Panaji",15.49,73.83,0),
("Bhopal",23.26,77.41,1),("Indore",22.72,75.86,1),("Jabalpur",23.18,79.95,1),("Gwalior",26.22,78.18,1),
("Bengaluru",12.97,77.59,1),("Mysuru",12.30,76.64,1),("Mangaluru",12.91,74.86,0),("Hubballi",15.36,75.12,0),
("Chennai",13.08,80.27,1),("Coimbatore",11.02,76.96,1),("Madurai",9.93,78.12,1),("Tiruchirappalli",10.79,78.70,0),
("Puducherry",11.94,79.81,0),("Ooty",11.41,76.70,0),("Hyderabad",17.39,78.49,1),("Visakhapatnam",17.69,83.22,1),
("Vijayawada",16.51,80.65,1),("Tirupati",13.63,79.42,0),("Kochi",9.93,76.27,1),("Thiruvananthapuram",8.52,76.94,1),
("Kozhikode",11.26,75.78,1),("Thrissur",10.53,76.21,1),("Kannur",11.87,75.37,0),("Munnar",10.09,77.06,0),
("Kollam",8.89,76.61,0),("Alappuzha",9.50,76.34,0),("Port Blair",11.62,92.73,0)]
C = pd.DataFrame(CITIES, columns=["city", "clat", "clon", "big"])


def km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


CELL = G["CELL"]
w = d2.copy().reset_index(drop=True)
w["la"] = w["lat"] + CELL / 2
w["lo"] = w["lon"] + CELL / 2
D = km(w["la"].to_numpy()[:, None], w["lo"].to_numpy()[:, None], C["clat"].to_numpy()[None, :], C["clon"].to_numpy()[None, :])
w["near_city"] = C["city"].to_numpy()[D.argmin(1)]
w["near_km"] = D.min(1)
w["big_km"] = D[:, C["big"].to_numpy() == 1].min(1)


def c10(g):
    m = ols(g, "species_rarefied", HAB + ["light"], "block").loc["light"]
    s = g["light"].std()
    return m["coef"] / s, m["se"] / s


res = pd.concat([pd.read_csv(G["OUT"] / "results" / "explore_states.csv"), pd.read_csv(G["OUT"] / "results" / "SEALED_holdout_states.csv")])
res = res[res["eligible"]].set_index("state_code")

# (i) drop one block at a time; (j) without city cores
rows = []
for code, g in w.groupby("state"):
    if code not in res.index:
        continue
    base, se = c10(g)
    infl = []
    for b, gb in g.groupby("block"):
        rest = g[g["block"] != b]
        infl.append((b, c10(rest)[0] - base, len(gb), gb["near_city"].mode().iloc[0], gb["near_km"].median()))
    infl.sort(key=lambda t: -abs(t[1]))
    nc = g[g["radiance_mean"] <= 20]
    nb = g[g["big_km"] > 25]
    rows.append({"state": res.loc[code, "state"], "check": base - res.loc[code, "coef_10x"], "coef": base, "se": se,
                 "block1": f"{infl[0][3]} ({infl[0][4]:.0f} km)", "chg1": infl[0][1], "sq1": infl[0][2],
                 "block2": f"{infl[1][3]} ({infl[1][4]:.0f} km)", "chg2": infl[1][1], "sq2": infl[1][2],
                 "n": len(g), "n_core": int((g["radiance_mean"] > 20).sum()), "no_core": c10(nc)[0],
                 "n_big25": int((g["big_km"] <= 25).sum()), "no_big25": c10(nb)[0] if nb["block"].nunique() >= 5 else np.nan})
T = pd.DataFrame(rows).sort_values("coef")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
print("(i)+(j) light per 10x brighter; chg = change in the state's value when that block is dropped")
print(T.round(2).to_string(index=False))
T.to_csv(G["OUT"] / "results" / "posthoc_state_influence.csv", index=False)

# (h) moving window
out = []
la, lo = w["la"].to_numpy(), w["lo"].to_numpy()
for a in np.arange(7.5, 35.5, 1.0):
    for b in np.arange(68.5, 97.5, 1.0):
        g = w[km(la, lo, a, b) <= 150]
        if len(g) >= 150 and g["block"].nunique() >= 10:
            c, s = c10(g)
            out.append((a, b, len(g), g["block"].nunique(), c, s))
MW = pd.DataFrame(out, columns=["lat", "lon", "n", "blocks", "coef", "se"])
MW.to_csv(G["OUT"] / "results" / "posthoc_moving_window.csv", index=False)
print("MW_START")
print(MW.round(3).to_csv(index=False))
print("MW_END")

# (k) rainfall (WorldClim V1 bio12, annual precipitation, mm)
bio = ee.Image("WORLDCLIM/V1/BIO").select("bio12")
got = []
for i in range(0, len(w), 3000):
    ch = w.iloc[i:i + 3000]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(b), float(a)]), {"sq": int(s)}) for s, a, b in zip(ch["sq"], ch["la"], ch["lo"])])
    o = bio.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=1000).getInfo()
    got += [(f["properties"]["sq"], f["properties"].get("mean")) for f in o["features"]]
w = w.merge(pd.DataFrame(got, columns=["sq", "rain_mm"]), on="sq", how="left")
dumw = pd.get_dummies(w["state"].astype(int), prefix="st", drop_first=True, dtype=float)
x = pd.concat([w, dumw], axis=1)
x = x[x["rain_mm"].notna()].copy()
x["rain_z"] = (x["rain_mm"] - x["rain_mm"].mean()) / x["rain_mm"].std()
x["tree_z"] = (x["tree"] - x["tree"].mean()) / x["tree"].std()
x["light_c"] = x["light"] - x["light"].mean()
x["lx_rain"] = x["light_c"] * x["rain_z"]
x["lx_tree"] = x["light_c"] * x["tree_z"]
r1 = ols(x, "species_rarefied", HAB + ["light", "lx_rain", "rain_z"] + list(dumw.columns), "block")
r2 = ols(x, "species_rarefied", HAB + ["light", "lx_rain", "rain_z", "lx_tree"] + list(dumw.columns), "block")
print(f"(k) rainfall matched for {x.shape[0]:,} squares")
for lab, r, ks in [("alone", r1, ["lx_rain"]), ("with light x trees", r2, ["lx_rain", "lx_tree"])]:
    for k in ks:
        s = x[k].std()
        q = r.loc[k]
        print(f"  {lab}: {k} {q['coef']/s:+.2f} per SD [{q['low95']/s:+.2f}, {q['high95']/s:+.2f}] p {q['p']:.3g}")
st_rain = w.groupby("state")["rain_mm"].mean()
e = res.copy()
e["rain"] = st_rain.reindex(e.index).to_numpy()
for lab, tab in [("13 fresh states", e[~e.index.isin([16, 17])]), ("15 states", e)]:
    s_, se_, pp = metareg(tab["coef_10x"], tab["se_10x"], tab["rain"])
    print(f"  {lab}: slope per SD of state rainfall {s_:+.2f} (SE {se_:.2f}) p {pp:.3g}")
eco_t = pd.read_csv(G["OUT"] / "results" / "posthoc_eco_name.csv")
eco_t = eco_t[eco_t["eligible"]].copy()
eco_t["rain"] = eco_t["unit"].map(w.groupby("ECO_NAME")["rain_mm"].mean())
s_, se_, pp = metareg(eco_t["coef_10x"], eco_t["se_10x"], eco_t["rain"])
print(f"  18 ecoregions: slope per SD of rainfall {s_:+.2f} (SE {se_:.2f}) p {pp:.3g}")
print("  state mean rainfall (mm):", {res.loc[c, "state"]: int(v) for c, v in st_rain.items() if c in res.index})

# background points and state labels for the map (copied out; the map keeps 0.5 degree cells)
bg = pd.DataFrame({"a": (w["la"] * 10).round() / 10, "b": (w["lo"] * 10).round() / 10}).drop_duplicates()
print("BG_START")
print(";".join(f"{a:.1f},{b:.1f}" for a, b in bg.itertuples(index=False)))
print("BG_END")
lab = w.groupby("state")[["la", "lo"]].median()
print("LAB_START")
print(";".join(f"{G['STATES'][int(c)]},{r.la:.2f},{r.lo:.2f}" for c, r in lab.iterrows() if int(c) in res.index))
print("LAB_END")
