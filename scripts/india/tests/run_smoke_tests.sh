#!/usr/bin/env bash
# Smoke tests for the India pipeline (run in Claude's Linux workspace, not needed on the laptop).
# 1) old steps 2,4,5,6 vs new pipeline on fake Karnataka and Kerala downloads (must be IDENTICAL)
# 2) fake 21-state India download: explore/sealed split, final-tests locks.
# The old steps are patched to save exact values (pickle), as parquet does in Colab.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); S=$HERE/../..; W=${1:-/tmp/lpb_india_smoke}
rm -rf "$W" && mkdir -p "$W/oldpatched" && cd "$W" && cp "$HERE"/*.py .
export MPLBACKEND=Agg LPB_FAKE_EE=$W/fake_ee.py PYTHONPATH=$W
python3 - "$S" <<'PY'
import sys; from pathlib import Path
S = Path(sys.argv[1]); O = Path("oldpatched")
r = {"step2_slim_table": [('EXT = ".csv.gz"', 'EXT = ".pkl"'), ("kept.to_csv(part_file, index=False)", "kept.to_pickle(part_file)"),
                          ('pd.read_parquet(p) if EXT == ".parquet" else pd.read_csv(p)', 'pd.read_parquet(p) if EXT == ".parquet" else pd.read_pickle(p)')],
     "step4_join_birds_lights": [("b = pd.read_csv(part, usecols=COLUMNS)", "b = pd.read_pickle(part)[COLUMNS]")],
     "step5_habitat_model": [], "step6_time_and_traits": [("pd.read_csv(p, usecols=COLS)", "pd.read_pickle(p)[COLS]")]}
for name, subs in r.items():
    t = (S / f"{name}.py").read_text()
    for a, b in subs: t = t.replace(a, b)
    for reg in ("karnataka", "kerala"):
        (O / f"{name}_{reg}.py").write_text(t.replace('REGION = "karnataka"', f'REGION = "{reg}"'))
PY
for reg in karnataka kerala; do
  H=$W/home_$reg; F=$([ $reg = kerala ] && echo lpb_kerala || echo lpb); Z=$([ $reg = kerala ] && echo gbif_test.zip || echo 0008405-261110092616502.zip)
  mkdir -p $H/bigdata/$F/raw && python3 make_download.py $H/bigdata/$F/raw/$Z $reg 11 && python3 make_old_files.py $H/bigdata/$F/clean $reg
  for s in step2_slim_table step4_join_birds_lights step5_habitat_model step6_time_and_traits; do HOME=$H python3 -W ignore oldpatched/${s}_$reg.py > old_${s}_$reg.log 2>&1; done
  sed -e "s/^RUN = \"repro_karnataka\"/RUN = \"repro_$reg\"/" -e 's/^CHUNK_ROWS = 1_000_000/CHUNK_ROWS = 50_000/' $S/india/india_pipeline.py > new_$reg.py
  HOME=$H FAKE_EE_MAX_CELLS=2000 python3 -W ignore new_$reg.py > new_$reg.log 2>&1
  python3 - <<PY
import pandas as pd
oc = pd.read_csv("$H/bigdata/$F/clean/step5_model_coefficients.csv", index_col=0).loc["light"]
o6 = pd.read_csv("$H/bigdata/$F/clean/step6_results.csv").iloc[0]
n_old = len(pd.read_csv("$H/bigdata/$F/clean/step5_analysis_table.csv"))
nc = pd.read_csv("$H/bigdata/lpb_india/repro_$reg/results/reproduction_check.csv").iloc[0]
ok = abs(oc['coef'] - nc['coef_sd']) < 1e-9 and abs(oc['se'] - nc['se_sd']) < 1e-9 and n_old == nc['n_squares'] and abs(o6['coef'] - nc['time_coef_10x']) < 1e-9
print("$reg old vs new:", "IDENTICAL" if ok else "DIFFERENT")
PY
done
H=$W/home_india; mkdir -p $H/bigdata/lpb_india/raw && python3 make_india_download.py $H/bigdata/lpb_india/raw/gbif_india_test.zip 3
sed -e 's/^RUN = "repro_karnataka"/RUN = "india"/' -e 's/^MIN_SQUARES, MIN_BLOCKS = 150, 10/MIN_SQUARES, MIN_BLOCKS = 15, 3/' $S/india/india_pipeline.py > india.py
HOME=$H python3 -W ignore india.py > india.log 2>&1 && echo "india run: ok"
sed -e 's/^EXPLORE_FROZEN = False/EXPLORE_FROZEN = True/' $S/india/india_final_tests.py > final.py
HOME=$H python3 -W ignore final.py | grep -E "Verdict"; HOME=$H python3 -W ignore final.py | tail -1
