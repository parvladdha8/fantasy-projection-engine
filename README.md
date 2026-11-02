# Fantasy Projection Engine

Weekly full-PPR fantasy football projections that try to beat a simple average by modeling situational effects, and that publicly grade themselves every week.

## Plain-English map of the project

| Folder / file | What it is |
|---|---|
| `CLAUDE.md` | The project's rulebook (goals, rigor rules, roadmap). |
| `DECISIONS.md` | Every modeling choice and why we made it. |
| `src/fantasy_projection_engine/` | The actual code. |
| `  data.py` | Downloads free NFL data (nflverse) and saves it locally. |
| `  scoring.py` | Turns box-score stats into full-PPR points. |
| `  quality.py` | Data-quality checks (duplicates, missing weeks, scoring matches, …). |
| `  baseline.py` | The naive baseline: weighted average of a player's past games. |
| `  metrics.py` | Error measures (MAE, RMSE). |
| `scripts/run_phase1.py` | Runs everything above and writes a report. |
| `tests/` | Automatic checks that the math is right and nothing peeks at the future. |
| `reports/phase1_report.md` | Latest results. |
| `data/` | Downloaded data (not saved to git; re-download any time). |

## How to run it (Terminal)

```bash
uv run python scripts/run_phase1.py --refresh   # download data + run everything
uv run python scripts/run_phase1.py             # rerun using already-downloaded data
uv run pytest                                   # run the tests
```

## Current status
Phase 1 (Foundation) complete. Baseline MAE on development seasons 2019–2023, Big-60-style pool: **6.75 points per player**.
