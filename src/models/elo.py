"""
Elo Rating Engine for international football.
Handles initialization, expected result, and rating updates
with goal-difference weighting and tournament K-factors.
"""

import math
from typing import Dict, Optional

from ..utils.config import (
    ELO_DEFAULT, ELO_HOME_ADVANTAGE, HOSTS,
    K_WORLD_CUP, K_QUALIFIER, K_FRIENDLY,
    goal_diff_multiplier, TEAMS,
)


class EloEngine:
    """
    Elo rating system adapted for football.

    Features:
    - Goal-difference weighted K-factor
    - Home advantage (+100 Elo for host nations at home)
    - Tournament-class K-factors (WC > Qualifier > Friendly)
    - Dynamic updates from match results
    """

    def __init__(self):
        """Initialize Elo ratings from config seeds."""
        self.ratings: Dict[str, float] = {}
        self._initialize_from_config()

    def _initialize_from_config(self):
        """Seed Elo ratings from team config."""
        for team, info in TEAMS.items():
            self.ratings[team] = float(info.get("elo_seed", ELO_DEFAULT))

    def get_rating(self, team: str) -> float:
        """Get current Elo rating for a team."""
        return self.ratings.get(team, ELO_DEFAULT)

    def set_rating(self, team: str, rating: float):
        """Set Elo rating for a team."""
        self.ratings[team] = rating

    def expected_result(self, team_a: str, team_b: str,
                        neutral: bool = True) -> float:
        """
        Calculate expected win probability for team_a vs team_b.
        400 Elo points difference = 10x odds ratio.

        Returns P(team_a wins) [0, 1].
        This is the expected score, not win prob (draw not yet separated).
        """
        rating_a = self.get_rating(team_a)
        rating_b = self.get_rating(team_b)

        # Home advantage for host nations
        if not neutral and team_a in HOSTS:
            rating_a += ELO_HOME_ADVANTAGE

        return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))

    def win_probability(self, team_a: str, team_b: str,
                        neutral: bool = True) -> Dict[str, float]:
        """
        Estimate win/draw/loss probabilities from Elo difference.

        Uses an approximation: draws are most likely when Elo difference
        is small. The draw probability peaks at ~29% for equal-rated teams.

        Returns: {"home_win": float, "draw": float, "away_win": float}
        """
        expected = self.expected_result(team_a, team_b, neutral)
        elo_diff = abs(self.get_rating(team_a) - self.get_rating(team_b))

        # Draw probability based on Elo difference
        # Empirical formula: draw_prob peaks at ~0.29 for equal teams
        draw_prob = 0.29 * math.exp(-elo_diff / 300.0)

        if expected >= 0.5:
            home_win = expected - draw_prob * expected
            away_win = 1.0 - home_win - draw_prob
        else:
            away_win = (1.0 - expected) - draw_prob * (1.0 - expected)
            home_win = 1.0 - away_win - draw_prob

        # Ensure non-negative
        home_win = max(0.0, home_win)
        draw = max(0.0, draw_prob)
        away_win = max(0.0, away_win)

        # Normalize
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total

        return {
            "home_win": round(home_win, 4),
            "draw": round(draw, 4),
            "away_win": round(away_win, 4),
        }

    def update(self, team_a: str, team_b: str, goals_a: int, goals_b: int,
               tournament: str = "World Cup", neutral: bool = True):
        """
        Update Elo ratings after a match.

        Args:
            team_a: Home/nominal home team
            team_b: Away/nominal away team
            goals_a: Goals scored by team_a
            goals_b: Goals scored by team_b
            tournament: 'World Cup', 'WC Qualifier', 'Continental Cup',
                       'Nations League', or 'Friendly'
            neutral: True if match at neutral venue
        """
        rating_a = self.get_rating(team_a)
        rating_b = self.get_rating(team_b)

        # Add home advantage for non-neutral host matches
        effective_a = rating_a
        if not neutral and team_a in HOSTS:
            effective_a += ELO_HOME_ADVANTAGE

        # Expected result
        expected_a = 1.0 / (1.0 + math.pow(10.0, (rating_b - effective_a) / 400.0))
        expected_b = 1.0 - expected_a

        # Actual result
        if goals_a > goals_b:
            actual_a, actual_b = 1.0, 0.0
        elif goals_a < goals_b:
            actual_a, actual_b = 0.0, 1.0
        else:
            actual_a, actual_b = 0.5, 0.5

        # K-factor by tournament
        if tournament == "World Cup":
            k = K_WORLD_CUP
        elif "Qualifier" in tournament:
            k = K_QUALIFIER
        else:
            k = K_FRIENDLY

        # Goal difference multiplier
        goal_diff = abs(goals_a - goals_b)
        gd_mult = goal_diff_multiplier(goal_diff)

        # Update ratings
        delta_a = k * gd_mult * (actual_a - expected_a)
        delta_b = k * gd_mult * (actual_b - expected_b)

        self.ratings[team_a] = rating_a + delta_a
        self.ratings[team_b] = rating_b + delta_b

    def update_from_history(self, matches_df):
        """
        Update Elo ratings by replaying historical matches in chronological order.

        Args:
            matches_df: DataFrame with columns:
                date, home_team, away_team, home_score, away_score, tournament, neutral
        """
        # Sort by date
        df = matches_df.sort_values("date")

        for _, row in df.iterrows():
            tournament = row.get("tournament", "Friendly")
            neutral = row.get("neutral", True)
            if isinstance(neutral, str):
                neutral = neutral.lower() == "true"

            self.update(
                team_a=row["home_team"],
                team_b=row["away_team"],
                goals_a=int(row["home_score"]),
                goals_b=int(row["away_score"]),
                tournament=tournament,
                neutral=neutral,
            )

    def get_all_ratings(self) -> Dict[str, float]:
        """Get all current Elo ratings, sorted highest to lowest."""
        return dict(sorted(self.ratings.items(), key=lambda x: x[1], reverse=True))

    def get_avg_rating(self) -> float:
        """Get average Elo rating across all teams."""
        if not self.ratings:
            return ELO_DEFAULT
        return sum(self.ratings.values()) / len(self.ratings)
