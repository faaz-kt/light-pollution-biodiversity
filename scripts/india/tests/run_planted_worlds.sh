#!/usr/bin/env bash
# Planted-world tests (plan step 3): fake Indias with a known truth, run through the real pipeline and final tests.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); S=$HERE/..; W=${1:-/tmp/lpb_worlds}
rm -rf "$W" && mkdir -p "$W" && cd "$W" && cp "$HERE"/*.py .
export MPLBACKEND=Agg LPB_FAKE_EE=$W/fake_ee_india.py PYTHONPATH=$W
sed -e 's/^RUN = "repro_karnataka"/RUN = "india"/' $S/india_pipeline.py > pipe.py
sed -e 's/^EXPLORE_FROZEN = False/EXPLORE_FROZEN = True/' $S/india_final_tests.py > final.py
for spec in "null 8" "no2 8" "random 8" "no2 20" "random 20"; do
  set -- $spec; H=$W/h_$1_$2; mkdir -p $H/bigdata/lpb_india/raw
  python3 make_world.py $H/bigdata/lpb_india/raw/gbif.zip $1 7 $2 > /dev/null
  HOME=$H python3 -W ignore pipe.py > $H.log 2>&1
  echo "--- world $1, strength $2"; HOME=$H python3 -W ignore final.py | grep -E "Verdict|-> \*\*SUPPORTED"
done
