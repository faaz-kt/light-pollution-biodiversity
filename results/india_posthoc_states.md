# India: post-hoc look at the state results (EXPLORATORY)

Run after the final tests (18 Nov 2026). Listed in the plan before running. Cannot confirm anything.

Check: P1 recomputed from the copied tables: Q = 35.7, p = 0.000365, I2 = 66%, tau = 3.34, mean -3.55 (final run said Q 35.7, p 0.000365, I2 66%, tau 3.34, mean -3.55).

## (a) Every state (light effect per 10x brighter, after habitat; species per 200 records)

| State | Half | Eligible | Squares | Blocks | Across space | 95% range | Over time | 95% range |
|---|---|---|---|---|---|---|---|---|
| Delhi | holdout | no | 57 | 3 | -36.2 | -70.9 to -1.4 | +8.9 | +0.2 to +17.6 |
| Kerala | seen | yes | 1072 | 27 | -16.5 | -22.3 to -10.7 | -0.6 | -2.8 to +1.5 |
| Haryana | explore | no | 96 | 19 | -15.6 | -24.6 to -6.6 | +20.7 | +13.7 to +27.6 |
| Andhra Pradesh | explore | yes | 204 | 42 | -9.7 | -16.5 to -2.9 | +7.1 | -1.7 to +15.8 |
| Assam | holdout | yes | 319 | 35 | -8.3 | -13.0 to -3.6 | +4.1 | -1.3 to +9.6 |
| Odisha | explore | yes | 169 | 39 | -7.0 | -13.3 to -0.7 | +7.6 | -9.4 to +24.7 |
| Uttarakhand | holdout | yes | 388 | 26 | -6.2 | -10.3 to -2.2 | +3.7 | -4.5 to +11.8 |
| Maharashtra | explore | yes | 1012 | 104 | -5.9 | -9.1 to -2.7 | +0.6 | -4.9 to +6.2 |
| Uttar Pradesh | holdout | yes | 217 | 51 | -5.8 | -14.3 to +2.6 | +7.7 | -4.6 to +19.9 |
| West Bengal | holdout | yes | 388 | 41 | -4.8 | -9.5 to -0.1 | -5.2 | -11.0 to +0.7 |
| Tamil Nadu | holdout | yes | 1134 | 60 | -4.6 | -10.0 to +0.7 | +6.6 | -1.0 to +14.2 |
| Gujarat | holdout | yes | 638 | 74 | -3.3 | -6.3 to -0.2 | -11.5 | -21.1 to -1.9 |
| Telangana | explore | no | 131 | 26 | -0.5 | -5.4 to +4.3 | -28.3 | -42.0 to -14.5 |
| Himachal Pradesh | explore | yes | 214 | 27 | -0.3 | -6.6 to +5.9 | -3.1 | -12.4 to +6.1 |
| Karnataka | seen | yes | 1014 | 71 | -0.3 | -3.3 to +2.7 | -1.6 | -5.6 to +2.3 |
| Madhya Pradesh | explore | yes | 403 | 69 | +1.6 | -3.6 to +6.8 | -0.8 | -6.6 to +5.1 |
| Rajasthan | holdout | yes | 367 | 71 | +2.2 | -1.3 to +5.6 | +2.0 | -10.1 to +14.1 |
| Goa | explore | no | 115 | 5 | +4.1 | +0.5 to +7.7 | +4.3 | -2.5 to +11.1 |
| Chhattisgarh | holdout | yes | 195 | 33 | +6.5 | -0.7 to +13.7 | -8.8 | -20.2 to +2.6 |
| Andaman and Nicobar | explore | no | 75 | 16 | +9.2 | +1.1 to +17.2 | -9.1 | -12.8 to -5.3 |
| Punjab | explore | no | 88 | 17 | +10.1 | -10.4 to +30.7 | +3.0 | -15.4 to +21.4 |

Of 15 eligible states: 8 clearly negative (95% range below 0), 0 clearly positive, 7 unclear.

## (b) How solid is 'states differ meaningfully'?

Leaving out one state at a time (13 runs):
- verdict holds in 13 of 13; tau ranges 2.63 to 3.76, I2 53% to 69%
- per SD of light instead of per 10x: tau 2.00 species per SD, I2 66%, p 0.000475 (the 2-species bar was set for per-10x units)
- adding Karnataka and Kerala (15 states): tau 4.14, I2 76%, p 1.51e-07, mean -4.08 (SE 1.26)
- adding the 6 states that failed the size rules (19 states; their error bars are less trustworthy): tau 4.50, I2 75%, p 1.46e-08
- each half on its own: explore (5 states) tau 3.44, I2 62%, mean -4.19; hold-out (8) tau 3.59, I2 71%, mean -3.17

## (c) Do states with a stronger across-space effect also show a stronger over-time effect?

Spearman rho between the two, over 15 eligible states: -0.55 (p 0.03). Over-time average across states: +0.03 (SE 1.12) species per visit per 10x brighter. (If light itself removed species, both measures should be negative and move together.)

## (d) The four factors over all 15 eligible states (each alone; no correction; exploratory)

- F1_built_m2_per_person: slope +0.27 species per 10x per SD of the factor (SE 1.50), p 0.862, 15 states
- F2_no2_umol_m2: slope +2.24 species per 10x per SD of the factor (SE 1.50), p 0.158, 15 states
- F3_tree_share: slope -2.92 species per 10x per SD of the factor (SE 1.22), p 0.0328, 15 states
- F4_median_observers: slope -2.26 species per 10x per SD of the factor (SE 1.40), p 0.13, 15 states

How the factors move together (Spearman, 15 states):

```
                        F1_built_m2_per_person  F2_no2_umol_m2  F3_tree_share  F4_median_observers
F1_built_m2_per_person                    1.00           -0.72           0.40                 0.35
F2_no2_umol_m2                           -0.72            1.00          -0.72                -0.64
F3_tree_share                             0.40           -0.72           1.00                 0.65
F4_median_observers                       0.35           -0.64           0.65                 1.00
```

