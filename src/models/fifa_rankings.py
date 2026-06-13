"""
FIFA 排名和历史交锋数据

功能：
- FIFA 排名查询
- 历史交锋记录
- 主客场表现统计

用法：
    rankings = get_fifa_rankings()
    rank = rankings.get_ranking("Argentina")
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..utils.config import TEAMS


class FIFAData:
    """FIFA 数据管理器"""

    def __init__(self):
        self.rankings = self._load_default_rankings()
        self.head_to_head = {}  # 历史交锋数据

    def _load_default_rankings(self) -> Dict[str, int]:
        """加载默认 FIFA 排名（2026年世界杯前）"""
        # 基于实际 FIFA 排名的近似值
        return {
            # UEFA
            "Argentina": 1, "France": 2, "England": 3, "Belgium": 4,
            "Brazil": 5, "Netherlands": 6, "Portugal": 7, "Spain": 8,
            "Italy": 9, "Croatia": 10, "Germany": 11, "Colombia": 12,
            "Uruguay": 13, "Switzerland": 14, "Denmark": 15, "Austria": 16,
            "Sweden": 17, "Ukraine": 18, "Poland": 19, "Serbia": 20,
            "Wales": 21, "Czech Republic": 22, "Norway": 23, "Scotland": 24,
            "Turkey": 25, "Russia": 26, "Hungary": 27, "Slovakia": 28,
            "Greece": 29, "Romania": 30,

            # CONMEBOL
            "Ecuador": 31, "Paraguay": 32, "Peru": 33, "Chile": 34,
            "Bolivia": 35, "Venezuela": 36,

            # CONCACAF
            "USA": 37, "Mexico": 38, "Canada": 39, "Costa Rica": 40,
            "Panama": 41, "Jamaica": 42,

            # CAF
            "Morocco": 43, "Senegal": 44, "Tunisia": 45, "Algeria": 46,
            "Egypt": 47, "Nigeria": 48, "Cameroon": 49, "Ivory Coast": 50,
            "Ghana": 51, "South Africa": 52, "DR Congo": 53, "Mali": 54,

            # AFC
            "Japan": 55, "South Korea": 56, "Iran": 57, "Australia": 58,
            "Saudi Arabia": 59, "Qatar": 60, "Iraq": 61, "UAE": 62,
            "Uzbekistan": 63, "Jordan": 64, "China": 65, "Oman": 66,
            "Bahrain": 67, "Syria": 68, "Thailand": 69, "Vietnam": 70,

            # OFC
            "New Zealand": 71,

            # 其他
            "Bosnia": 72, "Iceland": 73, "Ireland": 74, "Northern Ireland": 75,
            "Finland": 76, "Slovenia": 77, "Montenegro": 78, "North Macedonia": 79,
            "Albania": 80, "Armenia": 81, "Georgia": 82, "Kosovo": 83,
            "Belarus": 84, "Estonia": 85, "Latvia": 86, "Lithuania": 87,
            "Moldova": 88, "Luxembourg": 89, "Malta": 90, "Andorra": 91,
            "San Marino": 92, "Gibraltar": 93, "Liechtenstein": 94,
            "Faroe Islands": 95, "Azerbaijan": 96, "Kazakhstan": 97,
            "Cyprus": 98, "Israel": 99, "Bulgaria": 100,

            # 中北美及加勒比海地区
            "Honduras": 101, "El Salvador": 102, "Guatemala": 103,
            "Trinidad and Tobago": 104, "Haiti": 105, "Curacao": 106,
            "Suriname": 107, "Guyana": 108, "Bermuda": 109,
            "Barbados": 110, "Jamaica": 111,

            # 非洲
            "Burkina Faso": 112, "Cape Verde": 113, "Guinea": 114,
            "Zambia": 115, "Uganda": 116, "Benin": 117, "Madagascar": 118,
            "Mozambique": 119, "Angola": 120, "Togo": 121, "Kenya": 122,
            "Congo": 123, "Gabon": 124, "Libya": 125, "Sudan": 126,
            "Zimbabwe": 127, "Tanzania": 128, "Ethiopia": 129, "Rwanda": 130,

            # 亚洲
            "India": 131, "Indonesia": 132, "Malaysia": 133, "Philippines": 134,
            "Singapore": 135, "Kuwait": 136, "Lebanon": 137, "Tajikistan": 138,
            "Kyrgyzstan": 139, "Turkmenistan": 140, "Yemen": 141, "Myanmar": 142,
            "North Korea": 143, "Laos": 144, "Cambodia": 145, "Nepal": 146,
            "Bangladesh": 147, "Sri Lanka": 148, "Pakistan": 149, "Afghanistan": 150,
        }

    def get_ranking(self, team: str) -> int:
        """获取队伍的 FIFA 排名"""
        return self.rankings.get(team, 100)  # 默认排名 100

    def get_ranking_weight(self, team: str) -> float:
        """
        获取队伍的排名权重

        Returns:
            0.0-1.0 之间的权重值，排名越高权重越大
        """
        rank = self.get_ranking(team)
        # 使用指数衰减函数
        # 排名 1 → 权重 1.0
        # 排名 50 → 权重 0.5
        # 排名 100 → 权重 0.25
        return 1.0 / (1.0 + rank / 50.0)

    def update_rankings_from_matches(self, matches: pd.DataFrame):
        """
        根据比赛结果更新排名

        Args:
            matches: 比赛数据 DataFrame
        """
        # 简化的排名更新逻辑
        # 实际应用中应该使用更复杂的算法
        for _, match in matches.iterrows():
            home_team = match["home_team"]
            away_team = match["away_team"]
            home_score = match["home_score"]
            away_score = match["away_score"]

            # 获取当前排名
            home_rank = self.get_ranking(home_team)
            away_rank = self.get_ranking(away_team)

            # 计算排名变化
            if home_score > away_score:
                # 主队获胜
                rank_change = max(1, (away_rank - home_rank) // 10)
                self.rankings[home_team] = max(1, home_rank - rank_change)
                self.rankings[away_team] = min(150, away_rank + rank_change)
            elif home_score < away_score:
                # 客队获胜
                rank_change = max(1, (home_rank - away_rank) // 10)
                self.rankings[home_team] = min(150, home_rank + rank_change)
                self.rankings[away_team] = max(1, away_rank - rank_change)
            # 平局不改变排名

    def compute_head_to_head(self, team_a: str, team_b: str,
                             matches: pd.DataFrame) -> Dict:
        """
        计算两队历史交锋记录

        Args:
            team_a: 队伍 A
            team_b: 队伍 B
            matches: 比赛数据 DataFrame

        Returns:
            {
                "total_matches": int,
                "team_a_wins": int,
                "team_b_wins": int,
                "draws": int,
                "team_a_goals": int,
                "team_b_goals": int,
                "team_a_win_rate": float,
                "team_b_win_rate": float,
                "draw_rate": float,
                "recent_form": str,  # 最近 5 场交锋结果
            }
        """
        # 筛选两队交锋记录
        h2h_matches = matches[
            ((matches["home_team"] == team_a) & (matches["away_team"] == team_b)) |
            ((matches["home_team"] == team_b) & (matches["away_team"] == team_a))
        ].copy()

        if len(h2h_matches) == 0:
            return self._default_head_to_head()

        # 计算统计
        team_a_wins = 0
        team_b_wins = 0
        draws = 0
        team_a_goals = 0
        team_b_goals = 0
        recent_form = []

        for _, match in h2h_matches.iterrows():
            is_team_a_home = match["home_team"] == team_a

            if is_team_a_home:
                gf_a = match["home_score"]
                gf_b = match["away_score"]
            else:
                gf_a = match["away_score"]
                gf_b = match["home_score"]

            team_a_goals += gf_a
            team_b_goals += gf_b

            if gf_a > gf_b:
                team_a_wins += 1
                recent_form.append("W")
            elif gf_a < gf_b:
                team_b_wins += 1
                recent_form.append("L")
            else:
                draws += 1
                recent_form.append("D")

        total_matches = len(h2h_matches)

        return {
            "total_matches": total_matches,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "draws": draws,
            "team_a_goals": team_a_goals,
            "team_b_goals": team_b_goals,
            "team_a_win_rate": round(team_a_wins / total_matches, 4),
            "team_b_win_rate": round(team_b_wins / total_matches, 4),
            "draw_rate": round(draws / total_matches, 4),
            "recent_form": "".join(recent_form[-5:]),  # 最近 5 场
        }

    def _default_head_to_head(self) -> Dict:
        """默认历史交锋数据"""
        return {
            "total_matches": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "draws": 0,
            "team_a_goals": 0,
            "team_b_goals": 0,
            "team_a_win_rate": 0.33,
            "team_b_win_rate": 0.33,
            "draw_rate": 0.34,
            "recent_form": "",
        }

    def compute_venue_performance(self, team: str, matches: pd.DataFrame,
                                  venue: str = "home") -> Dict:
        """
        计算队伍在特定场地的表现

        Args:
            team: 队伍名称
            matches: 比赛数据 DataFrame
            venue: 场地类型 ("home", "away", "neutral")

        Returns:
            {
                "matches_played": int,
                "wins": int,
                "draws": int,
                "losses": int,
                "goals_scored": int,
                "goals_conceded": int,
                "win_rate": float,
            }
        """
        if venue == "home":
            venue_matches = matches[matches["home_team"] == team]
            goals_scored = venue_matches["home_score"].sum()
            goals_conceded = venue_matches["away_score"].sum()
            wins = len(venue_matches[venue_matches["home_score"] > venue_matches["away_score"]])
            draws = len(venue_matches[venue_matches["home_score"] == venue_matches["away_score"]])
            losses = len(venue_matches[venue_matches["home_score"] < venue_matches["away_score"]])
        elif venue == "away":
            venue_matches = matches[matches["away_team"] == team]
            goals_scored = venue_matches["away_score"].sum()
            goals_conceded = venue_matches["home_score"].sum()
            wins = len(venue_matches[venue_matches["away_score"] > venue_matches["home_score"]])
            draws = len(venue_matches[venue_matches["away_score"] == venue_matches["home_score"]])
            losses = len(venue_matches[venue_matches["away_score"] < venue_matches["home_score"]])
        else:
            # 中立场地（简化处理）
            venue_matches = matches[
                ((matches["home_team"] == team) | (matches["away_team"] == team))
            ]
            goals_scored = venue_matches["home_score"].sum() + venue_matches["away_score"].sum()
            goals_conceded = 0  # 简化处理
            wins = 0
            draws = 0
            losses = 0

        matches_played = len(venue_matches)

        return {
            "matches_played": matches_played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_scored": int(goals_scored),
            "goals_conceded": int(goals_conceded),
            "win_rate": round(wins / matches_played, 4) if matches_played > 0 else 0.0,
        }


# 全局单例
_fifa_data: Optional[FIFAData] = None


def get_fifa_data() -> FIFAData:
    """获取 FIFAData 实例"""
    global _fifa_data
    if _fifa_data is None:
        _fifa_data = FIFAData()
    return _fifa_data
