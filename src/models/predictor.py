"""
Unified Match Predictor — combines Elo ratings + Poisson model
to provide complete match predictions.

This is the primary interface consumed by all Streamlit pages.
"""

from typing import Dict, Optional, Tuple
import pandas as pd
from functools import lru_cache

from .elo import EloEngine
from .poisson_model import PoissonModel
from .form_calculator import get_form_calculator
from .fifa_rankings import get_fifa_data
from .squad_data import get_squad_data
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
        self.form_calculator = get_form_calculator()
        self.fifa_data = get_fifa_data()
        self.squad_data = get_squad_data()
        self.historical_df: Optional[pd.DataFrame] = None
        self._trained = False
        self._prediction_cache = {}  # 预测结果缓存

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
                neutral: bool = True, match_importance: str = "World Cup",
                injured_players: List[str] = None,
                suspended_players: List[str] = None) -> Dict:
        """
        Predict a single match.

        Args:
            home_team: Name of home/nominal home team
            away_team: Name of away/nominal away team
            neutral: True if match is at neutral venue
            match_importance: 比赛重要性 ("World Cup", "Qualifier", "Friendly")
            injured_players: 受伤球员列表
            suspended_players: 停赛球员列表

        Returns:
            Dict with all prediction details
        """
        # 检查缓存
        cache_key = f"{home_team}_{away_team}_{neutral}_{match_importance}"
        if cache_key in self._prediction_cache:
            return self._prediction_cache[cache_key]

        # 计算 Elo 差异（用于动态 rho）
        elo_diff = self.elo.get_rating(home_team) - self.elo.get_rating(away_team)
        quality_diff = elo_diff / 400.0

        # 动态调整 Dixon-Coles 参数
        dynamic_rho = self.poisson.compute_dynamic_rho(match_importance, quality_diff)
        self.poisson.rho = dynamic_rho

        lambda_h, lambda_a = self._compute_lambdas(home_team, away_team, neutral)

        # Poisson-based match probabilities
        poisson_probs = self.poisson.match_probabilities(lambda_h, lambda_a)

        # Elo-based probabilities (for comparison / blending)
        elo_probs = self.elo.win_probability(home_team, away_team, neutral)

        # 计算近期战绩权重
        form_weight = self._compute_form_weight(home_team, away_team)

        # 计算 FIFA 排名权重
        fifa_weight = self._compute_fifa_weight(home_team, away_team)

        # 计算历史交锋权重
        h2h_weight = self._compute_h2h_weight(home_team, away_team)

        # 计算阵容影响
        home_squad = self.squad_data.calculate_squad_impact(
            home_team, injured_players, suspended_players
        )
        away_squad = self.squad_data.calculate_squad_impact(
            away_team, injured_players, suspended_players
        )

        # 动态权重调整
        weights = self._compute_dynamic_weights(
            poisson_probs, elo_probs, form_weight, neutral, match_importance
        )

        # Blend probabilities with dynamic weights
        blended = {
            "home_win": round(
                weights["poisson"] * poisson_probs["home_win"] +
                weights["elo"] * elo_probs["home_win"] +
                weights["form"] * form_weight["home"] +
                weights["fifa"] * fifa_weight["home"] +
                weights["h2h"] * h2h_weight["home"], 4
            ),
            "draw": round(
                weights["poisson"] * poisson_probs["draw"] +
                weights["elo"] * elo_probs["draw"] +
                weights["form"] * form_weight["draw"] +
                weights["fifa"] * fifa_weight["draw"] +
                weights["h2h"] * h2h_weight["draw"], 4
            ),
            "away_win": round(
                weights["poisson"] * poisson_probs["away_win"] +
                weights["elo"] * elo_probs["away_win"] +
                weights["form"] * form_weight["away"] +
                weights["fifa"] * fifa_weight["away"] +
                weights["h2h"] * h2h_weight["away"], 4
            ),
        }

        # 归一化
        total = sum(blended.values())
        if total > 0:
            blended = {k: v / total for k, v in blended.items()}

        result = {
            "home_team": home_team,
            "away_team": away_team,
            "neutral": neutral,
            "elo_home": round(self.elo.get_rating(home_team), 1),
            "elo_away": round(self.elo.get_rating(away_team), 1),
            "elo_diff": round(elo_diff, 1),
            "fifa_rank_home": self.fifa_data.get_ranking(home_team),
            "fifa_rank_away": self.fifa_data.get_ranking(away_team),
            # Blended probabilities
            "home_win": round(blended["home_win"], 4),
            "draw": round(blended["draw"], 4),
            "away_win": round(blended["away_win"], 4),
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
            # Squad info
            "home_squad": home_squad,
            "away_squad": away_squad,
            "home_key_players": [p.name for p in self.squad_data.get_key_players(home_team)],
            "away_key_players": [p.name for p in self.squad_data.get_key_players(away_team)],
            # Model details
            "weights": weights,
            "form_weight": form_weight,
            "fifa_weight": fifa_weight,
            "h2h_weight": h2h_weight,
            "dynamic_rho": dynamic_rho,
        }

        # 缓存结果
        self._prediction_cache[cache_key] = result

        return result

    def _compute_form_weight(self, home_team: str, away_team: str) -> Dict:
        """
        计算近期战绩权重

        Returns:
            {"home": float, "draw": float, "away": float}
        """
        if self.historical_df is None or self.historical_df.empty:
            return {"home": 0.0, "draw": 0.0, "away": 0.0}

        home_form = self.form_calculator.compute_form(home_team, self.historical_df)
        away_form = self.form_calculator.compute_form(away_team, self.historical_df)

        # 计算近期战绩差异
        form_diff = home_form["form_score"] - away_form["form_score"]

        # 转换为概率权重
        # 正值表示主队近期状态更好
        if form_diff > 0:
            home_weight = min(0.2, form_diff * 0.3)
            away_weight = 0.0
        else:
            home_weight = 0.0
            away_weight = min(0.2, abs(form_diff) * 0.3)

        draw_weight = 0.0  # 近期战绩不影响平局概率

        return {
            "home": round(home_weight, 4),
            "draw": round(draw_weight, 4),
            "away": round(away_weight, 4),
        }

    def _compute_fifa_weight(self, home_team: str, away_team: str) -> Dict:
        """
        计算 FIFA 排名权重

        Returns:
            {"home": float, "draw": float, "away": float}
        """
        home_rank = self.fifa_data.get_ranking(home_team)
        away_rank = self.fifa_data.get_ranking(away_team)

        # 计算排名差异
        rank_diff = away_rank - home_rank  # 正值表示主队排名更高

        # 转换为概率权重
        # 排名差异越大，权重越大
        if rank_diff > 0:
            # 主队排名更高
            home_weight = min(0.15, rank_diff / 200.0)
            away_weight = 0.0
        else:
            # 客队排名更高
            home_weight = 0.0
            away_weight = min(0.15, abs(rank_diff) / 200.0)

        draw_weight = 0.0  # 排名不影响平局概率

        return {
            "home": round(home_weight, 4),
            "draw": round(draw_weight, 4),
            "away": round(away_weight, 4),
        }

    def _compute_h2h_weight(self, home_team: str, away_team: str) -> Dict:
        """
        计算历史交锋权重

        Returns:
            {"home": float, "draw": float, "away": float}
        """
        if self.historical_df is None or self.historical_df.empty:
            return {"home": 0.0, "draw": 0.0, "away": 0.0}

        h2h = self.fifa_data.compute_head_to_head(home_team, away_team, self.historical_df)

        if h2h["total_matches"] < 3:
            # 交锋次数太少，不使用权重
            return {"home": 0.0, "draw": 0.0, "away": 0.0}

        # 计算胜率差异
        win_rate_diff = h2h["team_a_win_rate"] - h2h["team_b_win_rate"]

        # 转换为概率权重
        if win_rate_diff > 0:
            home_weight = min(0.1, win_rate_diff * 0.2)
            away_weight = 0.0
        else:
            home_weight = 0.0
            away_weight = min(0.1, abs(win_rate_diff) * 0.2)

        draw_weight = 0.0  # 历史交锋不影响平局概率

        return {
            "home": round(home_weight, 4),
            "draw": round(draw_weight, 4),
            "away": round(away_weight, 4),
        }

    def _compute_dynamic_weights(self, poisson_probs: Dict, elo_probs: Dict,
                                form_weight: Dict, neutral: bool,
                                match_importance: str) -> Dict:
        """
        动态调整模型权重

        Returns:
            {"poisson": float, "elo": float, "form": float, "fifa": float, "h2h": float}
        """
        # 基础权重
        base_poisson = 0.55
        base_elo = 0.20
        base_form = 0.10
        base_fifa = 0.10
        base_h2h = 0.05

        # 根据比赛重要性调整
        if match_importance == "World Cup":
            # 世界杯比赛，Poisson 模型更重要
            importance_factor = 1.1
        elif "Qualifier" in match_importance:
            importance_factor = 1.0
        else:
            # 友谊赛，Elo 模型更重要
            importance_factor = 0.9

        # 根据中立场地调整
        if neutral:
            # 中立场地，Elo 模型更重要
            neutral_factor = 1.1
        else:
            neutral_factor = 1.0

        # 根据近期战绩差异调整
        form_diff = abs(form_weight["home"] - form_weight["away"])
        if form_diff > 0.1:
            # 近期战绩差异大，增加 form 权重
            form_factor = 1.5
        else:
            form_factor = 1.0

        # 计算最终权重
        poisson_weight = base_poisson * importance_factor
        elo_weight = base_elo * neutral_factor
        form_weight_final = base_form * form_factor
        fifa_weight = base_fifa
        h2h_weight = base_h2h

        # 归一化
        total = poisson_weight + elo_weight + form_weight_final + fifa_weight + h2h_weight
        if total > 0:
            poisson_weight /= total
            elo_weight /= total
            form_weight_final /= total
            fifa_weight /= total
            h2h_weight /= total

        return {
            "poisson": round(poisson_weight, 4),
            "elo": round(elo_weight, 4),
            "form": round(form_weight_final, 4),
            "fifa": round(fifa_weight, 4),
            "h2h": round(h2h_weight, 4),
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
