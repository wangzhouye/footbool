"""
Unified Match Predictor — combines Elo ratings + Poisson model
to provide complete match predictions.

This is the primary interface consumed by all Streamlit pages.
"""

from typing import Dict, Optional, Tuple
import pandas as pd

from .elo import EloEngine
from .poisson_model import PoissonModel
from ..data.preprocessor import compute_attack_defense_strengths
from ..utils.config import FORM_WEIGHT


class MatchPredictor:
    """
    Unified prediction interface.

    Usage:
        predictor = MatchPredictor()
        predictor.load_historical_data(historical_df)  # train Elo from history
        result = predictor.predict("Argentina", "Brazil")
        # result contains win/draw/loss, expected goals, scoreline matrix, etc.
    """

    def __init__(self):
        self.elo = EloEngine()
        self.poisson = PoissonModel(rho=-0.08)
        self.historical_df: Optional[pd.DataFrame] = None
        self._trained = False

    def load_historical_data(self, df: pd.DataFrame):
        """
        Load and process historical match data.
        Updates Elo ratings by replaying all matches chronologically.
        """
        self.historical_df = df
        if not df.empty:
            self.elo.update_from_history(df)
        self._trained = True

    def get_team_elo(self, team: str) -> float:
        """Get current Elo rating."""
        return self.elo.get_rating(team)

    def get_all_elos(self) -> Dict[str, float]:
        """Get all Elo ratings."""
        return self.elo.get_all_ratings()

    def _compute_lambdas(self, home_team: str, away_team: str,
                         neutral: bool = True) -> Tuple[float, float]:
        """
        Compute expected goals (lambdas) for both teams.

        lambda = attack_strength * defense_weakness_opponent * league_avg * home_factor
        """
        if self.historical_df is not None and not self.historical_df.empty:
            avg_elo = self.elo.get_avg_rating()
            home_attack, home_defense = compute_attack_defense_strengths(
                home_team, self.elo.get_rating(home_team), avg_elo, self.historical_df
            )
            away_attack, away_defense = compute_attack_defense_strengths(
                away_team, self.elo.get_rating(away_team), avg_elo, self.historical_df
            )
        else:
            # Fallback: use Elo-only strengths
            elo_h = self.elo.get_rating(home_team)
            elo_a = self.elo.get_rating(away_team)
            avg = (elo_h + elo_a) / 2
            home_attack = max(0.5, min(2.0, 1.0 + (elo_h - avg) / 400))
            home_defense = max(0.5, min(2.0, 1.0 - (elo_h - avg) / 400))
            away_attack = max(0.5, min(2.0, 1.0 + (elo_a - avg) / 400))
            away_defense = max(0.5, min(2.0, 1.0 - (elo_a - avg) / 400))

        return self.poisson.expected_goals(
            home_attack, away_defense,
            away_attack, home_defense,
            home_advantage=not neutral,
        )

    def predict(self, home_team: str, away_team: str,
                neutral: bool = True) -> Dict:
        """
        Predict a single match.

        Args:
            home_team: Name of home/nominal home team
            away_team: Name of away/nominal away team
            neutral: True if match is at neutral venue

        Returns:
            Dict with all prediction details
        """
        lambda_h, lambda_a = self._compute_lambdas(home_team, away_team, neutral)

        # Poisson-based match probabilities
        poisson_probs = self.poisson.match_probabilities(lambda_h, lambda_a)

        # Elo-based probabilities (for comparison / blending)
        elo_probs = self.elo.win_probability(home_team, away_team, neutral)

        # Blend: 70% Poisson, 30% Elo
        blended = {
            "home_win": round(0.7 * poisson_probs["home_win"] + 0.3 * elo_probs["home_win"], 4),
            "draw": round(0.7 * poisson_probs["draw"] + 0.3 * elo_probs["draw"], 4),
            "away_win": round(0.7 * poisson_probs["away_win"] + 0.3 * elo_probs["away_win"], 4),
        }

        return {
            "home_team": home_team,
            "away_team": away_team,
            "neutral": neutral,
            "elo_home": round(self.elo.get_rating(home_team), 1),
            "elo_away": round(self.elo.get_rating(away_team), 1),
            "elo_diff": round(self.elo.get_rating(home_team) - self.elo.get_rating(away_team), 1),
            # Blended probabilities
            "home_win": blended["home_win"],
            "draw": blended["draw"],
            "away_win": blended["away_win"],
            # Poisson details
            "expected_home_goals": poisson_probs["expected_home_goals"],
            "expected_away_goals": poisson_probs["expected_away_goals"],
            "total_expected_goals": poisson_probs["total_expected_goals"],
            "most_likely_score": poisson_probs["most_likely_score"],
            "most_likely_prob": poisson_probs["most_likely_prob"],
            "scoreline_matrix": poisson_probs["scoreline_matrix"],
            # Markets
            "over_2_5": poisson_probs["over_2_5"],
            "under_2_5": poisson_probs["under_2_5"],
            "btts_yes": poisson_probs["btts_yes"],
            "btts_no": poisson_probs["btts_no"],
        }

    def _compute_lambdas_fast(self, home_team: str, away_team: str,
                              neutral: bool = True) -> Tuple[float, float]:
        """
        Fast Elo-only lambda computation for Monte Carlo.
        Skips expensive form calculations.
        """
        elo_h = self.elo.get_rating(home_team)
        elo_a = self.elo.get_rating(away_team)
        avg = (elo_h + elo_a) / 2

        home_attack = max(0.5, min(2.0, 1.0 + (elo_h - avg) / 400))
        home_defense = max(0.5, min(2.0, 1.0 - (elo_h - avg) / 400))
        away_attack = max(0.5, min(2.0, 1.0 + (elo_a - avg) / 400))
        away_defense = max(0.5, min(2.0, 1.0 - (elo_a - avg) / 400))

        return self.poisson.expected_goals(
            home_attack, away_defense,
            away_attack, home_defense,
            home_advantage=not neutral,
        )

    def simulate_goals(self, home_team: str, away_team: str,
                       neutral: bool = True) -> Tuple[int, int]:
        """
        Simulate a single match outcome (for Monte Carlo).
        Returns (home_goals, away_goals).
        """
        import numpy as np
        lambda_h, lambda_a = self._compute_lambdas_fast(home_team, away_team, neutral)
        home_goals = np.random.poisson(lambda_h)
        away_goals = np.random.poisson(lambda_a)
        return home_goals, away_goals
