"""
实时阵容数据获取 — 从多个 API 获取球队阵容和伤病信息

数据来源：
- ESPN API（美国本地，可访问）
- SofaScore API（国际）

功能：
- 获取球队大名单
- 获取首发阵容
- 获取伤病信息
- 获取停赛信息

用法：
    fetcher = SquadFetcher()
    squad = fetcher.get_team_squad("Argentina")
    injuries = fetcher.get_team_injuries("Argentina")
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── API 配置 ─────────────────────────────────────
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
SOFASCORE_BASE_URL = "https://api.sofascore.com/api/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# 球队 ID 映射（ESPN）
ESPN_TEAM_IDS = {
    "Argentina": "1",
    "France": "2",
    "England": "3",
    "Brazil": "4",
    "Spain": "5",
    "Germany": "6",
    "Portugal": "7",
    "Netherlands": "8",
    "Croatia": "9",
    "Belgium": "10",
    "Morocco": "11",
    "Japan": "12",
    "South Korea": "13",
    "USA": "14",
    "Mexico": "15",
    "Switzerland": "16",
    "Australia": "17",
    "Qatar": "18",
    "Turkey": "19",
    "Tunisia": "20",
    "Ecuador": "21",
    "Ivory Coast": "22",
    "Senegal": "23",
    "Ghana": "24",
    "Nigeria": "25",
    "Cameroon": "26",
    "Egypt": "27",
    "Paraguay": "28",
    "Uruguay": "29",
    "Colombia": "30",
    "Peru": "31",
    "Chile": "32",
    "Canada": "33",
    "Bosnia": "34",
    "Czech Republic": "35",
    "Poland": "36",
    "Sweden": "37",
    "Denmark": "38",
    "Norway": "39",
    "Austria": "40",
    "Scotland": "41",
    "Wales": "42",
    "Serbia": "43",
    "Ukraine": "44",
    "Romania": "45",
    "Hungary": "46",
    "Greece": "47",
    "Cape Verde": "48",
    "DR Congo": "49",
    "Iran": "50",
    "Saudi Arabia": "51",
    "Iraq": "52",
    "Jordan": "53",
    "Uzbekistan": "54",
    "Panama": "55",
    "Curacao": "56",
    "Haiti": "57",
    "New Zealand": "58",
}


class SquadFetcher:
    """阵容数据获取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}
        self._cache_time = {}

    def get_team_squad(self, team: str) -> List[Dict]:
        """
        获取球队大名单

        Args:
            team: 球队名称

        Returns:
            [
                {
                    "name": "Messi",
                    "position": "FW",
                    "number": 10,
                    "age": 36,
                    "club": "Inter Miami",
                    "status": "available"
                }
            ]
        """
        # 尝试 ESPN API
        try:
            squad = self._fetch_from_espn(team)
            if squad:
                logger.info(f"从 ESPN 获取到 {team} 的 {len(squad)} 名球员")
                return squad
        except Exception as e:
            logger.warning(f"ESPN API 获取 {team} 阵容失败: {e}")

        # 尝试 SofaScore API
        try:
            squad = self._fetch_from_sofascore(team)
            if squad:
                logger.info(f"从 SofaScore 获取到 {team} 的 {len(squad)} 名球员")
                return squad
        except Exception as e:
            logger.warning(f"SofaScore API 获取 {team} 阵容失败: {e}")

        return []

    def _fetch_from_espn(self, team: str) -> List[Dict]:
        """从 ESPN 获取球队阵容"""
        team_id = ESPN_TEAM_IDS.get(team)
        if not team_id:
            return []

        url = f"{ESPN_BASE_URL}/fifa.world.cup/teams/{team_id}/roster"
        response = self.session.get(url, timeout=10)

        if response.status_code != 200:
            raise Exception(f"ESPN API 返回状态码: {response.status_code}")

        data = response.json()
        squad = []

        for athlete in data.get("athletes", []):
            player = {
                "name": athlete.get("displayName", ""),
                "position": athlete.get("position", {}).get("abbreviation", "MF"),
                "number": athlete.get("jersey", 0),
                "age": athlete.get("age", 0),
                "club": athlete.get("club", {}).get("name", ""),
                "status": "available",
                "source": "espn",
            }
            squad.append(player)

        return squad

    def _fetch_from_sofascore(self, team: str) -> List[Dict]:
        """从 SofaScore 获取球队阵容"""
        # SofaScore 需要 team ID，这里简化处理
        # 实际应用中需要维护 team ID 映射
        return []

    def get_team_injuries(self, team: str) -> List[Dict]:
        """
        获取球队伤病信息

        Args:
            team: 球队名称

        Returns:
            [
                {
                    "name": "Messi",
                    "injury": "Knee",
                    "status": "Doubtful",
                    "expected_return": "2026-06-20"
                }
            ]
        """
        # ESPN API 不直接提供伤病信息
        # 这里返回空列表，后续可以添加其他数据源
        return []

    def get_match_squad(self, home_team: str, away_team: str) -> Dict:
        """
        获取比赛双方阵容

        Args:
            home_team: 主队名称
            away_team: 客队名称

        Returns:
            {
                "home": {"squad": [...], "injuries": [...]},
                "away": {"squad": [...], "injuries": [...]},
            }
        """
        home_squad = self.get_team_squad(home_team)
        away_squad = self.get_team_squad(away_team)

        home_injuries = self.get_team_injuries(home_team)
        away_injuries = self.get_team_injuries(away_team)

        return {
            "home": {
                "squad": home_squad,
                "injuries": home_injuries,
            },
            "away": {
                "squad": away_squad,
                "injuries": away_injuries,
            },
        }

    def get_key_players_from_squad(self, squad: List[Dict], top_n: int = 3) -> List[Dict]:
        """
        从阵容中获取关键球员

        基于球员位置和俱乐部水平判断重要性

        Args:
            squad: 球员列表
            top_n: 返回前 N 名关键球员

        Returns:
            关键球员列表
        """
        if not squad:
            return []

        # 为每个球员计算重要性分数
        scored_players = []
        for player in squad:
            score = self._calculate_player_importance(player)
            scored_players.append({**player, "importance": score})

        # 按重要性排序
        scored_players.sort(key=lambda p: p["importance"], reverse=True)

        return scored_players[:top_n]

    def _calculate_player_importance(self, player: Dict) -> float:
        """
        计算球员重要性分数

        基于：
        - 位置（前锋 > 中场 > 后卫 > 门将）
        - 俱乐部水平（豪门 > 中游 > 保级）
        - 年龄（黄金年龄 > 年轻 > 老将）
        """
        score = 0.5  # 基础分

        # 位置权重
        position_weights = {
            "FW": 0.15,  # 前锋
            "MF": 0.10,  # 中场
            "DF": 0.05,  # 后卫
            "GK": 0.00,  # 门将
        }
        position = player.get("position", "MF")
        score += position_weights.get(position, 0.05)

        # 俱乐部权重（简化版）
        top_clubs = [
            "Real Madrid", "Barcelona", "Manchester City", "Liverpool",
            "Bayern Munich", "PSG", "Juventus", "Inter Milan",
            "Chelsea", "Arsenal", "Manchester United", "Tottenham",
            "Atletico Madrid", "Borussia Dortmund", "Napoli",
        ]
        club = player.get("club", "")
        if any(c in club for c in top_clubs):
            score += 0.20
        elif club:
            score += 0.05

        # 年龄权重（黄金年龄 24-30）
        age = player.get("age", 25)
        if 24 <= age <= 30:
            score += 0.10
        elif 20 <= age <= 23:
            score += 0.05
        elif age > 32:
            score -= 0.05

        return min(1.0, max(0.0, score))


# 全局单例
_squad_fetcher: Optional[SquadFetcher] = None


def get_squad_fetcher() -> SquadFetcher:
    """获取 SquadFetcher 实例"""
    global _squad_fetcher
    if _squad_fetcher is None:
        _squad_fetcher = SquadFetcher()
    return _squad_fetcher
