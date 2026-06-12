"""
Preprocessor — feature engineering for the prediction models.
Computes recent form, rolling averages, attack/defense strengths.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..utils.config import TIME_HALF_LIFE_YEARS, LEAGUE_AVG_HOME_GOALS, LEAGUE_AVG_AWAY_GOALS


def compute_match_weight(match_date: datetime, reference_date: datetime = None) -> float:
    """
    Compute time-decay weight for a match.
    Half-life = 4 years (World Cup cycle).
    More recent matches get higher weight.
    """
    if reference_date is None:
        reference_date = datetime.now()

    age_years = abs((reference_date - match_date).days) / 365.25
    weight = np.exp(-np.log(2) * age_years / TIME_HALF_LIFE_YEARS)
    return weight


def compute_team_form(historical_df: pd.DataFrame, team: str,
                      reference_date: datetime = None, n_matches: int = 10) -> dict:
    """
    Compute recent form metrics for a team.

    Returns dict with:
    - avg_goals_for: weighted average goals scored
    - avg_goals_against: weighted average goals conceded
    - recent_results: list of recent (date, opponent, score, weight)
    - elo_form_boost: form-based Elo adjustment
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Filter matches involving this team
    home_matches = historical_df[historical_df["home_team"] == team].copy()
    away_matches = historical_df[historical_df["away_team"] == team].copy()

    # Combine
    matches = []
    for _, row in home_matches.iterrows():
        matches.append({
            "date": row["date"],
            "opponent": row["away_team"],
            "goals_for": row["home_score"],
            "goals_against": row["away_score"],
            "home": True,
        })
    for _, row in away_matches.iterrows():
        matches.append({
            "date": row["date"],
            "opponent": row["home_team"],
            "goals_for": row["away_score"],
            "goals_against": row["home_score"],
            "home": False,
        })

    if not matches:
        return {
            "avg_goals_for": LEAGUE_AVG_HOME_GOALS,
            "avg_goals_against": LEAGUE_AVG_AWAY_GOALS,
            "recent_results": [],
            "elo_form_boost": 0.0,
        }

    # Sort by date descending, take recent N
    matches_df = pd.DataFrame(matches)
    matches_df = matches_df.sort_values("date", ascending=False).head(n_matches * 2)

    # Apply time weights
    matches_df["weight"] = matches_df["date"].apply(
        lambda d: compute_match_weight(d, reference_date)
    )

    # Weighted averages
    total_weight = matches_df["weight"].sum()
    if total_weight == 0:
        total_weight = 1.0

    avg_gf = (matches_df["goals_for"] * matches_df["weight"]).sum() / total_weight
    avg_ga = (matches_df["goals_against"] * matches_df["weight"]).sum() / total_weight

    # Form boost based on performance above/below baseline
    # Weighted goal difference scaled to Elo points
    weighted_gd = ((matches_df["goals_for"] - matches_df["goals_against"]) *
                   matches_df["weight"]).sum() / total_weight
    elo_form_boost = weighted_gd * 15  # ~15 Elo per goal difference

    # Recent results for display
    recent = []
    for _, row in matches_df.head(n_matches).iterrows():
        is_win = row["goals_for"] > row["goals_against"]
        is_draw = row["goals_for"] == row["goals_against"]
        result = "W" if is_win else ("D" if is_draw else "L")
        recent.append({
            "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
            "opponent": row["opponent"],
            "score": f"{int(row['goals_for'])}-{int(row['goals_against'])}",
            "result": result,
            "weight": round(row["weight"], 3),
        })

    return {
        "avg_goals_for": round(avg_gf, 2),
        "avg_goals_against": round(avg_ga, 2),
        "recent_results": recent,
        "elo_form_boost": round(elo_form_boost, 1),
    }


def compute_attack_defense_strengths(team: str, team_elo: float,
                                     avg_elo: float,
                                     historical_df: pd.DataFrame) -> tuple:
    """
    Compute attack and defense strengths for a team.
    Blends Elo prior (60%) with recent form (40%).

    Returns (attack_strength, defense_strength).
    """
    form = compute_team_form(historical_df, team)

    # Elo-based expected goals
    elo_diff = team_elo - avg_elo
    elo_attack = 1.0 + elo_diff / 400.0
    elo_defense = 1.0 - elo_diff / 400.0  # Higher Elo = better defense (lower multiplier)

    # Form-based — 用主客场综合均值归一化（form 包含主客场所有比赛）
    league_avg_goals = (LEAGUE_AVG_HOME_GOALS + LEAGUE_AVG_AWAY_GOALS) / 2.0
    form_attack = form["avg_goals_for"] / league_avg_goals
    form_defense = form["avg_goals_against"] / league_avg_goals

    # Blend
    attack = 0.6 * elo_attack + 0.4 * form_attack
    defense = 0.6 * elo_defense + 0.4 * form_defense

    # Clamp to reasonable range
    attack = max(0.5, min(2.0, attack))
    defense = max(0.5, min(2.0, defense))

    return round(attack, 3), round(defense, 3)
