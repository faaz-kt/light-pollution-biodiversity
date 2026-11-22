# Night lights and birds in India (started in Karnataka)

**Question:** does artificial light at night change which birds are found where, and when, in Karnataka, India?

Faaz Abdulla Kizhisseri, BSc (Research) student, Indian Institute of Science, Bengaluru. Semester 1 project (2026).

## Results so far

| Step | What | Result |
|---|---|---|
| 2 | Clean 7.8 million bird records | 7,814,812 kept, 576 species, 26,139 observers |
| 3 | Night lights per 5.5 km square, 2015-2025 | Karnataka's average night brightness roughly doubled (0.66 → 1.30 nW/sr/cm²) |
| 4 | Birds vs light at equal birdwatching effort | Brighter squares have ~13% fewer species (Spearman rho −0.30, 1,020 squares) |
| 5 | Add habitat (buildings, farmland, trees, water, elevation) | The pattern is explained by habitat, mainly buildings and farmland. Light adds nothing (−0.23 species per SD, 95% range −2.20 to +1.75), but light and buildings are too tangled (rho 0.86) to rule out a modest effect |
| 6 | Change over time within squares (2015-2025) + species traits (AVONET) | **Night birds** (owls, nightjars, night herons; 1.1% of all detections) are a smaller share of what birdwatchers record where it is brighter: −0.48 percentage points per 10× brighter across space (95% range −0.85 to −0.11), and the same direction over time within squares (−0.41, −0.85 to +0.04). **Migrants** (AVONET label, 14% of detections; see 7b-7c) are a *larger* share where and when it gets brighter (over time +3.4, +0.8 to +6.0; across space +1.2, +0.2 to +2.3). Insect-eaters and overall species per visit: no clear change. Exploratory: 8 tests, so these need confirming |
| 7 | Fix species-name matching; split migrants into waterbirds vs landbirds; winter-only check | All 576 species now have traits (synonym table). Of 20 tests, 3 survive correction for multiple testing: migrants are a larger share **among waterbirds** where it got brighter over time (+3.9 points per 10×, 95% range +1.8 to +6.0; winter only +5.1) and **among landbirds** in brighter places (+1.5, +0.4 to +2.6). Waterbirds overall don't rise with light, so new lakes don't explain it. Night birds: same direction as step 6 but no longer convincing after correction |
| 7b | Are AVONET "migrants" migrants *here*? (monsoon vs winter reporting rates) | **No, half of them aren't.** 49% of "migrant" records come from 22 species that live in Karnataka all year (Black Kite alone: 162,000 records; also Shikra, Little Swift, Pied Bushchat). AVONET scores whole species worldwide |
| 7c | Redo the migrant tests with the local label (winter visitors, winter visits only) | Step 7's waterbird result **mostly disappears** (+1.9 over time, 95% range −4.1 to +7.9): it came from resident herons that AVONET calls migrants. **True winter-visitor landbirds** (Barn Swallow, Ashy Drongo, Brown Shrike, leaf warblers…) are a larger share where and when it is brighter (+4.1 over time, −0.0 to +8.2; +1.4 across space, +0.04 to +2.7), but not after correcting for 8 tests (q 0.14): a lead, not a finding. Year-round "migrants" (Black Kite, Shikra…) are more common in brighter places (+1.0, +0.5 to +1.6, q 0.003) but not clearly over time, so city habitat could explain it |
| 8 | Night vs day migrants (test plan fixed in advance: [`PLAN_step8_kerala.md`](PLAN_step8_kerala.md)) | Karnataka first look: **inconclusive** by the plan's rule. Across space, brighter places have relatively more night migrants (night share of migrants +7.3 points per 10x brighter, 95% range +2.8 to +11.9), as predicted, with no change in day migrants. But over time, as squares got brighter, day migrants rose (+2.1, +0.9 to +3.4) and the night share fell (−9.2, −19.0 to +0.6), the opposite of the prediction. A pattern that holds across space but not over time is what fixed habitat differences produce (night migrants here are mostly garden and woodland insect-eaters). Kerala, with fresh data, is the real test |
| 8 (Kerala) | The same test, run once on fresh data from Kerala ([DOI 10.15468/dl.tzdphq](https://doi.org/10.15468/dl.tzdphq); 5.96 M records, 563 species, all matched to traits) | **Inconclusive again, and the pattern flips.** Night share of migrants: +2.8 over time (95% range −3.8 to +9.5), −8.9 across space (−18.2 to +0.4). Across space, Kerala goes the opposite way to Karnataka in every night-migrant test. So the night-migrant idea is **not supported**: whatever drives these patterns differs between states (habitat, coast, where people birdwatch), which is what you expect from confounding, not from light |
| 5 (Kerala, unplanned) | Same habitat model on Kerala | In Kerala, brighter squares have clearly fewer species even after habitat (−7.4 species per SD of light, 95% range −10.1 to −4.7; Karnataka: −0.2). Not part of the plan, so exploratory. First suspect: the coastline (coastal squares are bright, crowded, and part sea, so they hold less land for birds) |
| 9 | Is that just the coastline? Land fraction of every square (Hansen data mask) as a control, and inland squares only | **No.** Kerala: −7.2 with land as a control (95% range −9.9 to −4.5), −7.9 using only squares that are at least 95% land (−11.0 to −4.8). Karnataka stays near zero (−0.4, −0.5). Untested explanations left: night lights may measure Kerala's spread-out towns better than the building map does (so "light" stands in for urbanisation), or bright squares get more casual birders. Exploratory |
| India (planned tests done) | Does the light-bird link differ between states, and why? Plan written and **locked before any data** ([`PLAN_india.md`](PLAN_india.md), 18 Nov 2026, 12:47 IST): 21 states, 9 held out at random, four pre-chosen explanations (built-up area per person, NO2 air pollution, tree cover, birdwatching effort) | Code written and checked ([`scripts/india/`](scripts/india/)): on fake data it reproduces the old steps 2-6 exactly, and five fake Indias with a planted truth all got the right verdict. On the real Karnataka and Kerala downloads it gives back the old results exactly (Karnataka -0.2286, Kerala -7.4047 species per SD of light; in the plan's unit -0.35 and -16.06 per 10x brighter). **India run done** (18 Nov; [DOI 10.15468/dl.nhjj65](https://doi.org/10.15468/dl.nhjj65), 48.8 M records, 8,802 squares in the models; 13 fresh states pass the size rules: 5 explore, 8 hold-out). **Explore half only, exploratory** ([`results/india_explore_states.csv`](results/india_explore_states.csv)): after habitat, brighter squares have fewer species in Maharashtra (-5.9 per 10x brighter, 95% range -9.1 to -2.7), Odisha (-7.0, -13.3 to -0.7) and Andhra Pradesh (-9.7, -16.5 to -2.9), as in Kerala (-16.5), but not in Karnataka (-0.3), Himachal Pradesh (-0.3) or Madhya Pradesh (+1.6). Over time within squares, no eligible state shows a clear light effect. **Planned tests, run once on 18 Nov ([`results/india_final_tests_summary.md`](results/india_final_tests_summary.md)): P1, the states differ meaningfully** (13 fresh states; typical difference between states tau = 3.3 species per 10x brighter, bar 2; I-squared 66%, p = 0.0004; average effect -3.6). **P2, none of the four pre-chosen factors explains the differences** in the 8 hold-out states (built-up area per person, NO2, tree cover, birdwatchers; all Holm p > 0.25; NO2 leaned the opposite way to the prediction). With 8 states this is "unsupported", not "disproved" |
| India (after the tests, exploratory) | How solid is it, and what else lines up? Listed in the plan before running ([`results/india_posthoc_states.md`](results/india_posthoc_states.md), [`results/india_posthoc_squares.md`](results/india_posthoc_squares.md), [`results/india_states_forest.png`](results/india_states_forest.png)) | **Across India, a square 10x brighter has about 3.7 fewer species** after habitat (one model, 8,802 squares, 95% range −5.1 to −2.3); 8 of 15 states clearly negative, none clearly positive. **The differences between places are solid:** they survive dropping any state and show up just as strongly between natural regions (18 ecoregions, I-squared 71%), but none of the four factors explains them there either. Inside states, light's link is stronger in greener, less built-up squares and where NO2 is higher; birdwatcher numbers don't change it (and allowing for them makes it stronger). **But over time, squares that got brighter did not lose species** (average over 15 states +0.03 species per visit per 10x brighter, SE 1.1), and states with the strongest across-space effect tend to have the weakest over-time one. Most likely reading: bright spots in green, unbuilt land mark villages, roads and farms that the building map underrates, so light stands in for human disturbance; a direct effect of light can't be shown with these data. **Cities don't drive it** ([`results/india_posthoc_places.md`](results/india_posthoc_places.md)): no single 50 km block flips any state, and states keep their sign without city cores. **It follows regions, not state lines** ([`results/india_light_effect_map.png`](results/india_light_effect_map.png)): strongest in the southern Western Ghats and hills, the Himalayan foothills and western Gangetic plain, the north-east and Vidarbha; near zero on the central Karnataka plateau, Goa and inner Madhya Pradesh / Chhattisgarh (Karnataka's zero hides a negative south and a positive middle). **Change maps** ([`results/india_map_light_change.png`](results/india_map_light_change.png), [`results/india_map_bird_change.png`](results/india_map_bird_change.png)): the median birded square got 1.8x brighter (90% brighter), while species per visit in the same 2,264 squares did not change on average (half up, half down); where light rose most is unrelated to where birds changed (Spearman -0.03) |

**Where this stands:** the drop in species with light in Karnataka is explained by habitat. A planned, written-down
test of the most promising idea (lights pull in night-migrating birds) was run on Karnataka and then once on
fresh data from Kerala: neither state supports it, and the patterns reverse between states, a warning sign of
confounding. Side results: worldwide trait labels (AVONET's migration score) can create false local effects, and
in Kerala (unplanned) brighter squares hold fewer species even after habitat. The coastline does not explain it
(step 9). Across India (a test locked before the data), the link between light and fewer species differs
meaningfully from state to state, and none of four pre-chosen explanations (built-up area per person, air
pollution, tree cover, birdwatching effort) accounts for it. On average brighter places hold fewer species even
after habitat, most in green, unbuilt landscapes, but places that got brighter over the decade did not lose
species, so light most likely marks human disturbance rather than causing the loss itself.

Figures are in [`results/`](results/).

## Data

| Data | Source | Citation |
|---|---|---|
| Bird records (eBird, iNaturalist, ...) | GBIF occurrence download: Aves, Karnataka (GADM IND.16_1), 2015-2025 | GBIF.org (15 November 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.t3hgj6 |
| Night lights | VIIRS annual composites V2.1/V2.2 (NOAA/EOG) via Google Earth Engine | Elvidge et al. (2021) *Remote Sensing* 13(5):922, https://doi.org/10.3390/rs13050922 |
| Buildings | GHSL built-up surface P2023A, 2015/2020/2025 (JRC) | Pesaresi & Politis (2023), GHS-BUILT-S R2023A, JRC Data Catalogue; Earth Engine `JRC/GHSL/P2023A/GHS_BUILT_S` |
| Tree cover / farmland | MODIS MOD44B and MCD12Q1 (NASA) | Earth Engine `MODIS/061/MOD44B`, `MODIS/061/MCD12Q1` |
| Surface water | JRC Global Surface Water v1.4 | Pekel et al. (2016) *Nature* 540:418 |
| Elevation | SRTM 90 m (CGIAR-CSI) | Earth Engine `CGIAR/SRTM90_V4` |
| Land / water mask (step 9) | Hansen/UMD Global Forest Change v1.12, data mask | Hansen et al. (2013) *Science* 342:850, https://doi.org/10.1126/science.1244693; Earth Engine `UMD/hansen/global_forest_change_2024_v1_12` |
| Population (India plan, F1) | GHSL population P2023A, 2020 (JRC) | Schiavina et al. (2023), GHS-POP R2023A, JRC Data Catalogue; Earth Engine `JRC/GHSL/P2023A/GHS_POP/2020` |
| Air pollution (India plan, F2) | Sentinel-5P TROPOMI tropospheric NO2, offline L3, 2019-2025 (ESA/Copernicus) | Earth Engine `COPERNICUS/S5P/OFFL/L3_NO2` |
| Kerala bird records (replication) | GBIF occurrence download: Aves, Kerala (GADM IND.17_1), 2015-2025 | GBIF.org (18 November 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.tzdphq |
| Rainfall (India, post-hoc) | WorldClim V1, annual precipitation (bio12) | Hijmans et al. (2005) *International Journal of Climatology* 25:1965, https://doi.org/10.1002/joc.1276; Earth Engine `WORLDCLIM/V1/BIO` |
| Natural regions (India, post-hoc) | RESOLVE Ecoregions 2017 | Dinerstein et al. (2017) *BioScience* 67:534, https://doi.org/10.1093/biosci/bix014; Earth Engine `RESOLVE/ECOREGIONS/2017` |
| India bird records (state comparison) | GBIF occurrence download: Aves, all of India (GADM IND), 2015-2025; 48,811,567 records | GBIF.org (18 November 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.nhjj65 |
| Bird traits | AVONET (CC BY 4.0) | Tobias et al. (2022) *Ecology Letters* 25:581, https://doi.org/10.1111/ele.13898 |

The data is **not** stored in this repository. Download the GBIF file with the DOI above (or `scripts/step1b_gbif_download.py`); every other source is fetched by the scripts.

## How to run

Each step is a Python script in `scripts/` (the master copy) with a matching Colab notebook in `notebooks/`.
Heavy steps (2, 3, 5, 6) are easiest in Google Colab; steps 3, 5 and 6 need a free Earth Engine project.

| Step | Script | Reads | Writes (in the data folder) |
|---|---|---|---|
| 1 | `step1_gbif_pull.py` | GBIF API | `step1/` overview (optional) |
| 1b | `step1b_gbif_download.py` | GBIF account | `raw/` the GBIF zip |
| 2 | `step2_slim_table.py` | `raw/` zip | `clean/birds_parts/` |
| 3 | `step3_night_lights.py` | Earth Engine | `clean/nightlights_*.csv` |
| 4 | `step4_join_birds_lights.py` | steps 2-3 | `clean/step4_*` |
| 5 | `step5_habitat_model.py` | step 4 + Earth Engine | `clean/habitat_*.csv`, `clean/step5_*` |
| 6 | `step6_time_and_traits.py` | steps 2-5 + AVONET + Earth Engine | `clean/step6_*`, `traits/` |
| 7 | `step7_traits_refined.py` | steps 2-6 + AVONET (no Earth Engine) | `clean/step7_*`, `traits/avonet_all_sheets.csv` |
| 7b | `step7b_seasonality_check.py` | step 2 + step 7 traits | `clean/step7b_seasonality.csv` |
| 7c | `step7c_local_migrants.py` | steps 2-7b (no Earth Engine) | `clean/step7c_*` |
| 8 | `step8_night_day_migrants.py` (`REGION` = karnataka or kerala) | steps 2-7b | `clean/step8_*` |
| 9 | `step9_land_check.py` (both states in one run) | step 5 + Earth Engine | `clean/land_0.05deg.csv`, `clean/step9_land_check.csv` |
| India | `india/india_pipeline.py`, then `india/india_final_tests.py` once (see [`scripts/india/README.md`](scripts/india/README.md)) | GBIF zip + Earth Engine | `bigdata/lpb_india/<run>/` |
| India, post-hoc | `india/india_posthoc_states.py` (laptop, small tables), `india/india_posthoc_squares.py` then `india/india_posthoc_places.py` (Colab), `india/india_posthoc_map.py` (laptop) | the India run | `results/india_posthoc_*`, `results/india_light_effect_map.png` |

Kerala replication: data in `bigdata/lpb_kerala/`; set `REGION = "kerala"` in each script (steps 1b, 2, ..., 8).

**Data folder:** in Colab, `My Drive/bigdata/lpb/`; on a computer, `~/bigdata/lpb/` or `~/Downloads/bigdata/lpb/` (the scripts check both).

Packages: `pip install -r requirements.txt`.

## Methods in one paragraph

Records are placed on a grid of 0.05° squares (~5.5 km). Birdwatching effort differs hugely between squares
(a box around Bengaluru holds ~45% of all records), so species counts are compared at equal effort using
Hurlbert rarefaction (expected species in 200 records). Models use cluster-robust standard errors over
0.5° blocks, because neighbouring squares are not independent. When many groups are tested at once, p-values
are corrected with Benjamini-Hochberg (q-values). Group shares are compared within like birds (e.g. migrants
among landbirds), because shares add up to 100% and one group rising can fake a fall in another. Every method was first tested on synthetic
data with a known answer (e.g. a planted "no effect" must come out near zero) before being run on the real data.

## How this was made

Built with Claude (Anthropic), which wrote the code and helped with the analysis and write-ups.
