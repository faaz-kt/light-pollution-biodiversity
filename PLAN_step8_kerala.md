# Plan: night vs day migrants (step 8) and the Kerala replication

**Written 17 November 2026, ~22:30 IST, before running step 8 and before downloading any Kerala data.**
Anything changed after this date is listed at the bottom, with the reason. Results that come out "wrong" get
reported the same way as results that come out "right".

## Why this test

- Step 7c: birds that are true winter visitors to Karnataka made up a larger share of landbird records where it
  is brighter (+4.1 percentage points per 10x brighter over time, +1.4 across space), but this did not survive
  correction for the number of tests (q = 0.14). About 40 tests have been run on Karnataka so far, so this could
  be luck.
- Known biology: many birds migrate at night and are drawn towards artificial light (weather-radar studies in
  the USA: McLaren et al. 2018 *Ecology Letters* 21:356; Horton et al. 2023 *Nature Communications* 14:7446).
  Birds that migrate by day have no reason to be drawn to lights at night.
- So if light is really involved, the effect should be in **night migrants, not day migrants**. Comparing the
  two is a built-in control: things like "cities have more water" or "birdwatchers visit cities in winter"
  should affect both groups, but light attraction should only affect night migrants.

## Faaz's prediction (his words, 17 Nov 2026)

> "I'd say the hypothesis will be true that night migrants would be more, because the opposite would break the
> idea, or the fact that both of them does not care, both day and night."

In test terms: night migrants are a larger share where it is brighter; day migrants show no change, or a
smaller one. **The idea is wrong if** both groups rise by the same amount, or if night migrants show nothing.

Replication state: **Kerala**, chosen by Faaz. It is the neighbouring state, with a different landscape (more
Western Ghats forest, a narrow coastal plain, a different pattern of towns). Since 2015-2020 it has also had
the systematic Kerala Bird Atlas surveys (submitted through eBird), so its coverage is more even.

## Groups (fixed now, by family, from general knowledge, before seeing any results)

- **Winter visitor** = the step 7b rule: recorded in the monsoon (Jun-Aug) less than 1/5 as often as in winter
  (Nov-Feb). Worked out from **each state's own records**.
- **Night migrants** (most species migrate at night): Acrocephalidae (reed warblers), Locustellidae,
  Phylloscopidae (leaf warblers), Sylviidae, Muscicapidae (flycatchers, chats, robins), Turdidae (thrushes),
  Oriolidae (orioles), Laniidae (shrikes), Monarchidae (paradise flycatchers), Pittidae (pittas), Cuculidae
  (cuckoos), Rallidae (rails, crakes), Caprimulgidae (nightjars).
- **Day migrants** (migrate by day, as seen in "visible migration" counts): Hirundinidae (swallows),
  Apodidae (swifts), Accipitridae (hawks, eagles, harriers), Pandionidae (osprey), Falconidae (falcons),
  Ciconiidae (storks), Gruidae (cranes), Meropidae (bee-eaters), Motacillidae (wagtails, pipits),
  Sturnidae (starlings), Columbidae (pigeons, doves).
- **Neither (left out of both)**: families that migrate both by day and by night or are unclear, including waders
  (Scolopacidae, Charadriidae, Glareolidae and others), ducks and geese (Anatidae), gulls, terns and skuas,
  herons (Ardeidae), drongos (Dicruridae), rollers, buntings, finches, larks, cuckooshrikes, and anything else.
- **Night birds** (step 6 definition, unchanged): Strigidae, Tytonidae, Caprimulgidae, Podargidae, Burhinidae +
  genera Nycticorax, Gorsachius.
- **Insect-eaters**: AVONET Trophic.Niche = Invertivore (step 6 definition, unchanged).

## Tests (winter visits Nov-Feb unless stated; models exactly as in step 7c)

Each test is run two ways: **over time** (the same squares followed across years; light and buildings) and
**across space** (squares compared; habitat controls for buildings, trees, farmland, water, elevation).
Effect = change in percentage points when a square is 10x brighter.

**Primary test (P1): night share of migrants** = night-migrant records / (night-migrant + day-migrant records),
among winter visitors. Prediction: **positive**. If both groups rise equally, this stays flat.

**Secondary tests** (corrected together with Benjamini-Hochberg, 8 tests):
- S1: night-migrant visitors as % of all records. Prediction: positive.
- S2: day-migrant visitors as % of all records. Prediction: about zero, and smaller than S1.
- S3: night-migrant visitors as % of insect-eater records. These are compared with resident insect-eaters
  that use similar gardens and trees. Prediction: positive.
- S4: night birds as % of all records, **all year**. Prediction: negative (the step 6 lead).

## Decision rule for Kerala (primary test P1)

- **Supported**: P1 is positive in both analyses, and its 95% range is above zero in at least one.
- **Wrong**: P1 is zero or negative in both analyses.
- **Inconclusive**: anything else (opposite signs, or both positive with both ranges crossing zero).
- If an analysis has too little data (fewer than 30 rows, as in the code), it is skipped and the rule uses
  the other one. This will be stated.

## Order

1. Run step 8 on Karnataka. This is a first look, **not** independent evidence, because the idea came from
   Karnataka.
2. Download Kerala records from GBIF with the same filters as Karnataka: Aves (COL), GADM Kerala, 2015-2025,
   has coordinates, no geospatial issue. Prepare Kerala's lights, habitat, buildings, traits and seasonality
   with the same code (only the region setting changes).
3. Run the step 8 script on Kerala **once**, unchanged except for the region setting. Bug fixes are allowed
   only if they are listed below and the Karnataka run is repeated with the fixed code.
4. Report the result, whichever way it comes out.

## Weak points known before seeing results

- Night migrants here are mostly small insect-eaters of trees and gardens; day migrants include more open-country
  birds (pipits, raptors, storks). If brighter places have more garden trees, night migrants could rise for
  habitat reasons. Habitat controls and S3 address this partly, not fully.
- Records show what birdwatchers record, not true numbers of birds. GBIF has no checklist effort data
  (duration, distance).
- Family is a rough guide to when a species migrates. A few species will be in the "wrong" group.

## Changes after 17 Nov 2026

- 17 Nov, ~23:00, before any real run (clarification only): in S3, the top of the fraction is night-migrant
  visitors **that are insect-eaters**, so the share stays inside one group (insect-eaters), as in steps 7-7c.
- 17 Nov, before any real run: the step 8 script was tested on three fake worlds. (A) Light pulls in night
  migrants: the verdict was "supported". (B) Light raises night and day migrants equally: "wrong", even though
  night migrants alone (S1, S3) rose clearly. (C) No effect: "wrong". This is why P1, not S1, is the main test.
- 18 Nov (procedure only, before any Kerala analysis): GBIF rejected the API login, so Faaz requested the
  Kerala download on gbif.org himself. Checked against the plan: download 0013799-261110092616502,
  **DOI 10.15468/dl.tzdphq**, 5,964,349 records, filters identical to Karnataka's (GADM IND.17_1, Aves "V2" in
  the same Catalogue of Life checklist, 2015-2025, has coordinates, no geospatial issue).
- 18 Nov: steps 2-7b got the same `REGION` switch as step 8 (box and folder only; Karnataka values unchanged,
  checked line by line). Kerala data prep (steps 2-7b) runs and is checked first; step 8 runs on Kerala after
  that, once.
- 18 Nov, ~11:53 IST, Kerala prep checked BEFORE running step 8 (no light results looked at): all files present;
  5,960,964 records kept, 563 species, 23,811 observers; all 563 species matched to AVONET (100%, the Karnataka
  synonym table was enough); 236 winter-visitor species (10.6% of detections): 71 night-migrant species (41.1% of
  visitor records; Indian Golden Oriole, Blyth's Reed Warbler, Paradise Flycatcher, Brown Shrike, Greenish
  Warbler) and 55 day-migrant species (28.4%; Blue-tailed Bee-eater, Barn Swallow, Grey Wagtail, Oriental Honey
  Buzzard, Western Yellow Wagtail). Sample sizes: winter time model 4,193 square-years / 646 squares;
  winter space model 762 squares. Kerala is narrow, so only 27 neighbourhood blocks (0.5°) for the
  cluster-robust error bars: fewer than Karnataka, so its ranges are somewhat less exact. No changes needed.
- 18 Nov, ~11:56 IST: **step 8 run once on Kerala.** Result by the rule: **INCONCLUSIVE**. P1 night share of
  migrants: over time +2.81 (95% range -3.84 to +9.46), across space -8.88 (-18.19 to +0.43): opposite signs.
  No secondary test passed the correction (all q >= 0.21). Compared with Karnataka, the across-space signs FLIPPED
  (P1 +7.3 -> -8.9; S1 +1.5 -> -2.0; S3 +3.0 -> -3.4) and the over-time P1 sign flipped too (-9.2 -> +2.8).
  Night birds (S4): Karnataka -0.41 / -0.48, Kerala +0.55 / -0.69 (not consistent either).
  **Conclusion: the idea that light pulls in night migrants is not supported by these records in either state.**
  Note: the Colab cells for Kerala steps 3-7b left out some Karnataka-only prints and figures (place names on maps,
  extra plots); every calculation was the same code.
- 18 Nov, ~12:11 IST, **outside this plan (exploratory):** while preparing Kerala, the step 5 habitat model showed
  fewer species in brighter Kerala squares (-7.4 per SD of light, 95% range -10.1 to -4.7; Karnataka -0.2). Step 9
  checked whether the coastline explains this, after a fake-data test. It does not: -7.2 with land fraction as a
  control, -7.9 in inland squares only (Karnataka -0.4 / -0.5). This was found after looking at the data, so it is a
  lead for a new written plan, not a result of this one.
