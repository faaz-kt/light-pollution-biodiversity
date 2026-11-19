# %% [markdown]
# # India: post-hoc look at the state results (EXPLORATORY, after the final tests)
#
# Listed in PLAN_india.md "Changes" (18 Nov 2026, ~19:35 IST) before being run. Nothing here can confirm anything:
# the tests were already run once (results/india_final_tests_summary.md). This script only asks how solid the P1
# verdict is and which leads a new, written-down test should look at.
#
# Reads the two small state tables copied from Drive (results/india_explore_states.csv,
# results/india_holdout_states.csv) and writes results/india_posthoc_states.md and results/india_states_forest.png.

# %%
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
RES = HERE / "results"
SEEN = [16, 17]
TAU_MIN = 2.0
FACTORS = ["F1_built_m2_per_person", "F2_no2_umol_m2", "F3_tree_share", "F4_median_observers"]

explore = pd.read_csv(RES / "india_explore_states.csv")
holdout = pd.read_csv(RES / "india_holdout_states.csv")
allst = pd.concat([explore, holdout], ignore_index=True)
elig = allst[allst["eligible"]].copy()
fresh = elig[~elig["state_code"].isin(SEEN)].copy()


def dl(y, se):
    """DerSimonian-Laird: Q, p, I2, tau, random-effects mean (same maths as india_final_tests.py)."""
    y, se = np.asarray(y, float), np.asarray(se, float)
    w = 1 / se ** 2
    k = len(y)
    m = np.sum(w * y) / np.sum(w)
    Q = float(np.sum(w * (y - m) ** 2))
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (Q - (k - 1)) / C)
    ws = 1 / (se ** 2 + tau2)
    mu = np.sum(ws * y) / np.sum(ws)
    return {"k": k, "Q": Q, "p": float(stats.chi2.sf(Q, k - 1)), "I2": max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0,
            "tau": float(np.sqrt(tau2)), "mean": float(mu), "mean_se": float(np.sqrt(1 / np.sum(ws)))}


def metareg(y, se, x):
    """Random-effects meta-regression, DL residual tau2, Knapp-Hartung (as in india_final_tests.py)."""
    y, se, x = np.asarray(y, float), np.asarray(se, float), np.asarray(x, float)
    k = len(y)
    X = np.column_stack([np.ones(k), (x - x.mean()) / x.std(ddof=1)])
    v = se ** 2
    W = np.diag(1 / v)
    A = np.linalg.inv(X.T @ W @ X)
    b = A @ X.T @ W @ y
    QE = float(np.sum((y - X @ b) ** 2 / v))
    P = W - W @ X @ A @ X.T @ W
    tau2 = max(0.0, (QE - (k - 2)) / np.trace(P))
    Ws = np.diag(1 / (v + tau2))
    As = np.linalg.inv(X.T @ Ws @ X)
    bs = As @ X.T @ Ws @ y
    s2 = float(np.sum((y - X @ bs) ** 2 / (v + tau2)) / (k - 2))
    se_b = float(np.sqrt(s2 * As[1, 1]))
    t = bs[1] / se_b
    return {"k": k, "slope": float(bs[1]), "se": se_b, "p": float(2 * stats.t.sf(abs(t), k - 2))}


def verdict(r):
    return "differ meaningfully" if (r["p"] < 0.05 and r["I2"] >= 0.5 and r["tau"] >= TAU_MIN) else "not meaningful"


out = ["# India: post-hoc look at the state results (EXPLORATORY)", "",
       "Run after the final tests (18 Nov 2026). Listed in the plan before running. Cannot confirm anything.", ""]

# %% (0) check: the final P1 number again, from the copied tables
p1 = dl(fresh["coef_10x"], fresh["se_10x"])
out += [f"Check: P1 recomputed from the copied tables: Q = {p1['Q']:.1f}, p = {p1['p']:.3g}, I2 = {p1['I2']:.0%}, "
        f"tau = {p1['tau']:.2f}, mean {p1['mean']:+.2f} (final run said Q 35.7, p 0.000365, I2 66%, tau 3.34, "
        f"mean -3.55).", ""]

# %% (a) all states
out += ["## (a) Every state (light effect per 10x brighter, after habitat; species per 200 records)", "",
        "| State | Half | Eligible | Squares | Blocks | Across space | 95% range | Over time | 95% range |",
        "|---|---|---|---|---|---|---|---|---|"]
for r in allst.sort_values("coef_10x").itertuples():
    out.append(f"| {r.state} | {r.half} | {'yes' if r.eligible else 'no'} | {r.n_squares} | {r.n_blocks} | "
               f"{r.coef_10x:+.1f} | {r.low95_10x:+.1f} to {r.high95_10x:+.1f} | {r.time_coef_10x:+.1f} | "
               f"{r.time_coef_10x - 1.96 * r.time_se_10x:+.1f} to {r.time_coef_10x + 1.96 * r.time_se_10x:+.1f} |")
neg = (elig["high95_10x"] < 0).sum()
pos = (elig["low95_10x"] > 0).sum()
out += ["", f"Of {len(elig)} eligible states: {neg} clearly negative (95% range below 0), {pos} clearly positive, "
        f"{len(elig) - neg - pos} unclear.", ""]

# %% (b) robustness of P1
out += ["## (b) How solid is 'states differ meaningfully'?", ""]
rows = []
for code in fresh["state_code"]:
    sub = fresh[fresh["state_code"] != code]
    r = dl(sub["coef_10x"], sub["se_10x"])
    rows.append((fresh.loc[fresh["state_code"] == code, "state"].iloc[0], r))
out.append("Leaving out one state at a time (13 runs):")
taus = [r["tau"] for _, r in rows]
i2s = [r["I2"] for _, r in rows]
n_ok = sum(verdict(r) == "differ meaningfully" for _, r in rows)
out.append(f"- verdict holds in {n_ok} of {len(rows)}; tau ranges {min(taus):.2f} to {max(taus):.2f}, "
           f"I2 {min(i2s):.0%} to {max(i2s):.0%}")
for name, r in rows:
    if verdict(r) != "differ meaningfully":
        out.append(f"- without {name}: tau {r['tau']:.2f}, I2 {r['I2']:.0%}, p {r['p']:.3g} -> {verdict(r)}")
r_sd = dl(fresh["coef_sd"], fresh["se_sd"])
out.append(f"- per SD of light instead of per 10x: tau {r_sd['tau']:.2f} species per SD, I2 {r_sd['I2']:.0%}, "
           f"p {r_sd['p']:.3g} (the 2-species bar was set for per-10x units)")
r15 = dl(elig["coef_10x"], elig["se_10x"])
out.append(f"- adding Karnataka and Kerala (15 states): tau {r15['tau']:.2f}, I2 {r15['I2']:.0%}, p {r15['p']:.3g}, "
           f"mean {r15['mean']:+.2f} (SE {r15['mean_se']:.2f})")
allfresh = allst[~allst["state_code"].isin(SEEN)].dropna(subset=["coef_10x"])
r19 = dl(allfresh["coef_10x"], allfresh["se_10x"])
out.append(f"- adding the 6 states that failed the size rules (19 states; their error bars are less trustworthy): "
           f"tau {r19['tau']:.2f}, I2 {r19['I2']:.0%}, p {r19['p']:.3g}")
ex5 = fresh[fresh["half"] == "explore"]
ho8 = fresh[fresh["half"] == "holdout"]
r_ex, r_ho = dl(ex5["coef_10x"], ex5["se_10x"]), dl(ho8["coef_10x"], ho8["se_10x"])
out.append(f"- each half on its own: explore (5 states) tau {r_ex['tau']:.2f}, I2 {r_ex['I2']:.0%}, "
           f"mean {r_ex['mean']:+.2f}; hold-out (8) tau {r_ho['tau']:.2f}, I2 {r_ho['I2']:.0%}, mean {r_ho['mean']:+.2f}")
out.append("")

# %% (c) space vs time
ok = elig.dropna(subset=["time_coef_10x"])
rho, prho = stats.spearmanr(ok["coef_10x"], ok["time_coef_10x"])
rt = dl(ok["time_coef_10x"], ok["time_se_10x"])
out += ["## (c) Do states with a stronger across-space effect also show a stronger over-time effect?", "",
        f"Spearman rho between the two, over {len(ok)} eligible states: {rho:+.2f} (p {prho:.2f}). "
        f"Over-time average across states: {rt['mean']:+.2f} (SE {rt['mean_se']:.2f}) species per visit per 10x "
        f"brighter. (If light itself removed species, both measures should be negative and move together.)", ""]

# %% (d) factors over all 15 eligible states
out += ["## (d) The four factors over all 15 eligible states (each alone; no correction; exploratory)", ""]
for f in FACTORS:
    o = elig.dropna(subset=[f])
    r = metareg(o["coef_10x"], o["se_10x"], o[f])
    out.append(f"- {f}: slope {r['slope']:+.2f} species per 10x per SD of the factor (SE {r['se']:.2f}), "
               f"p {r['p']:.3g}, {r['k']} states")
cor = elig[FACTORS].corr(method="spearman").round(2)
out += ["", "How the factors move together (Spearman, 15 states):", "", "```", cor.to_string(), "```", ""]

(RES / "india_posthoc_states.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))

# %% forest plot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

show = elig.sort_values("coef_10x").reset_index(drop=True)
colors = {"explore": "#2b6cb0", "holdout": "#c05621", "seen": "#718096"}
fig, ax = plt.subplots(figsize=(7.5, 6.2))
for i, r in show.iterrows():
    ax.errorbar(r["coef_10x"], i, xerr=1.96 * r["se_10x"], fmt="o", color=colors[r["half"]], capsize=2, lw=1.4)
ax.axvline(0, color="black", lw=0.8)
ax.axvline(p1["mean"], color="#2f855a", lw=1, ls="--")
ax.set_yticks(range(len(show)), [f"{s} ({h})" for s, h in zip(show["state"], show["half"])])
ax.set_xlabel("Change in species (per 200 records) when a square is 10x brighter,\nafter buildings, trees, farmland, water, elevation (95% range)")
ax.set_title("Night light and bird species, state by state (India, 2015-2025)")
ax.set_ylim(-1.3, len(show) - 0.5)
ax.text(p1["mean"], -1.0, f" average of the 13 fresh states: {p1['mean']:+.1f}", color="#2f855a", fontsize=8,
        va="center")
fig.tight_layout()
fig.savefig(RES / "india_states_forest.png", dpi=150)
print("saved", RES / "india_states_forest.png")
