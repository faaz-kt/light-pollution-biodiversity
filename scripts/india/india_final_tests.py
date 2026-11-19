# %% [markdown]
# # India: the final tests (P1 and P2), run ONCE
#
# This is step 3 of the locked plan `PLAN_india.md`: run only after the explore half has been looked at and
# **frozen** (any new idea written into the plan's "Changes" with its date). It opens the sealed hold-out file,
# runs the tests exactly as the plan says, saves the result with the time, and refuses to run a second time.
#
# - **P1, do the states differ?** All fresh eligible states (not Karnataka or Kerala): Cochran's Q, I-squared and
#   tau (DerSimonian-Laird) on the light effect per 10x brighter. "Differ meaningfully" = Q p < 0.05 and
#   I-squared >= 50% and tau >= 2 species per 10x brighter.
# - **P2, does a factor line up?** Hold-out eligible states only, one factor at a time: random-effects
#   meta-regression of the light effect on the standardised factor, Knapp-Hartung p-values, Holm correction over
#   the factors tested. "Supported" = Holm p < 0.05 and, for F1 and F2, a negative slope (stronger harm).
# - **Secondary (reported, not decisive):** P1 on the over-time model; the explore half's own factor slopes.

# %%
# ---------------------------------------------------------------- SETTINGS --
EXPLORE_FROZEN = False        # set to True only after the explore half is frozen (plan, Order step 3)
FROZEN_NOTE = ""              # e.g. "Frozen 2 Dec 2026 15:10 IST, no extra factors" (copied into the result)
EXTRA_FACTORS = {}            # extra factors logged in the plan before freezing: {"column": predicted sign or None}

FACTORS = {"F1_built_m2_per_person": -1,    # plan: more built-up area per person -> more negative (stronger harm)
           "F2_no2_umol_m2": -1,            # plan: more NO2 -> more negative
           "F3_tree_share": None,           # plan: two-sided
           "F4_median_observers": None}     # plan: two-sided
TAU_MIN = 2.0                 # plan: species per 10x brighter
SEEN = [16, 17]

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    ROOT = Path("/content/drive/MyDrive/bigdata")
else:
    _options = [Path.home() / "bigdata", Path.home() / "Downloads" / "bigdata"]
    ROOT = next((p for p in _options if p.exists()), _options[0])
RESULTS = ROOT / "lpb_india" / "india" / "results"
FINAL = RESULTS / "FINAL_tests.csv"
SUMMARY = RESULTS / "FINAL_tests_summary.md"

if not EXPLORE_FROZEN:
    raise SystemExit("Not run: set EXPLORE_FROZEN = True only after the explore half is frozen (see the plan).")
if FINAL.exists() or SUMMARY.exists():
    raise SystemExit(f"Not run: the final tests were already run once ({FINAL.name} exists). The plan allows one run.")

explore = pd.read_csv(RESULTS / "explore_states.csv")
holdout = pd.read_csv(RESULTS / "SEALED_holdout_states.csv")
FACTORS.update(EXTRA_FACTORS)

# %%
def dersimonian_laird(y, se):
    """Heterogeneity between estimates y with standard errors se: Q, its p, I-squared, tau (DL)."""
    y, se = np.asarray(y, float), np.asarray(se, float)
    w = 1 / se ** 2
    k = len(y)
    mean_fixed = np.sum(w * y) / np.sum(w)
    Q = float(np.sum(w * (y - mean_fixed) ** 2))
    df = k - 1
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (Q - df) / C)
    I2 = max(0.0, (Q - df) / Q) if Q > 0 else 0.0
    ws = 1 / (se ** 2 + tau2)
    mu = np.sum(ws * y) / np.sum(ws)
    return {"k": k, "Q": Q, "df": df, "p_Q": float(stats.chi2.sf(Q, df)), "I2": I2, "tau2": tau2,
            "tau": float(np.sqrt(tau2)), "mean_effect": float(mu), "mean_effect_se": float(np.sqrt(1 / np.sum(ws)))}


def meta_regression(y, se, x):
    """Random-effects meta-regression of y on standardised x: method-of-moments (DL) residual tau-squared,
    then weighted least squares with weights 1/(se^2 + tau^2) and Knapp-Hartung standard errors (t, k-2 df)."""
    y, se, x = np.asarray(y, float), np.asarray(se, float), np.asarray(x, float)
    k = len(y)
    X = np.column_stack([np.ones(k), (x - x.mean()) / x.std(ddof=1)])
    p = X.shape[1]
    v = se ** 2
    W = np.diag(1 / v)
    A = np.linalg.inv(X.T @ W @ X)
    b = A @ X.T @ W @ y
    QE = float(np.sum((y - X @ b) ** 2 / v))
    P = W - W @ X @ A @ X.T @ W
    tau2 = max(0.0, (QE - (k - p)) / np.trace(P))
    Ws = np.diag(1 / (v + tau2))
    As = np.linalg.inv(X.T @ Ws @ X)
    bs = As @ X.T @ Ws @ y
    s2 = float(np.sum((y - X @ bs) ** 2 / (v + tau2)) / (k - p))
    se_b = np.sqrt(np.diag(s2 * As))
    t = bs[1] / se_b[1]
    return {"k": k, "slope": float(bs[1]), "slope_se": float(se_b[1]), "t": float(t), "df": k - p,
            "p": float(2 * stats.t.sf(abs(t), k - p)), "tau2_residual": tau2}


def holm(pvals):
    """Holm-adjusted p-values."""
    pvals = np.asarray(pvals, float)
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


# %%
now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %Y %H:%M IST")
fresh = pd.concat([explore[(explore["half"] == "explore") & explore["eligible"]],
                   holdout[holdout["eligible"]]], ignore_index=True)
fresh = fresh[~fresh["state_code"].isin(SEEN)]
hold = holdout[holdout["eligible"]].copy()
lines = [f"# Final tests (plan P1, P2), run {now}", "", f"Freeze note: {FROZEN_NOTE or '(none given)'}", ""]
rows = []

# P1
p1 = dersimonian_laird(fresh["coef_10x"], fresh["se_10x"])
differ = p1["p_Q"] < 0.05 and p1["I2"] >= 0.5 and p1["tau"] >= TAU_MIN
rows.append({"test": "P1 across space (main)", **p1, "verdict": "states differ meaningfully" if differ
             else "no evidence of meaningful differences"})
lines += [f"## P1: do the states differ? ({p1['k']} fresh states: {', '.join(fresh['state'])})",
          f"Q = {p1['Q']:.1f} on {p1['df']} df, p = {p1['p_Q']:.3g}; I-squared = {p1['I2']:.0%}; "
          f"tau = {p1['tau']:.2f} species per 10x brighter (needs >= {TAU_MIN}); "
          f"average effect {p1['mean_effect']:+.2f} (SE {p1['mean_effect_se']:.2f}).",
          f"**Verdict: {rows[-1]['verdict']}.**", ""]

# P1 secondary: over time
t_ok = fresh.dropna(subset=["time_coef_10x", "time_se_10x"])
if len(t_ok) >= 3:
    p1t = dersimonian_laird(t_ok["time_coef_10x"], t_ok["time_se_10x"])
    rows.append({"test": "P1 over time (secondary)", **p1t, "verdict": "reported only"})
    lines += [f"Secondary, over time ({p1t['k']} states): Q = {p1t['Q']:.1f}, p = {p1t['p_Q']:.3g}, "
              f"I-squared = {p1t['I2']:.0%}, tau = {p1t['tau']:.2f}.", ""]

# P2 on the hold-out half
lines += [f"## P2: does a factor line up? (hold-out half, {len(hold)} states: {', '.join(hold['state'])})"]
p2 = []
for f, sign in FACTORS.items():
    ok = hold.dropna(subset=["coef_10x", "se_10x", f])
    if len(ok) < 4 or ok[f].std() == 0:
        p2.append({"factor": f, "k": len(ok), "predicted_sign": sign, "note": "not testable (too few states)"})
        continue
    p2.append({"factor": f, "predicted_sign": sign, **meta_regression(ok["coef_10x"], ok["se_10x"], ok[f])})
p2 = pd.DataFrame(p2)
tested = p2["p"].notna() if "p" in p2 else pd.Series(False, index=p2.index)
p2["p_holm"] = np.nan
if tested.any():
    p2.loc[tested, "p_holm"] = holm(p2.loc[tested, "p"])
for r in p2.itertuples():
    if pd.isna(getattr(r, "p_holm", np.nan)):
        verdict = "not testable"
    else:
        sign_ok = r.predicted_sign is None or pd.isna(r.predicted_sign) or np.sign(r.slope) == r.predicted_sign
        verdict = "SUPPORTED" if (r.p_holm < 0.05 and sign_ok) else "unsupported (not disproved)"
        lines.append(f"- {r.factor}: slope {r.slope:+.2f} species per 10x per SD of the factor "
                     f"(SE {r.slope_se:.2f}, t = {r.t:.2f} on {r.df} df), p = {r.p:.3g}, Holm p = {r.p_holm:.3g}"
                     f" -> **{verdict}**")
    rows.append({"test": f"P2 {r.factor}", "verdict": verdict, **{k: v for k, v in r._asdict().items() if k != 'Index'}})

# Secondary: the explore half's own slopes (including Karnataka and Kerala)
ex = explore[explore["eligible"]]
lines += ["", f"Secondary (explore half, {len(ex)} states incl. Karnataka and Kerala; not decisive):"]
for f in FACTORS:
    ok = ex.dropna(subset=["coef_10x", "se_10x", f])
    if len(ok) >= 4 and ok[f].std() > 0:
        r = meta_regression(ok["coef_10x"], ok["se_10x"], ok[f])
        rows.append({"test": f"explore-half slope {f}", "verdict": "reported only", **r})
        lines.append(f"- {f}: slope {r['slope']:+.2f} (SE {r['slope_se']:.2f}), p = {r['p']:.3g}")

pd.DataFrame(rows).to_csv(FINAL, index=False)
SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nSaved {FINAL.name} and {SUMMARY.name} in {RESULTS}. Copy the verdicts into the plan's Changes log.")
