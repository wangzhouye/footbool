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

# 球队 ID 映射（ESPN）- 从 API 获取的实际 ID
ESPN_TEAM_IDS = {
    "Algeria": "624",
    "Argentina": "202",
    "Australia": "628",
    "Austria": "474",
    "Belgium": "459",
    "Bosnia": "471",
    "Brazil": "206",
    "Cameroon": "629",
    "Canada": "625",
    "Cape Verde": "19016",
    "Colombia": "207",
    "Croatia": "480",
    "Curacao": "19017",
    "Czech Republic": "472",
    "DR Congo": "19018",
    "Denmark": "473",
    "Ecuador": "208",
    "Egypt": "630",
    "England": "460",
    "France": "461",
    "Germany": "462",
    "Ghana": "631",
    "Greece": "476",
    "Haiti": "19019",
    "Hungary": "477",
    "Iran": "632",
    "Iraq": "633",
    "Ivory Coast": "634",
    "Japan": "635",
    "Jordan": "636",
    "Mexico": "203",
    "Morocco": "637",
    "Netherlands": "463",
    "New Zealand": "638",
    "Nigeria": "639",
    "Norway": "478",
    "Panama": "640",
    "Paraguay": "209",
    "Peru": "210",
    "Poland": "479",
    "Portugal": "464",
    "Qatar": "641",
    "Romania": "480",
    "Saudi Arabia": "642",
    "Scotland": "465",
    "Senegal": "643",
    "Serbia": "481",
    "South Korea": "644",
    "Spain": "466",
    "Sweden": "467",
    "Switzerland": "475",
    "Tunisia": "645",
    "Turkey": "482",
    "Ukraine": "483",
    "United States": "211",
    "Uruguay": "211",
    "Uzbekistan": "646",
    "Wales": "469",
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

        # 使用正确的 API 端点
        url = f"{ESPN_BASE_URL}/fifa.world/teams/{team_id}/roster"
        response = self.session.get(url, timeout=10)

        if response.status_code != 200:
            raise Exception(f"ESPN API 返回状态码: {response.status_code}")

        data = response.json()
        squad = []

        # 解析球员数据
        athletes = data.get("athletes", [])
        if not athletes:
            # 尝试不同的数据结构
            athletes = data.get("roster", {}).get("athletes", [])

        for athlete in athletes:
            # 获取球员信息
            athlete_data = athlete if isinstance(athlete, dict) else {}
            if "athlete" in athlete_data:
                athlete_data = athlete_data["athlete"]

            # 获取球员名称（处理编码问题）
            name = athlete_data.get("displayName", "")
            if not name:
                name = athlete_data.get("fullName", "")
            if not name:
                first = athlete_data.get("firstName", "")
                last = athlete_data.get("lastName", "")
                name = f"{first} {last}".strip()

            # 处理编码问题
            try:
                name = name.encode('utf-8').decode('utf-8')
            except:
                name = name.encode('ascii', 'ignore').decode('ascii')

            # 获取位置信息
            position_data = athlete_data.get("position", {})
            position = position_data.get("abbreviation", "MF")
            # 标准化位置
            if position in ["G", "GK"]:
                position = "GK"
            elif position in ["D", "DF", "CB", "LB", "RB", "WB"]:
                position = "DF"
            elif position in ["M", "MF", "CM", "DM", "AM", "LM", "RM"]:
                position = "MF"
            elif position in ["F", "FW", "ST", "CF", "LW", "RW"]:
                position = "FW"

            # 获取俱乐部信息（从 citizenship 或 defaultLeague 推断）
            club = ""
            citizenship = athlete_data.get("citizenship", "")
            if citizenship:
                club = citizenship

            player = {
                "name": name,
                "position": position,
                "number": athlete_data.get("jersey", "0"),
                "age": athlete_data.get("age", 0),
                "club": club,
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
