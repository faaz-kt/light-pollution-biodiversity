# India: which places drive the outlier states? (EXPLORATORY)

Run 18 Nov 2026 ~20:10 IST in Colab ("POST-HOC 4"; code scripts/india/india_posthoc_places.py), after the final
tests; listed in the plan before running. Light effects: species per 200 records per 10x brighter, after habitat.
Place names are the nearest big city to a 0.5 degree block (approximate city centres). Map:
results/india_light_effect_map.png (from results/india_posthoc_moving_window.csv, 111 windows of 150 km).

## (i) + (j) Per state: the two blocks that move the state's value most, and refits without cities

chg = change in the state's value when that block is dropped. no_core = without squares brighter than
20 nW/sr/cm2 (n_core of them); no_big25 = without squares within 25 km of a big city (n_big25 of them).
check = difference from the planned run's value (0 = same).

```
           state  check   coef   se                     block1  chg1  sq1                     block2  chg2  sq2    n  n_core  no_core  n_big25  no_big25
          Kerala    0.0 -16.53 2.97             Kollam (16 km)  1.91   55             Munnar (40 km)  1.45   56 1072       1   -16.76      178    -15.08
  Andhra Pradesh    0.0  -9.74 3.47      Visakhapatnam (12 km)  3.68   25          Tirupati (121 km) -1.44   10  204       1    -9.93       37     -7.70
           Assam    0.0  -8.29 2.40           Guwahati (89 km)  2.13   17           Guwahati (14 km)  1.33   41  319       1    -8.60       35     -7.25
          Odisha    0.0  -7.02 3.23               Puri (51 km) -2.16   16        Bhubaneswar (15 km)  2.15   41  169       2    -8.17       35     -5.41
     Uttarakhand    0.0  -6.23 2.07           Dehradun (13 km) -1.84   50 Ramnagar (Corbett) (46 km)  1.33   31  388       1    -6.46       43     -7.83
     Maharashtra    0.0  -5.93 1.64             Mumbai (35 km) -0.85   37             Mumbai (19 km)  0.72   39 1012      44    -5.00      154     -4.94
   Uttar Pradesh    0.0  -5.84 4.31             Kanpur (15 km) -2.48    8          Bharatpur (23 km)  2.21   16  217      45    -8.33       79    -10.46
     West Bengal    0.0  -4.79 2.38            Kolkata (70 km) -1.37   11            Kolkata (22 km)  1.28   23  388      16    -5.26       48     -3.91
      Tamil Nadu    0.0  -4.64 2.72 Thiruvananthapuram (55 km)  1.89   34               Ooty (17 km)  1.69   69 1134      14    -4.95      122     -4.35
         Gujarat    0.0  -3.25 1.54               Bhuj (19 km)  0.87   38          Ahmedabad (17 km) -0.71   24  638      26    -4.17       88     -4.47
Himachal Pradesh   -0.0  -0.32 3.20        Dharamshala (11 km)  1.83   21           Dehradun (42 km) -1.68    3  214       0    -0.32        2     -1.09
       Karnataka    0.0  -0.29 1.53             Mysuru (47 km)  0.93   54          Bengaluru (32 km)  0.63   57 1014      35    -0.88      116     -0.93
  Madhya Pradesh    0.0   1.58 2.66             Indore (13 km)  1.44   29           Jabalpur (13 km) -1.34    7  403      13     3.70       86      3.08
       Rajasthan    0.0   2.19 1.76             Jaipur (11 km) -0.94   28            Udaipur (10 km) -0.74   16  367      14     2.20       61     -0.68
    Chhattisgarh    0.0   6.53 3.67             Raipur (54 km) -1.89   15         Jagdalpur (114 km) -1.56    3  195       7     8.07       37      7.63
```

No single place flips any state, and removing city cores or everything near big cities leaves every state on the
same side of zero (largest moves: Andhra Pradesh -9.7 to -6.1 without the Visakhapatnam block; Uttar Pradesh
becomes more negative without its cities, -10.5).

## (k) Rainfall (WorldClim V1 annual precipitation)

```
(k) rainfall matched for 8,606 squares
  alone: lx_rain -0.56 per SD [-1.60, +0.47] p 0.284
  with light x trees: lx_rain +0.70 per SD [-0.41, +1.81] p 0.217
  with light x trees: lx_tree -3.23 per SD [-4.75, -1.72] p 3e-05
  13 fresh states: slope per SD of state rainfall -1.87 (SE 1.10) p 0.117
  15 states: slope per SD of state rainfall -3.18 (SE 1.16) p 0.0167
  18 ecoregions: slope per SD of rainfall -0.06 (SE 1.23) p 0.959
  state mean rainfall (mm): {'Andhra Pradesh': 959, 'Assam': 2378, 'Chhattisgarh': 1295, 'Gujarat': 722, 'Himachal Pradesh': 1508, 'Karnataka': 1616, 'Kerala': 2875, 'Madhya Pradesh': 1164, 'Maharashtra': 1712, 'Odisha': 1419, 'Rajasthan': 558, 'Tamil Nadu': 992, 'Uttar Pradesh': 972, 'Uttarakhand': 1636, 'West Bengal': 1918}
```

Rain alone is not the pattern: inside states it adds nothing once tree cover is in, and the state-level hint
depends on Kerala and Assam (15 states p 0.017; without Karnataka and Kerala p 0.12; ecoregions p 0.96).

## (h) The map, in words

Strongly negative windows (95% range below zero): the southern Western Ghats and hills (Kerala, the Nilgiris and
western Tamil Nadu, southern Karnataka around Mysuru), the Himalayan foothills and western Gangetic plain
(Uttarakhand, around Delhi, western Uttar Pradesh), the north-east (Brahmaputra valley, north Bengal) and
Vidarbha (around Nagpur). Near zero or positive: the central Karnataka plateau, Goa and coastal Karnataka
(northern Western Ghats), the Punjab-Himachal fringe and the interior of Madhya Pradesh and Chhattisgarh. Large
parts of the east (Andhra Pradesh, Odisha, Telangana, Bihar) have too few birded squares for a window.
Karnataka's near-zero total hides a negative south and a positive middle; windows overlap, so neighbouring
circles share data and the map is a picture, not a test.
