# Phase 1 report

## Data-quality checks

- **PASS**: No duplicate player-weeks. 0 rows share a (player, season, week, type) key
- **PASS**: Key fields present (skill positions). missing counts: {'player_id': 0, 'position': 0, 'team': 0, 'game_id': 0, 'fantasy_points_ppr': 0}
- **PASS**: All regular-season weeks present. every season has all expected weeks
- **PASS**: Our PPR formula matches nflverse. 0 of 47788 skill rows differ by >0.01 pts (max diff 0.00)
- **PASS**: Stats line up with schedule. 0 scheduled team-games with no player rows; 0 stat team-games not in schedule
- **PASS**: 32 teams per season. all seasons have 32
- **PASS**: Points plausible (hard limits -15 to 80). 0 impossible rows. Range -6.7 to 57.9. Reviewed extremes (verified real): Sam Darnold 2019 wk7 (-6.7), Tyreek Hill 2020 wk12 (57.9), Alvin Kamara 2020 wk16 (56.2), Ja'Marr Chase 2021 wk17 (55.6), Joe Mixon 2022 wk9 (55.1), Ja'Marr Chase 2024 wk10 (55.4), Jahmyr Gibbs 2025 wk12 (55.4)
- **PASS**: INFO: zero-point games. 15.7% of skill-position rows score exactly 0. Rows only exist when a player records a stat; snap-count zero games are added separately in player_games.py
- **PASS**: Snap-count player IDs map to nflverse (>= 99.5%). 99.84% of 53174 skill-position snap rows mapped

## Baseline variants, development seasons 2019–2023

### Pool: big60

| method | n | mae | rmse | spearman |
|---|---|---|---|---|
| ewma_hl8 | 5280 | 6.759 | 8.483 | 0.346 |
| ewma_hl16 | 5280 | 6.761 | 8.499 | 0.346 |
| ewma_hl4 | 5280 | 6.888 | 8.597 | 0.335 |
| career_mean | 5280 | 6.907 | 8.649 | 0.339 |
| last8_mean | 5280 | 7.025 | 8.717 | 0.331 |
| ewma_hl2 | 5280 | 7.242 | 8.953 | 0.313 |
| last3_mean | 5280 | 7.875 | 9.625 | 0.295 |
| last_game | 5280 | 10.214 | 12.414 | 0.252 |

### Pool: all

| method | n | mae | rmse | spearman |
|---|---|---|---|---|
| ewma_hl4 | 31661 | 4.346 | 6.121 | 0.691 |
| ewma_hl2 | 31661 | 4.379 | 6.232 | 0.688 |
| ewma_hl8 | 31661 | 4.385 | 6.133 | 0.684 |
| last8_mean | 31661 | 4.406 | 6.230 | 0.679 |
| ewma_hl16 | 31661 | 4.441 | 6.193 | 0.674 |
| career_mean | 31661 | 4.536 | 6.321 | 0.656 |
| last3_mean | 31661 | 4.586 | 6.587 | 0.661 |
| last_game | 31661 | 5.295 | 7.863 | 0.595 |

### Big-60 pool MAE by position

|  | QB | RB | WR | TE |
|---|---|---|---|---|
| ewma_hl8 | 6.674 | 6.808 | 7.261 | 5.744 |
| ewma_hl16 | 6.641 | 6.844 | 7.274 | 5.691 |
| career_mean | 6.752 | 7.047 | 7.409 | 5.778 |
| ewma_hl4 | 6.642 | 6.871 | 7.485 | 5.978 |
| last8_mean | 6.831 | 7.043 | 7.527 | 6.176 |
| ewma_hl2 | 6.994 | 7.150 | 7.928 | 6.303 |
| last3_mean | 7.525 | 7.734 | 8.612 | 7.034 |
| last_game | 9.547 | 9.615 | 11.677 | 9.150 |
