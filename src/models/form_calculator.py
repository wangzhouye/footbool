"""
近期战绩计算器 — 计算队伍的近期表现

功能：
- 计算最近 N 场比赛的胜率
- 计算近期进球和失球
- 计算近期状态指数
- 支持不同权重的时间衰减

用法：
    calculator = FormCalculator()
    form = calculator.compute_form("Argentina", matches, last_n=5)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..utils.config import TEAMS


class FormCalculator:
    """近期战绩计算器"""

    def __init__(self, half_life_days: int = 180):
        """
        Args:
            half_life_days: 时间衰减半衰期（天数）
                           越近的比赛权重越高
        """
        self.half_life_days = half_life_days

    def compute_form(self, team: str, matches: pd.DataFrame,
                     last_n: int = 10, reference_date: datetime = None) -> Dict:
        """
        计算队伍的近期战绩

        Args:
            team: 队伍名称
            matches: 比赛数据 DataFrame
            last_n: 最近 N 场比赛
            reference_date: 参考日期（默认为今天）

        Returns:
            {
                "form_score": 0.0-1.0,  # 近期状态指数
                "win_rate": 0.0-1.0,    # 胜率
                "draw_rate": 0.0-1.0,   # 平局率
                "loss_rate": 0.0-1.0,   # 负率
                "goals_scored": float,  # 场均进球
                "goals_conceded": float,# 场均失球
                "goal_diff": float,     # 场均净胜球
                "clean_sheets": int,    # 零封场次
                "matches_played": int,  # 比赛场次
                "recent_form": str,     # 近期表现描述
            }
        """
        if reference_date is None:
            reference_date = datetime.now()

        # 获取队伍的比赛
        team_matches = self._get_team_matches(team, matches, reference_date)

        if len(team_matches) == 0:
            return self._default_form()

        # 取最近 N 场
        recent_matches = team_matches.tail(last_n)

        # 计算各项指标
        wins = 0
        draws = 0
        losses = 0
        goals_scored = 0
        goals_conceded = 0
        clean_sheets = 0
        weighted_score = 0.0
        total_weight = 0.0

        for _, match in recent_matches.iterrows():
            is_home = match["home_team"] == team
            if is_home:
                gf = match["home_score"]
                ga = match["away_score"]
            else:
                gf = match["away_score"]
                ga = match["home_score"]

            goals_scored += gf
            goals_conceded += ga

            if gf > ga:
                wins += 1
                result_score = 1.0
            elif gf == ga:
                draws += 1
                result_score = 0.5
            else:
                losses += 1
                result_score = 0.0

            if ga == 0:
                clean_sheets += 1

            # 时间衰减权重
            match_date = match["date"]
            if isinstance(match_date, str):
                match_date = datetime.strptime(match_date, "%Y-%m-%d")

            days_ago = (reference_date - match_date).days
            weight = 2 ** (-days_ago / self.half_life_days)

            weighted_score += result_score * weight
            total_weight += weight

        n_matches = len(recent_matches)

        # 计算指标
        form_score = weighted_score / total_weight if total_weight > 0 else 0.5
        win_rate = wins / n_matches
        draw_rate = draws / n_matches
        loss_rate = losses / n_matches
        avg_goals_scored = goals_scored / n_matches
        avg_goals_conceded = goals_conceded / n_matches
        goal_diff = avg_goals_scored - avg_goals_conceded

        # 生成近期表现描述
        recent_form = self._generate_form_string(recent_matches, team)

        return {
            "form_score": round(form_score, 4),
            "win_rate": round(win_rate, 4),
            "draw_rate": round(draw_rate, 4),
            "loss_rate": round(loss_rate, 4),
            "goals_scored": round(avg_goals_scored, 2),
            "goals_conceded": round(avg_goals_conceded, 2),
            "goal_diff": round(goal_diff, 2),
            "clean_sheets": clean_sheets,
            "matches_played": n_matches,
            "recent_form": recent_form,
        }

    def _get_team_matches(self, team: str, matches: pd.DataFrame,
                          reference_date: datetime) -> pd.DataFrame:
        """获取队伍的所有比赛（按日期排序）"""
        # 筛选队伍的比赛
        home_matches = matches[matches["home_team"] == team].copy()
        away_matches = matches[matches["away_team"] == team].copy()

        # 添加标识列
        home_matches["is_home"] = True
        away_matches["is_home"] = False

        # 合并
        all_matches = pd.concat([home_matches, away_matches])

        # 转换日期
        if "date" in all_matches.columns:
            all_matches["date"] = pd.to_datetime(all_matches["date"])

        # 筛选参考日期之前的比赛
        all_matches = all_matches[all_matches["date"] <= reference_date]

        # 按日期排序
        all_matches = all_matches.sort_values("date")

        return all_matches

    def _generate_form_string(self, matches: pd.DataFrame, team: str) -> str:
        """生成近期表现字符串，如 'WWDLW'"""
        form = []
        for _, match in matches.iterrows():
            is_home = match["home_team"] == team
            if is_home:
                gf, ga = match["home_score"], match["away_score"]
            else:
                gf, ga = match["away_score"], match["home_score"]

            if gf > ga:
                form.append("W")
            elif gf == ga:
                form.append("D")
            else:
                form.append("L")

        return "".join(form)

    def _default_form(self) -> Dict:
        """默认战绩（无数据时）"""
        return {
            "form_score": 0.5,
            "win_rate": 0.33,
            "draw_rate": 0.33,
            "loss_rate": 0.34,
            "goals_scored": 1.0,
            "goals_conceded": 1.0,
            "goal_diff": 0.0,
            "clean_sheets": 0,
            "matches_played": 0,
            "recent_form": "",
        }


def get_form_calculator() -> FormCalculator:
    """获取 FormCalculator 实例"""
    return FormCalculator()
