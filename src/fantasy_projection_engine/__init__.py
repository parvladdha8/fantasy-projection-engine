"""Fantasy Projection Engine — redraft full-PPR weekly projections."""

SKILL_POSITIONS = ("QB", "RB", "WR", "TE")
SEASONS = list(range(2018, 2026))  # 2018–2025 inclusive

# Holdout discipline (CLAUDE.md rigor rule 4)
BURN_IN_SEASONS = [2018]                       # history only; never scored
DEV_SEASONS = [2019, 2020, 2021, 2022, 2023]   # tune here
VALIDATION_SEASON = 2024                       # check once tuning is done
TEST_SEASON = 2025                             # touch exactly once, at the end
