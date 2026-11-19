# Plan: does the link between night light and bird species differ across India, and why?

**Drafted 18 November 2026, ~12:40 IST. LOCKED 18 November 2026, 12:47 IST, at Faaz's request, before any
India-wide data was downloaded.** Anything changed after locking is listed at the bottom, with the date and the
reason. Results that come out "wrong" are reported exactly like results that come out "right".

## Why this study

- Step 5 on Karnataka: light adds nothing once habitat is controlled for (-0.23 species per SD of light).
  Step 5 on Kerala: light is clearly linked to fewer species (-7.40 per SD, 95% range -10.07 to -4.74). The
  difference is far bigger than the error bars. The coastline does not explain it (step 9).
- Both findings are **exploratory** (we looked first, then explained). Two states cannot say whether Kerala is an
  oddity or part of a pattern. Many fresh states can.

## Faaz's prediction (18 Nov 2026, before any data; voice-typed, trimmed)

> "my prediction would be that there will be some exceptions due to other factors, like other pollution. Yes, some
> cities are more urbanized than others, but it does not necessarily mean that they have a larger population. I'd
> say air pollution, water pollution, and some specific vegetation that does not really help the birds. These
> regions will have different patterns compared, but it's fine"

In test terms: **the states will differ** (P1), and the differences will line up with air pollution, with how
"urbanised" a state is relative to its population, and with vegetation type (P2). **The prediction is wrong if**
the states do not differ by a meaningful amount. If they differ but no factor lines up in the hold-out half, the
explanation part is **unsupported, not disproved**: with about 8 hold-out states the test is too weak to rule a
factor out.
Water pollution has no usable open map at this scale, so that part **cannot be tested** and will be reported as such.

## Data and units

- **Bird records:** one GBIF download for all of India (GADM IND), Aves in the same Catalogue of Life checklist,
  2015-2025, has coordinates, no geospatial issue; same filters as Karnataka and Kerala. Its DOI will be cited.
- **Same pipeline as steps 2-5**, run state by state: visits (observer x day x square), 0.05 degree squares,
  rarefied species at 200 records, VIIRS night lights, GHSL buildings, MODIS trees and farmland, JRC water,
  SRTM elevation.
- **Which states count (fixed now):** a state is analysed on its own if it has at least 300,000 records
  (live GBIF count on 18 Nov) **and** at least 150 squares with enough visits **and** those squares fall in at
  least 10 different 0.5 degree blocks (checked after step 4, using no light results). The blocks rule matters
  because the error bars come from comparing blocks, and with fewer than about 10 blocks they come out too small,
  which would make states look more different than they are. That gives up to 21 states, listed below. Smaller
  states (Bihar, Jharkhand, most of the northeast) are downloaded but left out of the state comparison. A state that
  fails a rule (Delhi and Goa almost certainly will, being only one or two blocks wide) is dropped from whichever
  half it is in.
- **Which state a square belongs to:** the state holding most of that square's records (squares on a border are
  not split).
- **Effect size:** the light coefficient in the step 5 model, expressed **per 10x brighter** (the coefficient on
  log10(radiance + 0.1)), with cluster-robust standard errors over 0.5 degree blocks. Per-SD values are also saved
  so they can be compared with steps 5 and 9.
- **Reproduction check first:** run on the **original** Karnataka and Kerala downloads (DOIs t3hgj6 and tzdphq,
  already in Drive), the new code must give back Karnataka -0.23 and Kerala -7.40 per SD (and the same per-10x
  values the old code gives) before any other state is run. If not, stop and find out why. (The India download
  will contain slightly different Karnataka and Kerala records, because GBIF adds and removes records over time,
  so it is not used for this check.)

## The random split (drawn 18 Nov 2026, seed 20261118, within zones, before any data)

Karnataka and Kerala were already seen, so they are always in the **explore** half and are **not** used in P1.

- **Hold-out (9):** Chhattisgarh, West Bengal, Delhi, Uttar Pradesh, Uttarakhand, Assam, Tamil Nadu, Gujarat,
  Rajasthan.
- **Explore (10 new + Karnataka + Kerala):** Madhya Pradesh, Odisha, Haryana, Himachal Pradesh, Punjab,
  Andaman and Nicobar, Andhra Pradesh, Telangana, Goa, Maharashtra.

GADM codes: Andaman 1, Andhra 2, Assam 4, Chhattisgarh 7, Goa 10, Gujarat 11, Haryana 12, Himachal 13,
Karnataka 16, Kerala 17, Madhya Pradesh 19, Maharashtra 20, Delhi 25, Odisha 26, Punjab 28, Rajasthan 29,
Tamil Nadu 31, Telangana 32, Uttar Pradesh 34, Uttarakhand 35, West Bengal 36. (Names follow GADM's alphabetical
numbering; the code checks them against GADM before the split is used.)

## Tests

**P1: do the states differ?** One light coefficient (across-space model, per 10x brighter) per fresh state
(19 minus any dropped). Cochran's Q test for differences between states, I-squared, and the random-effects
spread tau (DerSimonian-Laird): tau is the typical difference between states' light effects, in species per 10x
brighter. With millions of records even tiny differences pass a Q test, so significance alone is not enough.
**States differ meaningfully** if Q has p < 0.05, I-squared >= 50% **and** tau >= 2 species per 10x brighter.
Otherwise: no evidence of meaningful differences. Karnataka and Kerala are shown on the map but left out,
because we already know they differ.

**P2: does a pre-chosen factor line up with the differences?** Four state-level factors, fixed now, each tested
**alone** (ten or so states cannot support more), in the **hold-out half only**, by a random-effects
meta-regression of the state's light coefficient on the factor (standardised): weights 1 / (SE^2 + tau^2), so one
very data-rich state cannot dominate, and the Knapp-Hartung correction (t-distribution), which keeps p-values honest
with so few states. All factors are measured from maps or the records, never from the light coefficients.

| Factor | How it is measured | Predicted sign (stronger harm = more negative) |
|---|---|---|
| F1: built-up area per person | GHSL built surface / GHSL population (squares in the analysis) | more built per person -> more negative |
| F2: air pollution | Sentinel-5P tropospheric NO2, 2019-2025 mean (a traffic and industry proxy) | higher NO2 -> more negative |
| F3: vegetation | mean tree cover share (MODIS) of the analysed squares | no sign predicted (two-sided) |
| F4: birdwatching effort | median number of distinct observers per analysed square | no sign predicted (two-sided) |

Signs for F1 and F2 were chosen by Claude from Faaz's reasoning; he can change them before the plan is locked.
**A factor is supported** if its slope in the hold-out half has p < 0.05 after Holm correction over the factors
tested (4, plus any logged extras), with the predicted sign where one is given. Coastline was dropped from the list:
step 9 already ruled it out in Kerala.

**Secondary (reported, not decisive):** the same P1 on the over-time model (squares followed across years, two-way
fixed effects); the explore half's own factor slopes (including Karnataka and Kerala).

## Order

1. Download, prepare and run all states. All estimates are saved to files; the code prints and plots the explore
   half only, and writes hold-out estimates to a separate file that nobody opens until step 3.
2. Look at the **explore half only** (maps, plots, anything). Any new idea is written into "Changes" below with the
   date **before** it is tested.
3. Freeze the explore-half analysis. Then run P1 and P2 on the hold-out half **once**, plus any logged extras.
4. Report the result, whichever way it comes out.

## Weak points known before seeing results

- **Power is low.** About 9 hold-out states cannot detect a modest link between a factor and the light effect. An
  inconclusive P2 is the likely outcome, even if the factors matter.
- States are political lines, not habitats. Averaging a state hides Western Ghats vs plateau type differences.
  Natural zones are a possible follow-up, not part of this plan.
- Records show where people birdwatch, not true bird numbers; effort and skill differ by state (F4 only partly
  covers this).
- NO2 comes from traffic and cities, so it moves with urbanisation. F1 and F2 may be tangled.
- Satellite NO2 starts in 2018, so F2 describes recent years, not 2015.
- No seasonal split: light and species are both all-year averages in this plan.
- Neighbouring states are not fully independent (shared birds, birders, weather), but the tests treat them as
  independent, so the p-values are somewhat optimistic.
- "Tree cover" mixes forest with plantations (rubber, eucalyptus, tea); the "vegetation that doesn't help birds"
  idea can only be tested roughly.
- The night-migrant question (winter vs passage months) is **not** part of this plan and needs its own.

## Changes

- 18 Nov, ~12:45 IST, review before locking (no data seen): added the 10-blocks rule (few blocks give error bars
  that are too small); P1 now also needs a meaningful size (tau >= 2 species per 10x brighter), since huge data
  makes Q significant for trivial differences; P2 specified as random-effects meta-regression with Knapp-Hartung;
  F3 reduced to tree cover only (two measures counted as one factor was a loophole); reproduction check moved to the
  original Karnataka/Kerala downloads; rule for border squares; hold-out results written to a separate file; a null
  P2 now reads "unsupported", not "wrong"; three more weak points listed.
- 18 Nov, 12:47 IST: **plan locked.** A copy of the locked file is kept in the "Fill that resume" Claude Project
  (claude/PLAN_india_locked.md), and its SHA-256 fingerprint is recorded in CLAUDE.md, so any later edit to the
  locked text can be detected. Everything below this line is a change made after locking.
- 18 Nov, ~13:10 IST, **clarifications made while writing the code** (no India data downloaded or seen; the
  meaning of the tests is unchanged):
  1. "At least 150 squares with enough visits" = squares that enter the model (>= 25 visits and >= 200 records,
     exactly step 5's filter).
  2. A square's state is taken from the state **name** in each record (GBIF's simple download has no GADM column):
     the state named in most of the square's records. As the promised check against GADM, part A compares each of
     the 21 states' record counts with GBIF's GADM-based counts of 18 Nov; any state off by more than 10% is
     checked before going on.
  3. P2's random-effects meta-regression estimates the leftover spread between states (tau-squared) by the method
     of moments (DerSimonian-Laird for meta-regression), within the hold-out states; then Knapp-Hartung as planned.
  4. F1 = total built-up area / total population over the state's model squares (each square weighted by its
     area); F2 = mean of the 2019-2025 yearly NO2 means (a square needs at least 5 of the 7 years); F4 counts
     distinct observers over all years.
  5. A state is eligible only if its model can be fitted (always true with >= 150 squares).
  6. The secondary over-time model is step 6's "species per visit" two-way fixed-effects model, per 10x brighter.
- 18 Nov, ~13:45 IST, **fake-world tests** (before any real India data; code unchanged): five fake Indias with a
  known truth gave the right verdict every time. No effect: P1 no, P2 nothing. Effect tied to NO2: P2 found F2
  only (Holm p 0.045 when weak, 0.001 when strong); P1 "differ meaningfully" only when the planted spread passed
  the 2-species bar (tau 5.2), not when it was below it (tau 0.9). Random differences: P1 yes when strong, P2
  nothing. Details in scripts/india/README.md.
- 18 Nov, ~14:20 IST, **reproduction checks PASSED** (Colab, original downloads, no India data yet). One bug was
  found and fixed first: single-band Earth Engine layers were not renamed (step 5 renamed them), so the buildings
  request failed; fixed by naming each band after its layer (no effect on any value). Results: Karnataka 1,020
  squares (old 1,020), light -0.2286 per SD (old -0.2286), 95% range -2.20 to +1.75; Kerala 1,054 squares (old
  1,054), -7.4047 per SD (old -7.4047), -10.07 to -4.74. In the plan's unit: Karnataka -0.35, Kerala -16.06 species
  per 10x brighter (SD of log10 light 0.661 and 0.461). State names put 99.5% / 99.9% of model squares in the right
  state. Part A matched step 2 exactly (Karnataka 7,814,812 records kept, 576 species, 26,139 observers).
- 18 Nov, ~17:25 IST, **India run finished (plan step 1; code unchanged, pipeline sha 77d8949d7626).** Download
  0014194-261110092616502 (DOI 10.15468/dl.nhjj65, 48,811,567 records, filters exactly as planned, file size matches
  GBIF's). Part A kept 48,786,341 records (1,390 species, 145,462 observers); all 21 states' record counts are within
  3% of GBIF's map-based counts (worst: Tamil Nadu 97.7%, Kerala 102.7%); 0.06% of records had no placeable state
  name. 8,987 squares enter the models. **Eligibility** (uses no light result; printed for every state by design):
  not eligible are Andaman (75 squares), Goa (5 blocks), Haryana (96 squares), Punjab (88) and Telangana (131) in the
  explore half, and Delhi in the hold-out half. So **P1 will use 13 fresh states** (5 explore: Andhra Pradesh,
  Himachal Pradesh, Madhya Pradesh, Maharashtra, Odisha; 8 hold-out) and **P2 will use the 8 hold-out states**
  (Assam, Chhattisgarh, Gujarat, Rajasthan, Tamil Nadu, Uttar Pradesh, Uttarakhand, West Bengal), fewer than the
  "about 9" the plan expected, so the power warning stands. The explore half was looked at
  (results/india_explore_states.csv, copied from Drive exactly as saved); the hold-out file was written but has not
  been opened. No new idea has been logged and no test has changed.
- 18 Nov, 17:32 IST, **Faaz's prediction before the final tests** (after seeing the explore half, before any
  hold-out result; voice-typed): "in the more polluted and urban areas, the variety of birds will be less, and of
  course, we have taken into account bird watchers in more light-ish areas, right?" In test terms (confirmed by his
  "GO" at 18:19): P1, states differ meaningfully (as in his locked prediction); P2, F2 NO2 and F1 built-up area per
  person line up with a more negative light effect; no prediction for F3 or F4. Noted to him first: the habitat
  controls already account for fewer species in built-up places, so P2 asks whether light's own extra effect is
  bigger in polluted or urban states.
- 18 Nov, 18:19 IST, **explore half frozen** at Faaz's "GO". No extra factors. india_final_tests.py run once with
  EXPLORE_FROZEN = True, FROZEN_NOTE = "Frozen 18 Nov 2026 18:19 IST, no extra factors".
- 18 Nov, 18:22 IST, **FINAL TESTS, run once** (Colab; code identical to scripts/india/india_final_tests.py apart
  from the two settings; full output in results/india_final_tests_summary.md).
  **P1: states differ meaningfully.** 13 fresh states: Q = 35.7 on 12 df, p = 0.0004; I-squared 66%; tau = 3.34
  species per 10x brighter (bar: 2); average light effect -3.55 species per 10x brighter (SE 1.18). Secondary, over
  time: Q p = 0.038, I-squared 45%, tau 3.65 (reported only).
  **P2: no factor supported** (8 hold-out states, Holm over 4): F1 built-up per person slope +0.36 (Holm p 0.86);
  F2 NO2 +3.16 (Holm p 0.30; opposite to the predicted sign); F3 tree cover -2.86 (raw p 0.064, Holm 0.26); F4
  observers per square -3.00 (raw p 0.10, Holm 0.30). All "unsupported, not disproved" (8 states is weak, as warned).
  Secondary, explore half (7 states): no slope near significance; F3 and F4 have the same sign as in the hold-out.
  **Faaz's prediction:** P1 right (states differ); P2 (NO2 and urban sprawl explain it) not supported, and NO2 leaned
  the other way.
- 18 Nov, ~19:35 IST, **post-hoc analyses listed before running them** (Faaz: "analyze the data, do what else you
  want with it"). All are EXPLORATORY: they come after the final tests, use the same data, and cannot confirm
  anything; they can only suggest what a new, written test should look at. (a) Open the hold-out file (allowed now,
  Order step 4) and report all 15 eligible states. (b) Is P1 robust? Drop one state at a time; per-SD units instead
  of per 10x; add Karnataka and Kerala; add the six states that failed the size rules. (c) Do states with a stronger
  across-space light effect also show a stronger over-time effect? (d) The four factors over all 15 eligible states.
  (e) Square level, all of India: one model with a separate starting level for each state; light x tree cover and
  light x observers interactions (do the two P2 leads show up inside states?). (f) How tangled light and buildings
  are in each state, and whether that tracks the light effect (a possible artifact). (g) The light effect by
  natural region (RESOLVE 2017 biomes) instead of by state, as the plan's weak points suggested.
- 18 Nov, ~20:00 IST, **post-hoc results (EXPLORATORY; results/india_posthoc_states.md, india_posthoc_squares.md,
  india_states_forest.png).** (a) Hold-out file opened: of 15 eligible states, 8 clearly negative, none clearly
  positive. (b) P1 holds when any one state is dropped (13 of 13; tau 2.6 to 3.8), in each half alone (explore tau
  3.4, hold-out 3.6), with Karnataka and Kerala added (tau 4.1) and with the small states added (tau 4.5); per SD of
  light tau is exactly 2.0. (c) Over time the average is +0.03 (SE 1.12), and states with a more negative
  across-space effect have a more positive over-time effect (Spearman -0.55, p 0.03): not what light causing the
  loss would produce. (d) Over all 15 states, tree cover -2.9 per SD (p 0.03, uncorrected), the others p > 0.1; the
  four factors are tangled (NO2 vs trees -0.72). (e) One model for all of India: -3.7 species per 10x brighter
  (95% -5.1 to -2.3) with state levels. Inside states, light's link is stronger where there are more trees (-2.4
  per SD) and more NO2 (-1.4), weaker where there are more buildings (+4.4), not changed by birdwatchers (-0.3);
  the first three survive together. (f) Light and buildings are tangled in every state (Spearman 0.71 to 0.96),
  but that does not track the light effect (+0.18, p 0.52), so the differences are not a collinearity artifact.
  (g) By ecoregion (18 pass the size rules) the effects differ as much as by state (I-squared 71%, tau 3.95) and
  none of the four factors explains it; by biome, forests are more negative (moist broadleaf -4.0, temperate -6.6)
  than deserts (-0.3). Correction to the 17:25 entry: 8,987 squares have >= 25 visits; 8,802 enter the models.
- 18 Nov, ~19:45 IST, **more post-hoc checks listed before running** (Faaz: which states break away from the rest,
  could specific cities or regions have skewed them, is there a pattern we are missing?). EXPLORATORY. (h) A map
  of the light effect across India from overlapping 150 km windows (one model per window, same as step 5).
  (i) For each eligible state, drop one 0.5 degree block at a time and see which place moves the state's light
  effect most (blocks named by the nearest big city, approximate). (j) Refit each state without bright city cores
  (radiance > 20) and without squares within 25 km of a big city. (k) Rainfall (WorldClim annual precipitation)
  as a wet/dry check, because the ecoregion list looked wet = more negative, dry = near zero.
- 18 Nov, ~20:15 IST, **results of (h)-(k)** (EXPLORATORY; results/india_posthoc_places.md,
  india_light_effect_map.png). (i)/(j) No single 0.5 degree block flips any state; the biggest single move is
  Andhra Pradesh -9.7 to -6.1 without the Visakhapatnam block. Dropping bright city cores or all squares within
  25 km of a big city leaves every state on the same side of zero (Kerala -16.8 / -15.1, Chhattisgarh +8.1 /
  +7.6), so big cities do not drive the outliers. (h) The light effect follows regions that cut across states:
  strongly negative in the southern Western Ghats and hills (Kerala, Nilgiris, southern Karnataka), the Himalayan
  foothills and western Gangetic plain, the north-east and Vidarbha; near zero or positive on the central
  Karnataka plateau, Goa and coastal Karnataka, and inner Madhya Pradesh / Chhattisgarh. Karnataka's near-zero
  value hides a negative south and a positive middle. (k) Rainfall adds nothing inside states once tree cover is
  in (light x trees stays -3.2 per SD); the state-level rain hint depends on Kerala and Assam.
- 18 Nov, ~20:40 IST, **change maps** (Faaz asked for maps, not graphs; EXPLORATORY; Colab "POST-HOC 5",
  scripts/india/india_change_maps.py, results/india_map_light_change.png, india_map_bird_change.png). Light: median
  square 1.84x brighter in 2024-25 than 2015-16; 90% of 8,987 birded squares got brighter, almost everywhere.
  Birds: 2,264 squares followed in both 2015-18 and 2022-25 (>= 10 visits a year); species per visit changed by a
  median -0.04 (of about 17), half gained, half lost. Light change vs bird change: Spearman -0.03 over squares
  (p 0.21), -0.02 over 205 cells (p 0.82): no link. Birdwatching does lean to brighter squares (Spearman light vs
  visits +0.22, vs observers +0.08); the species measures are effort-fair (200 records; per visit).
