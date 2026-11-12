"""First-start QB projection: estimate on 2018–2023, validate once on 2024 (never 2025). Writes reports/debuts.json.
Usage: uv run python scripts/estimate_debuts.py"""

import json

from fantasy_projection_engine.data import load_player_stats, load_players, load_schedules, load_snap_counts
from fantasy_projection_engine.debuts import FILE, estimate, first_starts, validate
from fantasy_projection_engine.player_games import build_player_games


def main():
    players = load_players()
    pg = build_player_games(load_player_stats(), load_snap_counts(), players)
    first = first_starts(load_schedules(), pg, players)
    est = estimate(first, range(2018, 2024))
    val = validate(first, est, 2024)
    # Comparison on the same 2024 starts: the average of ALL QB starts 2018–2023 (what you'd use with no
    # "first start" information). The first-start estimate must beat it to earn its place.
    from fantasy_projection_engine.debuts import starting_qbs
    allq = starting_qbs(load_schedules()).merge(pg[["game_id", "player_id", "fantasy_points_ppr"]], on=["game_id", "player_id"], how="left")
    allq_med = float(allq.loc[allq["season"].between(2018, 2023), "fantasy_points_ppr"].fillna(0).median())
    x = first.loc[first["season"] == 2024, "fantasy_points_ppr"]
    val["mae_all_qb_starts_median"] = float((x - allq_med).abs().mean())
    val["all_qb_starts_median"] = allq_med
    FILE.write_text(json.dumps({"estimate": est, "validation_2024": val,
                                "starts_2024": first.loc[first["season"] == 2024, ["player_id", "week", "fantasy_points_ppr"]].to_dict("records")}, indent=2))
    print(json.dumps({"estimate": est, "validation_2024": val}, indent=2))


if __name__ == "__main__":
    main()
