# Phase 1 report

## Data-quality checks

- **PASS**: No duplicate player-weeks. 0 rows share a (player, season, week, type) key
- **PASS**: Key fields present (skill positions). missing counts: {'player_id': 0, 'position': 0, 'team': 0, 'game_id': 0, 'fantasy_points_ppr': 0}
- **PASS**: All regular-season weeks present. every season has all expected weeks
- **PASS**: Our PPR formula matches nflverse. 0 of 47788 skill rows differ by >0.01 pts (max diff 0.00)
- **PASS**: Stats line up with schedule. 0 scheduled team-games with no player rows; 0 stat team-games not in schedule
- **PASS**: 32 teams per season. all seasons have 32
- **PASS**: Points plausible (hard limits -15 to 80). 0 impossible rows. Range -6.7 to 57.9. Reviewed extremes (verified real): Sam Darnold 2019 wk7 (-6.7), Tyreek Hill 2020 wk12 (57.9), Alvin Kamara 2020 wk16 (56.2), Ja'Marr Chase 2021 wk17 (55.6), Joe Mixon 2022 wk9 (55.1), Ja'Marr Chase 2024 wk10 (55.4), Jahmyr Gibbs 2025 wk12 (55.4)
- **PASS**: INFO: zero-point games. 15.7% of skill-position rows score exactly 0. Rows only exist when a player records a stat, so active players with no touches are mostly absent (see DECISIONS.md)

## Baseline variants, development seasons 2019–2023

### Pool: big60

| method | n | mae | rmse | spearman |
|---|---|---|---|---|
| ewma_hl8 | 5280 | 6.745 | 8.455 | 0.346 |
| ewma_hl16 | 5280 | 6.760 | 8.486 | 0.350 |
| ewma_hl4 | 5280 | 6.864 | 8.561 | 0.338 |
| career_mean | 5280 | 6.895 | 8.641 | 0.337 |
| last8_mean | 5280 | 6.997 | 8.678 | 0.332 |
| ewma_hl2 | 5280 | 7.222 | 8.913 | 0.313 |
| last3_mean | 5280 | 7.850 | 9.593 | 0.297 |
| last_game | 5280 | 10.158 | 12.358 | 0.248 |

### Pool: all

| method | n | mae | rmse | spearman |
|---|---|---|---|---|
| ewma_hl4 | 27763 | 4.726 | 6.435 | 0.645 |
| ewma_hl8 | 27763 | 4.752 | 6.436 | 0.640 |
| ewma_hl2 | 27763 | 4.777 | 6.560 | 0.640 |
| last8_mean | 27763 | 4.792 | 6.544 | 0.632 |
| ewma_hl16 | 27763 | 4.798 | 6.487 | 0.631 |
| career_mean | 27763 | 4.880 | 6.600 | 0.615 |
| last3_mean | 27763 | 5.018 | 6.934 | 0.609 |
| last_game | 27763 | 5.841 | 8.296 | 0.534 |

### Big-60 pool MAE by position

|  | QB | RB | WR | TE |
|---|---|---|---|---|
| ewma_hl8 | 6.658 | 6.788 | 7.259 | 5.715 |
| ewma_hl16 | 6.639 | 6.822 | 7.263 | 5.747 |
| career_mean | 6.729 | 7.008 | 7.424 | 5.780 |
| ewma_hl4 | 6.640 | 6.861 | 7.442 | 5.935 |
| last8_mean | 6.815 | 7.015 | 7.510 | 6.116 |
| ewma_hl2 | 6.994 | 7.128 | 7.871 | 6.338 |
| last3_mean | 7.525 | 7.720 | 8.568 | 6.997 |
| last_game | 9.525 | 9.579 | 11.604 | 9.054 |
