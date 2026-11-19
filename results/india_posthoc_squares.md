# India: post-hoc square-level looks (EXPLORATORY)

Run 18 Nov 2026 ~19:50 IST in Colab after the final tests (code: scripts/india/india_posthoc_squares.py; listed in
the plan before running). Pipeline sha 77d8949d7626. Light effects are species per 200 records per 10x brighter,
after buildings, trees, farmland, water and elevation; 95% ranges from block-clustered errors. The ecoregion tables
are also saved in Drive (bigdata/lpb_india/india/results/posthoc_*.csv). Output copied as printed:

```
8802 model squares
(e1) all India: 8,802 squares, 840 blocks, 36 states; SD of log10 light 0.651
  one model, no state levels:     light -3.21 species per 10x [-5.00, -1.41]
  each state its own level (FE):  light -3.69 species per 10x [-5.14, -2.25]
(e2) light x modifier, inside states (state levels included):
  tree cover             light at average -3.85 per 10x; change in that per SD of tree cover: -2.38 [-3.67, -1.08], p 0.000323  (8,802 squares)
  observers (log10)      light at average -6.19 per 10x; change in that per SD of observers (log10): -0.30 [-0.96, +0.37], p 0.378  (8,802 squares)
  NO2                    light at average -4.48 per 10x; change in that per SD of NO2: -1.42 [-2.29, -0.54], p 0.00152  (8,802 squares)
  buildings              light at average +0.12 per 10x; change in that per SD of buildings: +4.40 [+2.76, +6.05], p 1.53e-07  (8,802 squares)
(f) per state (eligible):
           state  coef_10x  rho_light_built  rho_light_tree  share_bright  sd_light
          Kerala   -16.531            0.918          -0.655         0.019     0.465
  Andhra Pradesh    -9.737            0.927          -0.174         0.142     0.589
           Assam    -8.286            0.714          -0.240         0.066     0.532
          Odisha    -7.018            0.952          -0.437         0.183     0.646
     Uttarakhand    -6.232            0.864          -0.486         0.067     0.558
     Maharashtra    -5.932            0.914          -0.500         0.183     0.655
   Uttar Pradesh    -5.840            0.962          -0.481         0.498     0.716
     West Bengal    -4.787            0.905          -0.478         0.227     0.692
      Tamil Nadu    -4.640            0.917          -0.491         0.109     0.527
         Gujarat    -3.254            0.924           0.187         0.161     0.658
Himachal Pradesh    -0.323            0.817           0.031         0.000     0.448
       Karnataka    -0.291            0.856          -0.657         0.145     0.659
  Madhya Pradesh     1.575            0.958          -0.632         0.166     0.721
       Rajasthan     2.192            0.931           0.132         0.180     0.633
    Chhattisgarh     6.527            0.933          -0.366         0.179     0.601
  across states, Spearman(light effect, rho_light_built) = +0.18 (p 0.52)
  across states, Spearman(light effect, rho_light_tree) = +0.13 (p 0.64)
  across states, Spearman(light effect, share_bright) = +0.23 (p 0.41)
  across states, Spearman(light effect, sd_light) = +0.33 (p 0.23)
(e3) light x all four modifiers together, inside states (8,802 squares):
  light x tree   -2.85 [-3.91, -1.80] p 1.25e-07
  light x built  +3.76 [+2.29, +5.23] p 5.27e-07
  light x no2    -2.36 [-3.26, -1.45] p 3.29e-07
  light x obs    -0.53 [-1.14, +0.09] p 0.0948
(g) squares matched to an ecoregion: 97.7%

(g) by BIOME_NAME: 11 units, 5 pass the plan's size rules (150 squares, 10 blocks)
                                          unit  n_squares  n_blocks  states  coef_10x  low95_10x  high95_10x  F2_no2_umol_m2  F3_tree_share  F4_median_observers
           Temperate Broadleaf & Mixed Forests        211        41       8     -6.59     -12.47       -0.70           18.04           0.47                 41.0
Tropical & Subtropical Moist Broadleaf Forests       4053       361      31     -4.03      -7.14       -0.93           31.87           0.25                 33.0
  Tropical & Subtropical Dry Broadleaf Forests       2375       293      15     -2.57      -5.11       -0.03           37.14           0.10                 28.0
                    Deserts & Xeric Shrublands       1355       235      12     -0.34      -2.99        2.31           34.93           0.07                 27.0
     Tropical & Subtropical Coniferous Forests        328        31       8      1.38      -4.25        7.01           22.59           0.35                 40.0
  differ? Q 7.0 on 4 df, p 0.136, I2 43%, tau 1.52, average -2.28
  F1_built_m2_per_person   slope +2.42 (SE 0.90) p 0.0751  [5 units]
  F2_no2_umol_m2           slope +0.75 (SE 1.66) p 0.684  [5 units]
  F3_tree_share            slope -1.33 (SE 1.45) p 0.426  [5 units]
  F4_median_observers      slope -0.84 (SE 1.59) p 0.633  [5 units]

(g) by ECO_NAME: 42 units, 18 pass the plan's size rules (150 squares, 10 blocks)
                                         unit  n_squares  n_blocks  states  coef_10x  low95_10x  high95_10x  F2_no2_umol_m2  F3_tree_share  F4_median_observers
  South Western Ghats moist deciduous forests        461        28       3    -11.00     -16.11       -5.90           21.08           0.29                 35.0
    Brahmaputra Valley semi-evergreen forests        281        31       2     -9.50     -13.85       -5.15           21.98           0.26                 33.0
Lower Gangetic Plains moist deciduous forests        273        48       7     -7.96     -15.70       -0.22           46.02           0.15                 22.0
     South Western Ghats montane rain forests        476        19       3     -6.98     -11.65       -2.30           19.51           0.45                 42.0
Upper Gangetic Plains moist deciduous forests        416        63       7     -6.54     -10.74       -2.33           53.86           0.12                 34.5
          Chhota-Nagpur dry deciduous forests        156        30       5     -5.47     -12.53        1.58           64.12           0.10                 21.0
 Central Deccan Plateau dry deciduous forests        460        64       5     -4.82      -8.83       -0.82           44.00           0.10                 26.0
          East Deccan moist deciduous forests        477        88       6     -4.62     -11.30        2.05           50.32           0.14                 23.0
           Khathiar-Gir dry deciduous forests        483        82       4     -2.77      -6.58        1.05           39.68           0.06                 28.0
   South Deccan Plateau dry deciduous forests        728        42       2     -2.52      -8.08        3.04           27.94           0.11                 31.0
            Aravalli west thorn scrub forests        583        94       7     -1.90      -5.18        1.39           41.93           0.06                 27.0
                  Malabar Coast moist forests        813        39       5     -1.48      -7.95        4.99           26.52           0.26                 45.0
         Narmada Valley dry deciduous forests        281        51       2     -0.25      -6.22        5.72           34.46           0.11                 27.0
                   Deccan thorn scrub forests        675       112       4      0.91      -3.53        5.36           30.33           0.08                 25.0
           Himalayan subtropical pine forests        315        28       6      1.19      -4.55        6.93           22.95           0.34                 41.0
  North Western Ghats moist deciduous forests        271        37       5      1.35      -4.27        6.97           30.66           0.18                 26.0
     North Western Ghats montane rain forests        239        25       3      4.40      -1.43       10.23           24.09           0.33                 30.0
            East Deccan dry-evergreen forests        211        16       3      8.44       2.93       13.94           28.60           0.10                 31.0
  differ? Q 58.2 on 17 df, p 2.07e-06, I2 71%, tau 3.95, average -2.79
  F1_built_m2_per_person   slope -0.76 (SE 1.24) p 0.547  [18 units]
  F2_no2_umol_m2           slope -0.86 (SE 1.25) p 0.499  [18 units]
  F3_tree_share            slope -0.91 (SE 1.19) p 0.452  [18 units]
  F4_median_observers      slope -0.40 (SE 1.27) p 0.757  [18 units]
```

Notes. (e2)/(e3): an interaction is how much light's effect changes per SD of the other variable; negative = light's
link to fewer species is stronger where that variable is higher. Seven interaction models were fitted, so treat
p-values loosely. The ecoregion source is RESOLVE Ecoregions 2017 (Dinerstein et al. 2017, BioScience 67:534;
Earth Engine 'RESOLVE/ECOREGIONS/2017').
