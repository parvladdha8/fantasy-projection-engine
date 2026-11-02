"""One call → every player's median, floor and ceiling, plus a step-by-step explanation.

CLAUDE.md model step 5 (explainability). This is the single entry point the website, the
in-season pipeline and the final 2025 test all use, so they all run exactly the same model.

The frozen model (settings in reports/opp_eff_params.json):

    mean projection  = opportunity × efficiency (v5): share of team volume × expected team volume
                       (history + betting lines) × shrunk efficiency × scoring-environment multiplier
    median           = b_pos × mean projection                    (v8m, LAD, walk-forward)
    floor / ceiling  = a + b·mean + c·mean·volatility, τ = 0.1/0.9 (v10, walk-forward)

Explanation = a waterfall. Starting from the baseline (recent average), each step switches ON one
more piece of the model, in the order the pieces earned their place, keeping every frozen setting:

    baseline      trailing weighted average of PPR points (the bar the model must beat)
    own           opportunity × efficiency from the player's own history (no team, no lines)
    team          volume = his share of the team's volume × team's expected volume (history only)
    lines_volume  team's expected volume also uses the betting lines (implied points, spread)
    eff_cal       efficiency × (1 + α): a general efficiency correction with NO game information
                  (the pre-registered v5-cal control; kept separate so the next step shows only
                  what the betting market adds)
    lines_eff     efficiency × (1 + α + β·(implied − ī)): the game's scoring environment
    median        mean → median (fantasy points are right-skewed; MAE rewards the median)

Each step's "delta" is the change it causes, so baseline + Σ deltas = median exactly.
Caveat (stated on the methodology page): a sequential waterfall depends on the ORDER of steps.
We use the adoption order, which matches how each feature was tested (each against the model
before it). An order-free alternative (Shapley values) would average over all 720 orders; it is
less transparent and was not needed.

No look-ahead: every piece only uses games before the one being projected, and every fitted map
(team volume, efficiency multiplier, median, floor/ceiling) is fitted on earlier seasons only.
"""

import json
from dataclasses import replace

import numpy as np
import pandas as pd

from . import TEST_SEASON
from .baseline import add_projection, prepare_games
from .betting import add_lines, build_team_lines
from .calibration import median_calibration, quantile_band, shrunk_volatility
from .data import PROJECT_ROOT, load_player_stats, load_players, load_schedules, load_snap_counts
from .opp_eff import COMPONENTS, CompParams, _share, add_components, project, team_projection
from .player_games import build_player_games
from .team_context import TEAM_COLS, add_team_totals, build_team_games
from .tuning import relevant_mask

CONFIG_PATH = PROJECT_ROOT / "reports" / "opp_eff_params.json"

STEPS = [  # (key, plain-English label), in waterfall order
    ("baseline", "recent average"),
    ("own", "role & efficiency (own history)"),
    ("team", "team context"),
    ("lines_volume", "betting lines: team volume"),
    ("eff_cal", "efficiency calibration"),
    ("lines_eff", "betting lines: scoring environment"),
    ("median", "median adjustment"),
]

# Model switches for each intermediate step (on top of the frozen settings)
_VARIANTS = {
    "own": dict(team=False, lines=False, eff_adj="none"),
    "team": dict(team=True, lines=False, eff_adj="none"),
    "lines_volume": dict(team=True, lines=True, eff_adj="none"),
    "eff_cal": dict(team=True, lines=True, eff_adj="cal"),
}

ID_COLS = ["player_id", "player_display_name", "position", "team", "season", "week", "game_id"]


def load_games(lines_transform=None) -> pd.DataFrame:
    """The player-game table every model uses (stats + snap-only zeros + team totals + betting lines)."""
    ps = load_player_stats()
    pg = build_player_games(ps, load_snap_counts(), load_players())
    lines = build_team_lines(load_schedules())
    if lines_transform is not None:
        lines = lines_transform(lines)
    pg = add_lines(add_team_totals(pg, build_team_games(ps)), lines)
    return add_components(prepare_games(pg))


def load_model(path=CONFIG_PATH) -> dict:
    """Read the frozen model. Refuses settings this code does not implement (no silent drift)."""
    raw = json.loads(path.read_text())
    if raw.get("final_calibration") != "lad_mult":
        raise ValueError(f"unsupported final_calibration: {raw.get('final_calibration')}")
    iv = raw.get("intervals", {})
    if iv.get("method") != "quantile_band" or iv.get("fit_rows") != "all player-games":
        raise ValueError(f"unsupported intervals config: {iv}")
    params = {c: CompParams(**raw[c]) for c in COMPONENTS} | {"other_hl": raw["other_hl"]}
    if any(p.vacated for c, p in params.items() if c in COMPONENTS):
        raise ValueError("vacated opportunity was rejected; it must not be switched on in the frozen model")
    return {"params": params, "baseline": raw["baseline_method"], "intervals": iv}


def _with(params: dict, **kw) -> dict:
    return {c: (replace(p, **kw) if c in COMPONENTS else p) for c, p in params.items()}


def predict(games: pd.DataFrame, model: dict | None = None, allow_test: bool = False) -> pd.DataFrame:
    """Median / floor / ceiling and the explanation for every player-game in `games`.

    games: output of load_games() (sorted by player, season, week). Rows for the season's later
    weeks never affect earlier weeks, so the table may hold any amount of future data.
    allow_test: rows from the 2025 test season are dropped unless this is True (rigor rule 4:
    the test season is looked at once, by the final-test script).

    Columns: ID_COLS, actual, step_<key> for each step (projection after that step),
    delta_<key> (change caused by that step), median, floor, ceiling, per-component detail
    (share, team volume, volume, efficiency, efficiency shrinkage, scoring-environment multiplier),
    volatility z, and `explanation` (one readable line).
    """
    model = load_model() if model is None else model
    g, p = games, model["params"]
    cache: dict = {}
    out = g[ID_COLS + ["actual", "implied", "margin"]].copy()

    out["step_baseline"] = add_projection(g, model["baseline"], "_b")["_b"].to_numpy()
    for key, kw in _VARIANTS.items():
        out[f"step_{key}"] = project(g, _with(p, **kw), cache)["proj"].to_numpy()
    full = project(g, p, cache)
    out["step_lines_eff"] = full["proj"].to_numpy()

    # Component detail of the final mean projection (what the site shows under "why")
    for c, opp in COMPONENTS.items():
        pc = p[c]
        out[f"share_{c}"] = _share(g, opp, pc, cache)
        out[f"team_vol_{c}"] = team_projection(g, TEAM_COLS[opp], pc.hl_team, cache, pc.lines, pc.team_reg)
        out[f"vol_{c}"] = full[f"vol_{c}"].to_numpy()
        out[f"eff_{c}"] = full[f"eff_{c}"].to_numpy()
        out[f"shrink_{c}"] = full[f"shrink_{c}"].to_numpy()  # 1 = fully league average, 0 = fully his own
        out[f"env_mult_{c}"] = cache.get(("eff_mult", c, pc.hl_eff, pc.k, pc.eff_adj), np.ones(len(g)))
        out[f"proj_{c}"] = full[f"proj_{c}"].to_numpy()
    out["proj_other"] = full["proj_other"].to_numpy()

    # Median: walk-forward, per position, fitted on fantasy-relevant player-games (as adopted)
    tmp = out[["season", "position", "actual"]].assign(raw=out["step_lines_eff"])
    out["step_median"], med_coefs = median_calibration(tmp, "raw", relevant_mask(g), "lad_mult")
    out["median_factor"] = _coef(out, med_coefs, "b")

    # Floor / ceiling: walk-forward quantile maps on ALL player-games, widened by volatility
    iv = model["intervals"]
    tmp["z"] = shrunk_volatility(g, iv["volatility"]["window"], iv["volatility"]["prior"]).to_numpy()
    every = np.ones(len(g), bool)
    floor = quantile_band(tmp, "raw", "z", every, iv["floor_tau"])[0]
    ceiling = quantile_band(tmp, "raw", "z", every, iv["ceiling_tau"])[0]
    out["volatility_z"] = tmp["z"].to_numpy()
    out["median"] = out["step_median"]
    out["floor"] = np.fmin(floor, out["median"])  # crossing fix; NaN stays NaN
    out["ceiling"] = np.fmax(ceiling, out["median"])
    out.loc[np.isnan(floor), "floor"] = np.nan
    out.loc[np.isnan(ceiling), "ceiling"] = np.nan

    prev = None
    for key, _ in STEPS:
        out[f"delta_{key}"] = out[f"step_{key}"] if prev is None else out[f"step_{key}"] - out[f"step_{prev}"]
        prev = key
    out["explanation"] = [explain(r) for r in out.itertuples()]

    if not allow_test:
        out = out[out["season"] != TEST_SEASON]
    return out


def _coef(out: pd.DataFrame, coefs: pd.DataFrame, col: str) -> np.ndarray:
    if coefs.empty:
        return np.full(len(out), np.nan)
    m = out[["season", "position"]].merge(coefs[["season", "position", col]], on=["season", "position"], how="left")
    return m[col].to_numpy()


def explain(r) -> str:
    """'recent average 17.2 → +1.1 role & efficiency … → median 15.4 (floor 7.0, ceiling 26.1)'."""
    vals = [getattr(r, f"step_{k}") for k, _ in STEPS]
    if not np.all(np.isfinite(vals)):
        return "no projection (no earlier games)" if not np.isfinite(vals[-1]) else "partial history: steps unavailable"
    parts = [f"{STEPS[0][1]} {vals[0]:.1f}"]
    parts += [f"{getattr(r, f'delta_{k}'):+.1f} {label}" for k, label in STEPS[1:]]
    s = " → ".join(parts) + f" → median {vals[-1]:.1f}"
    if np.isfinite(r.floor) and np.isfinite(r.ceiling):
        s += f" (floor {r.floor:.1f}, ceiling {r.ceiling:.1f})"
    return s


def explanation_table(pred: pd.DataFrame) -> pd.DataFrame:
    """Long format, one row per player-game per step (the shape the database / website will store)."""
    rows = []
    for i, (key, label) in enumerate(STEPS):
        rows.append(pred[["player_id", "season", "week", "game_id"]].assign(
            step_order=i, step=key, label=label, value=pred[f"step_{key}"], delta=pred[f"delta_{key}"]))
    return pd.concat(rows, ignore_index=True).sort_values(["season", "week", "player_id", "step_order"], ignore_index=True)
