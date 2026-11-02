# Prediction function check (real data, development seasons only)

| check | result |
|---|---|
| 1. No look-ahead: 2023 week 10 with vs without every later game (348 players) | max difference 0.0e+00 points, same missing values: True → PASS |
| 2. Mean projection = frozen v5 (the model validated on 2024) | PASS |
| 3. Waterfall adds up to the median (36,793 player-games, 2018–2023) | max error 1.8e-15 → PASS |
| Coverage of the explanation | 95.7% of player-games (the rest are first career games: no history) |

## Average size of each step, 2020–2023, by position (points; descriptive)

| position | role & efficiency (own history) | team context | betting lines: team volume | efficiency calibration | betting lines: scoring environment | median adjustment |
|---|---|---|---|---|---|---|
| QB | +0.24 (±1.18) | +0.02 (±0.67) | -0.12 (±0.44) | -0.57 (±0.57) | -0.12 (±0.80) | +0.32 (±0.32) |
| RB | +0.04 (±0.76) | -0.02 (±0.25) | -0.04 (±0.24) | -0.04 (±0.06) | -0.06 (±0.30) | -0.98 (±0.98) |
| WR | +0.07 (±0.69) | -0.05 (±0.27) | -0.05 (±0.29) | -0.18 (±0.18) | -0.05 (±0.28) | -0.46 (±0.46) |
| TE | +0.00 (±0.47) | -0.00 (±0.14) | -0.02 (±0.18) | -0.11 (±0.11) | -0.03 (±0.16) | -0.33 (±0.33) |

Each cell: average change (average size of the change). A step can matter a lot for individual players while averaging near zero.

## Examples: 2023 week 10, top 3 median projections per position

- **Josh Allen** (QB, BUF), actual 14.4: recent average 23.9 → -1.3 role & efficiency (own history) → +0.4 team context → +0.4 betting lines: team volume → -0.8 efficiency calibration → +1.4 betting lines: scoring environment → +0.4 median adjustment → median 24.4 (floor 12.5, ceiling 34.4)
  - rush: 7.8 carries × 1.00 pts (share 29% of 26.6; efficiency 47% shrunk to league average); pass: 35.4 attempts × 0.47 pts (share 99% of 35.8; efficiency 32% shrunk to league average)
- **Dak Prescott** (QB, DAL), actual 37.9: recent average 18.5 → -0.1 role & efficiency (own history) → +0.0 team context → -0.7 betting lines: team volume → -0.7 efficiency calibration → +1.3 betting lines: scoring environment → +0.3 median adjustment → median 18.5 (floor 8.1, ceiling 28.8)
  - rush: 5.2 carries × 0.69 pts (share 17% of 30.8; efficiency 59% shrunk to league average); pass: 31.9 attempts × 0.47 pts (share 97% of 32.8; efficiency 33% shrunk to league average)
- **Joe Burrow** (QB, CIN), actual 19.9: recent average 18.7 → +0.4 role & efficiency (own history) → -0.7 team context → -0.2 betting lines: team volume → -0.8 efficiency calibration → +0.6 betting lines: scoring environment → +0.3 median adjustment → median 18.2 (floor 7.8, ceiling 28.6)
  - rush: 4.6 carries × 0.62 pts (share 18% of 25.5; efficiency 59% shrunk to league average); pass: 35.6 attempts × 0.43 pts (share 100% of 35.8; efficiency 31% shrunk to league average)
- **Christian McCaffrey** (RB, SF), actual 20.2: recent average 23.4 → -2.6 role & efficiency (own history) → +0.7 team context → +0.2 betting lines: team volume → -0.3 efficiency calibration → +0.1 betting lines: scoring environment → -2.7 median adjustment → median 18.9 (floor 6.9, ceiling 33.2)
  - rec: 5.7 targets × 1.72 pts (share 19% of 29.6; efficiency 30% shrunk to league average); rush: 15.8 carries × 0.75 pts (share 55% of 28.5; efficiency 26% shrunk to league average)
- **Austin Ekeler** (RB, LAC), actual 21.5: recent average 19.9 → -0.3 role & efficiency (own history) → +0.5 team context → -0.2 betting lines: team volume → -0.3 efficiency calibration → -0.1 betting lines: scoring environment → -2.5 median adjustment → median 17.0 (floor 6.1, ceiling 30.4)
  - rec: 6.0 targets × 1.65 pts (share 17% of 35.7; efficiency 29% shrunk to league average); rush: 13.8 carries × 0.71 pts (share 55% of 25.2; efficiency 29% shrunk to league average)
- **Jahmyr Gibbs** (RB, DET), actual 26.2: recent average 17.2 → +1.8 role & efficiency (own history) → -1.3 team context → -0.5 betting lines: team volume → -0.2 efficiency calibration → +0.4 betting lines: scoring environment → -2.2 median adjustment → median 15.2 (floor 4.1, ceiling 30.5)
  - rec: 5.5 targets × 1.48 pts (share 16% of 34.3; efficiency 76% shrunk to league average); rush: 13.3 carries × 0.69 pts (share 47% of 28.1; efficiency 44% shrunk to league average)
- **Ja'Marr Chase** (WR, CIN), actual 23.4: recent average 19.9 → +0.7 role & efficiency (own history) → -0.0 team context → -0.8 betting lines: team volume → -0.6 efficiency calibration → +0.5 betting lines: scoring environment → -1.5 median adjustment → median 18.2 (floor 4.6, ceiling 34.5)
  - rec: 10.4 targets × 1.87 pts (share 30% of 35.2; efficiency 28% shrunk to league average)
- **Stefon Diggs** (WR, BUF), actual 6.4: recent average 19.8 → -0.8 role & efficiency (own history) → -0.0 team context → +0.0 betting lines: team volume → -0.6 efficiency calibration → +0.9 betting lines: scoring environment → -1.5 median adjustment → median 17.8 (floor 5.4, ceiling 32.7)
  - rec: 10.0 targets × 1.94 pts (share 29% of 34.1; efficiency 21% shrunk to league average)
- **Amon-Ra St. Brown** (WR, DET), actual 30.5: recent average 18.2 → -0.0 role & efficiency (own history) → -0.4 team context → +0.1 betting lines: team volume → -0.5 efficiency calibration → +0.4 betting lines: scoring environment → -1.4 median adjustment → median 16.3 (floor 5.2, ceiling 30.0)
  - rec: 10.0 targets × 1.76 pts (share 29% of 34.3; efficiency 29% shrunk to league average)
- **Sam LaPorta** (TE, DET), actual 8.0: recent average 14.0 → -0.3 role & efficiency (own history) → -0.4 team context → +0.1 betting lines: team volume → -0.4 efficiency calibration → +0.3 betting lines: scoring environment → -1.1 median adjustment → median 12.1 (floor 1.9, ceiling 23.3)
  - rec: 7.4 targets × 1.79 pts (share 22% of 34.3; efficiency 64% shrunk to league average)
- **George Kittle** (TE, SF), actual 20.6: recent average 13.6 → -0.7 role & efficiency (own history) → -0.1 team context → +0.7 betting lines: team volume → -0.4 efficiency calibration → +0.0 betting lines: scoring environment → -1.1 median adjustment → median 12.0 (floor 1.5, ceiling 24.6)
  - rec: 6.6 targets × 1.98 pts (share 22% of 29.6; efficiency 29% shrunk to league average)
- **Mark Andrews** (TE, BAL), actual 6.4: recent average 14.5 → -1.1 role & efficiency (own history) → -0.1 team context → -0.1 betting lines: team volume → -0.4 efficiency calibration → -0.2 betting lines: scoring environment → -1.1 median adjustment → median 11.6 (floor 2.1, ceiling 21.3)
  - rec: 6.9 targets × 1.82 pts (share 24% of 28.3; efficiency 26% shrunk to league average)
