# Feature log

Every candidate feature, kept or rejected (rigor rule 3). Evaluated on development seasons 2019–2023 unless noted. "Diff" = new − old MAE (negative = better). CI = 95% paired week-clustered bootstrap.

| Date | Feature | Pool | MAE before | MAE after | Diff | 95% CI | Verdict |
|---|---|---|---|---|---|---|---|
| 2026-11-01 | Snap-count zero games in history | Big-60 (union) | 6.762 | 6.743 | −0.019 | [−0.030, −0.009] | ✅ Kept |
| 2026-11-01 | Snap-count zero games in history | All players | 4.569 | 4.426 | −0.143 | [−0.151, −0.136] | ✅ Kept |

## Baseline weighting choices (dev seasons, Big-60 pool, complete data)

| Method | MAE | Verdict |
|---|---|---|
| EWMA half-life 8 games | 6.759 | ✅ Chosen |
| EWMA half-life 16 | 6.761 | ❌ Tied, not chosen (pre-stated rule: lowest MAE) |
| EWMA half-life 4 | 6.888 | ❌ |
| Career mean | 6.907 | ❌ |
| Last-8 mean | 7.025 | ❌ |
| EWMA half-life 2 | 7.242 | ❌ |
| Last-3 mean | 7.875 | ❌ |
| Last game | 10.214 | ❌ |
