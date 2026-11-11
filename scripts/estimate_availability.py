"""Estimate the chance of playing for each injury-report state, from 2018–2023 (development seasons only; rigor rule 4).
Writes reports/availability.json, which live projections read. Rules: DECISIONS.md 2026-11-11.

Usage: uv run python scripts/estimate_availability.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fantasy_projection_engine.availability import LABEL, estimate_play_rates
from fantasy_projection_engine.data import load_injuries, load_player_stats, load_players, load_rosters_weekly, load_snap_counts
from fantasy_projection_engine.grading import evidence_of_play

SEASONS = range(2018, 2024)
OUT = Path(__file__).resolve().parents[1] / "reports" / "availability.json"


def main():
    stats, snaps, players = load_player_stats(), load_snap_counts(), load_players()
    played = {(s, int(w)): evidence_of_play(stats, snaps, players, s, int(w))
              for s, w in stats.loc[stats["season"].isin(SEASONS), ["season", "week"]].drop_duplicates().itertuples(index=False)}
    r = estimate_play_rates(load_injuries(), played, load_rosters_weekly(), SEASONS)
    r = r.sort_values("p_play")
    for x in r.itertuples():
        print(f"{LABEL[x.state]:<22} n={x.n:>6}  played {x.played:>6}  → {x.p_play:6.1%}")
    OUT.write_text(json.dumps({"seasons": [min(SEASONS), max(SEASONS)],
                               "p_play": {x.state: round(float(x.p_play), 4) for x in r.itertuples()},
                               "n": {x.state: int(x.n) for x in r.itertuples()}}, indent=2) + "\n")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
