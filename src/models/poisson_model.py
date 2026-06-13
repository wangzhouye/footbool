"""
Poisson goal model for football match prediction.

Uses scipy-based Poisson distribution to model goals.
Computes expected goals from team attack/defense strengths,
then generates the full scoreline probability matrix.

Implements Dixon-Coles style low-score adjustment.
"""

import numpy as np
from scipy.stats import poisson
from typing import Dict, List, Tuple, Optional

from ..utils.config import (
    LEAGUE_AVG_HOME_GOALS, LEAGUE_AVG_AWAY_GOALS,
    MAX_GOALS, ELO_TO_GOALS_FACTOR,
)


class PoissonModel:
    """
    Poisson goal model for football match prediction.

    Models goals scored by each team as independent Poisson processes.
    The joint probability of scorelines is the outer product of the PMFs.

    A Dixon-Coles style correction adjusts low-score probabilities
    (0-0, 1-0, 0-1, 1-1) to correct the Poisson model's known
    tendency to underpredict draws.
    """

    def __init__(self, rho: float = -0.10):
        """
        Args:
            rho: Dixon-Coles dependence parameter.
                 Typically -0.03 to -0.15 for international football.
                 Negative values increase probability of low-scoring draws.
        """
        self.rho = rho
        self._rho_cache = {}  # 缓存动态 rho 值

    def compute_dynamic_rho(self, match_importance: str = "Friendly",
                           team_quality_diff: float = 0.0) -> float:
        """
        根据比赛重要性和队伍质量差异动态调整 rho

        Args:
            match_importance: 比赛重要性 ("World Cup", "Qualifier", "Friendly")
            team_quality_diff: 队伍质量差异 (Elo 差异 / 400)

        Returns:
            动态调整后的 rho 值
        """
        cache_key = f"{match_importance}_{team_quality_diff:.2f}"
        if cache_key in self._rho_cache:
            return self._rho_cache[cache_key]

        base_rho = self.rho

        # 比赛重要性调整
        if match_importance == "World Cup":
            importance_factor = 1.3  # 世界杯比赛更保守
        elif "Qualifier" in match_importance:
            importance_factor = 1.1  # 预选赛稍保守
        else:
            importance_factor = 1.0  # 友谊赛正常

        # 队伍质量差异调整
        # 质量差异越大，低比分概率越低
        quality_factor = 1.0 - abs(team_quality_diff) * 0.1
        quality_factor = max(0.7, min(1.3, quality_factor))

        # 计算动态 rho
        dynamic_rho = base_rho * importance_factor * quality_factor

        # 限制范围
        dynamic_rho = max(-0.20, min(-0.03, dynamic_rho))

        self._rho_cache[cache_key] = dynamic_rho
        return dynamic_rho

    def expected_goals(self, attack_home: float, defense_away: float,
                       attack_away: float, defense_home: float,
                       home_advantage: bool = False) -> Tuple[float, float]:
        """
        Calculate expected goals for both teams.

        lambda_home = attack_home * defense_away * league_avg_home
        lambda_away = attack_away * defense_home * league_avg_away

        Args:
            attack_home: Home team attack strength (1.0 = average)
            defense_away: Away team defense weakness (1.0 = average)
            attack_away: Away team attack strength
            defense_home: Home team defense weakness
            home_advantage: If True, apply +0.15 boost to home lambda

        Returns:
            (lambda_home, lambda_away) expected goals
        """
        home_factor = 1.15 if home_advantage else 1.0

        lambda_home = attack_home * defense_away * LEAGUE_AVG_HOME_GOALS * home_factor
        lambda_away = attack_away * defense_home * LEAGUE_AVG_AWAY_GOALS

        return max(0.1, lambda_home), max(0.1, lambda_away)

    def scoreline_probability(self, home_goals: int, away_goals: int,
                              lambda_home: float, lambda_away: float) -> float:
        """
        Dixon-Coles adjusted probability of exact scoreline.

        P(home_goals, away_goals) = tau * Poisson(home_goals; λh) * Poisson(away_goals; λa)

        where tau applies the low-score correction for (0,0), (1,0), (0,1), (1,1).
        """
        p_home = poisson.pmf(home_goals, lambda_home)
        p_away = poisson.pmf(away_goals, lambda_away)
        prob = p_home * p_away

        # Dixon-Coles adjustment for low scores
        if home_goals <= 1 and away_goals <= 1:
            tau = self._tau(home_goals, away_goals, lambda_home, lambda_away)
            prob *= tau

        return prob

    def _tau(self, h: int, a: int, lh: float, la: float) -> float:
        """
        Dixon-Coles adjustment factor for low scores.

        τ(h, a) = 1 - λh * λa * ρ  if h=a=0
        τ(h, a) = 1 + λa * ρ        if h=0, a=1
        τ(h, a) = 1 + λh * ρ        if h=1, a=0
        τ(h, a) = 1 - ρ             if h=a=1
        """
        if h == 0 and a == 0:
            return 1.0 - lh * la * self.rho
        elif h == 0 and a == 1:
            return 1.0 + la * self.rho
        elif h == 1 and a == 0:
            return 1.0 + lh * self.rho
        elif h == 1 and a == 1:
            return 1.0 - self.rho
        return 1.0

    def probability_matrix(self, lambda_home: float, lambda_away: float,
                           max_goals: int = MAX_GOALS) -> np.ndarray:
        """
        Compute full scoreline probability matrix.

        Returns:
            (max_goals+1) × (max_goals+1) matrix where [i, j] = P(home=i, away=j)
        """
        matrix = np.zeros((max_goals + 1, max_goals + 1))

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                matrix[i, j] = self.scoreline_probability(i, j, lambda_home, lambda_away)

        # Normalize to 1.0
        total = matrix.sum()
        if total > 0:
            matrix /= total

        return matrix

    def match_probabilities(self, lambda_home: float, lambda_away: float,
                            max_goals: int = MAX_GOALS) -> Dict:
        """
        Compute win/draw/loss probabilities from Poisson model.

        Returns dict with:
        - home_win, draw, away_win probabilities
        - expected_home_goals, expected_away_goals
        - scoreline_matrix (list of lists)
        - most_likely_score
        - over_under_probabilities
        - both_teams_to_score_prob
        """
        matrix = self.probability_matrix(lambda_home, lambda_away, max_goals)

        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                if i > j:
                    home_win += matrix[i, j]
                elif i == j:
                    draw += matrix[i, j]
                else:
                    away_win += matrix[i, j]

        # Most likely scoreline
        max_idx = np.unravel_index(matrix.argmax(), matrix.shape)
        most_likely_score = f"{max_idx[0]}-{max_idx[1]}"
        most_likely_prob = float(matrix[max_idx])

        # Over/Under 2.5
        over_25 = 0.0
        under_25 = 0.0
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                if i + j > 2.5:
                    over_25 += matrix[i, j]
                else:
                    under_25 += matrix[i, j]

        # Both Teams To Score
        btts_yes = 0.0
        btts_no = 0.0
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                if i > 0 and j > 0:
                    btts_yes += matrix[i, j]
                else:
                    btts_no += matrix[i, j]

        # Convert matrix to list for JSON serialization
        matrix_list = matrix.round(4).tolist()

        return {
            "home_win": round(home_win, 4),
            "draw": round(draw, 4),
            "away_win": round(away_win, 4),
            "expected_home_goals": round(lambda_home, 2),
            "expected_away_goals": round(lambda_away, 2),
            "total_expected_goals": round(lambda_home + lambda_away, 2),
            "most_likely_score": most_likely_score,
            "most_likely_prob": round(most_likely_prob, 4),
            "scoreline_matrix": matrix_list,
            "over_2_5": round(over_25, 4),
            "under_2_5": round(under_25, 4),
            "btts_yes": round(btts_yes, 4),
            "btts_no": round(btts_no, 4),
        }
