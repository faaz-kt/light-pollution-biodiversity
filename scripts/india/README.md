# India extension: how to run it

Follows the locked plan [`../../PLAN_india.md`](../../PLAN_india.md) (locked 18 Nov 2026, 12:47 IST).
Data folder: Google Drive `My Drive/bigdata/lpb_india/` (one sub-folder per run).

| # | What | Script / setting | Must give |
|---|---|---|---|
| 1 | Reproduction check, Karnataka (original download, DOI 10.15468/dl.t3hgj6, zip in `bigdata/lpb/raw/` or `bigdata/lpb/`) | `india_pipeline.py`, `RUN = "repro_karnataka"` | `PASSED`: -0.23 species per SD, 1,020 squares |
| 2 | Reproduction check, Kerala (DOI 10.15468/dl.tzdphq, zip in `bigdata/lpb_kerala/raw/`) | `RUN = "repro_kerala"` | `PASSED`: -7.40 per SD, 1,054 squares |
| 3 | Faaz requests the India download on gbif.org (below), then pulls it into Drive | `../step1b_gbif_download.py`, `REGION = "india"`, `KNOWN_KEY = "<key>"` | zip in `bigdata/lpb_india/raw/` |
| 4 | The real run | `india_pipeline.py`, `RUN = "india"` | `explore_states.csv` (shown), `SEALED_holdout_states.csv` (not opened) |
| 5 | Explore the explore half freely; write any new idea into the plan's Changes, with the date | (look at `explore_states.csv`, `explore_states.png`) | |
| 6 | Freeze, then the final tests, once | `india_final_tests.py`, `EXPLORE_FROZEN = True`, `FROZEN_NOTE = "..."` | `FINAL_tests_summary.md` |

Only go on from step 2 if steps 1 and 2 both say `PASSED`.

**Status, 18 Nov 2026:** steps 1-4 done (both reproduction checks `PASSED`; India download 0014194-261110092616502,
DOI 10.15468/dl.nhjj65; the real run finished in about 1 h 20 min on Colab: reading the zip ~12 min, squares ~2 min,
Earth Engine maps ~1 h, mostly the 7 NO2 years). Steps 5 and 6 done too: explore half frozen 18 Nov 18:19 IST, final
tests run once at 18:22 IST (`../../results/india_final_tests_summary.md`). Tip: when a Colab cell finishes with a plot, its text output becomes hard to read from
outside the notebook; print `results/explore_states.csv` in a new cell instead (never the `SEALED_` file).

**After the tests (exploratory, 18 Nov ~20:00 IST):** `india_posthoc_states.py` (runs on the laptop from the two
small state tables in `results/`) and `india_posthoc_squares.py` (Colab: loads the saved run, then square-level
models and the light effect by RESOLVE ecoregion). The final tests must not be run again: they were designed to
run once, and `FINAL_tests.csv` in Drive makes the script refuse.

**The India download (step 3), on gbif.org > Occurrences**, the same filters as the Karnataka and Kerala downloads:
Administrative areas (GADM) = India (`IND`); Scientific name = Aves (Catalogue of Life checklist, as before);
Year 2015-2025; Has coordinate = yes; Has geospatial issue = no. Then Download > Simple. Expect about 50 million
records and a zip of about 5 GB. Send the download key; `step1b` with `KNOWN_KEY` waits for it and saves it to Drive.

**What each part of `india_pipeline.py` does**
- **A** reads the zip in pieces of 1 million rows with step 2's cleaning, and stores every record as small whole
  numbers (square, date, observer, species, state). That is what lets 50 million records fit in Colab's memory.
- **B** makes the square tables: step 4's records, visits, observers and rarefied species; step 6's species per
  visit per year; and each square's state (the state named in most of its records).
- **C** gets the Earth Engine layers in tiles (5 degrees, 2.5 for the 30 m water map), saving each tile as it
  arrives, splitting a tile into four if Earth Engine says it is too big or slow, and running 4 requests at once.
  New layers for the plan: GHSL population 2020 and Sentinel-5P NO2 (2019-2025).
- **D** fits step 5's model and step 6's over-time model in every state, applies the eligibility rules, measures
  F1-F4, and writes the two halves to separate files. It prints and plots the explore half only.

Every part saves its output and is skipped on a re-run (set `REDO = {"B"}` etc. to redo one). Earth Engine tiles
stay cached in `earth_engine/`; delete that folder to fetch them again.

**How the code was checked before any real run (18 Nov 2026, in Claude's workspace)**
- On fake Karnataka- and Kerala-style downloads, the OLD steps 2, 4, 5, 6 and the NEW pipeline gave identical
  results to 12 decimal places: every square's records, visits, observers and rarefied species, the step 5 light
  coefficient and its error bar, and the step 6 over-time coefficient. (The old steps were run saving exact
  values, as parquet does in Colab.)
- Fake Earth Engine values placed at each pixel's centre came back to the right squares (checks the map
  orientation), and forcing every tile to be split gave the same values (differences around 1e-13).
- The meta-analysis maths reproduces the published result for the classic BCG vaccine trials
  (Q = 152.23, tau-squared = 0.3088, I-squared = 92.12%).
- On a fake 21-state India download: state-name spellings (Orissa, Uttaranchal, NCT of Delhi, Andaman &
  Nicobar) are matched, only the explore half is printed, and the final tests refuse to run before the freeze
  and refuse a second run.
- **Not yet done (Faaz's step 3, separate session):** fake worlds with planted differences between states, to
  show the tests find a real pattern and do not invent one.

**Planted-world tests (plan step 3, 18 Nov 2026, ~13:45 IST)** - `tests/run_planted_worlds.sh`. Fake Indias
(21 states, ~2.6-3 M records each) with a known truth, run through the real pipeline and the real final tests
(real thresholds: 150 squares, 10 blocks; Delhi and Goa dropped as expected, leaving 17 fresh states, 7 hold-out):

| Planted truth | P1 verdict | P2 verdict | Right? |
|---|---|---|---|
| No light effect anywhere | no meaningful differences (Q p = 0.95, tau 0) | nothing supported | yes |
| Effect grows with NO2, small (tau ~0.9) | real but below the 2-species bar (Q p = 0.0008, I2 60%) | **F2 NO2 supported** (Holm p = 0.045), nothing else | yes |
| Random differences, small (tau ~1.3) | real but below the bar (Q p = 1e-8, I2 77%) | nothing supported | yes |
| Effect grows with NO2, strong (tau 5.2) | **states differ meaningfully** | **F2 NO2 supported** (Holm p = 0.001), nothing else | yes |
| Random differences, strong (tau 6.0) | **states differ meaningfully** | nothing supported | yes |

Lesson from building the fake worlds: a light effect that lowers EVERY species' chance of being recorded by the
same amount is invisible to rarefied species (equal-records comparisons cancel it). Light must change WHICH
species are recorded. The worlds therefore plant the effect on a light-sensitive half of the species.
