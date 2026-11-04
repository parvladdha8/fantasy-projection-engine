"""Project the next unplayed week of the live season (local only; nothing is published).

Writes data/live/<season>/<pull>/projections_week<W>.parquet next to the data it was built from.
Usage: uv run python scripts/project_live.py [season]
"""

import sys

from fantasy_projection_engine import LIVE_SEASON
from fantasy_projection_engine.data import latest_live
from fantasy_projection_engine.live import live_games
from fantasy_projection_engine.predict import predict

season = int(sys.argv[1]) if len(sys.argv) > 1 else LIVE_SEASON
pull = latest_live(season)
games, week, excluded, src = live_games(season, pull=pull)
pred = predict(games, allow_test=True)
pred = pred[(pred.season == season) & (pred.week == week)].sort_values("median", ascending=False)
out = pull / f"projections_week{week:02d}.parquet"
pred.to_parquet(out)
print(f"data pull: {pull.name}   week {week}: {len(pred)} players projected, {pred['median'].isna().sum()} without a projection, "
      f"{len(excluded)} excluded (designated Out); team from: {src}")
print("saved to", out)
for pos, n in [("QB", 5), ("RB", 5), ("WR", 5), ("TE", 5)]:
    print(f"\n{pos}:")
    for r in pred[pred.position == pos].head(n).itertuples():
        print(f"  {r.player_display_name:<24} {r.team:<4} median {r.median:5.1f}  floor {r.floor:5.1f}  ceiling {r.ceiling:5.1f}")
print("\nexample explanation:", pred.iloc[0]["explanation"])
