"""
实时世界杯数据获取 — 进球、比赛状态、实时比分

数据来源：多个国际体育数据源
- ESPN API（全球可用）
- SofaScore API（全球可用）
- 自动切换备用源

功能：
- 实时比分更新
- 比赛状态（进行中、已结束、未开始）
- 进球事件
- 红黄牌
- 换人信息

用法：
    fetcher = LiveDataFetcher()
    matches = fetcher.get_live_matches()
"""

import requests
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── 数据源配置 ─────────────────────────────────────
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
ESPN_WORLD_CUP = f"{ESPN_BASE_URL}/fifa.world.cup/scoreboard"

SOFASCORE_BASE_URL = "https://api.sofascore.com/api/v1"
SOFASCORE_WORLD_CUP = f"{SOFASCORE_BASE_URL}/unique-tournament/16/season/52186/events"

# 标准浏览器头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


@dataclass
class LiveMatch:
    """实时比赛数据"""
    match_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str  # live, finished, scheduled
    status_detail: str  # "1st Half", "2nd Half", "Full Time", etc.
    minute: int  # 比赛分钟数
    events: List[Dict]  # 进球、红黄牌等事件
    start_time: str
    venue: str


class LiveDataFetcher:
    """实时数据获取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}
        self._cache_time = {}

    def get_live_matches(self) -> List[Dict]:
        """
        获取实时比赛数据

        Returns:
            [
                {
                    "match_id": "...",
                    "home_team": "Argentina",
                    "away_team": "Brazil",
                    "home_score": 2,
                    "away_score": 1,
                    "status": "live",
                    "status_detail": "2nd Half",
                    "minute": 75,
                    "events": [
                        {"type": "goal", "team": "home", "player": "Messi", "minute": 23},
                        {"type": "goal", "team": "away", "player": "Neymar", "minute": 56},
                        ...
                    ],
                    "start_time": "2026-06-20T03:00:00Z",
                    "venue": "MetLife Stadium"
                }
            ]
        """
        logger.info("正在获取实时比赛数据...")

        # 尝试 ESPN API
        try:
            matches = self._fetch_from_espn()
            if matches:
                logger.info(f"从 ESPN 获取到 {len(matches)} 场比赛")
                return matches
        except Exception as e:
            logger.warning(f"ESPN API 失败: {e}")

        # 尝试 SofaScore API
        try:
            matches = self._fetch_from_sofascore()
            if matches:
                logger.info(f"从 SofaScore 获取到 {len(matches)} 场比赛")
                return matches
        except Exception as e:
            logger.warning(f"SofaScore API 失败: {e}")

        # 返回空列表
        logger.warning("所有数据源都失败")
        return []

    def _fetch_from_espn(self) -> List[Dict]:
        """从 ESPN API 获取数据"""
        response = self.session.get(ESPN_WORLD_CUP, timeout=10)

        if response.status_code != 200:
            raise Exception(f"ESPN API 返回状态码: {response.status_code}")

        data = response.json()
        matches = []

        for event in data.get("events", []):
            try:
                match = self._parse_espn_event(event)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.debug(f"解析 ESPN 事件失败: {e}")
                continue

        return matches

    def _parse_espn_event(self, event: Dict) -> Optional[Dict]:
        """解析 ESPN 事件数据"""
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])

        if len(competitors) != 2:
            return None

        # 获取主客队
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)

        if not home or not away:
            return None

        # 获取比分
        home_score = int(home.get("score", "0"))
        away_score = int(away.get("score", "0"))

        # 获取比赛状态
        status = competition.get("status", {})
        status_type = status.get("type", {}).get("name", "")
        status_detail = status.get("type", {}).get("shortDetail", "")
        minute = status.get("displayClock", "0'").replace("'", "").split(":")[0]

        # 映射状态
        if status_type == "STATUS_IN_PROGRESS":
            match_status = "live"
        elif status_type == "STATUS_FINAL":
            match_status = "finished"
        else:
            match_status = "scheduled"

        # 获取事件（进球等）
        events = []
        for detail in competition.get("details", []):
            event_type = detail.get("type", {}).get("text", "")
            team = detail.get("team", {}).get("displayName", "")
            player = detail.get("athletesInvolved", [{}])[0].get("displayName", "")
            minute = detail.get("clock", {}).get("displayValue", "")

            if "Goal" in event_type:
                events.append({
                    "type": "goal",
                    "team": "home" if team == home.get("team", {}).get("displayName") else "away",
                    "player": player,
                    "minute": minute,
                })
            elif "Yellow Card" in event_type:
                events.append({
                    "type": "yellow_card",
                    "team": "home" if team == home.get("team", {}).get("displayName") else "away",
                    "player": player,
                    "minute": minute,
                })
            elif "Red Card" in event_type:
                events.append({
                    "type": "red_card",
                    "team": "home" if team == home.get("team", {}).get("displayName") else "away",
                    "player": player,
                    "minute": minute,
                })

        return {
            "match_id": event.get("id", ""),
            "home_team": home.get("team", {}).get("displayName", ""),
            "away_team": away.get("team", {}).get("displayName", ""),
            "home_score": home_score,
            "away_score": away_score,
            "status": match_status,
            "status_detail": status_detail,
            "minute": minute,
            "events": events,
            "start_time": event.get("date", ""),
            "venue": competition.get("venue", {}).get("fullName", ""),
            "source": "espn",
        }

    def _fetch_from_sofascore(self) -> List[Dict]:
        """从 SofaScore API 获取数据"""
        response = self.session.get(SOFASCORE_WORLD_CUP, timeout=10)

        if response.status_code != 200:
            raise Exception(f"SofaScore API 返回状态码: {response.status_code}")

        data = response.json()
        matches = []

        for event in data.get("events", []):
            try:
                match = self._parse_sofascore_event(event)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.debug(f"解析 SofaScore 事件失败: {e}")
                continue

        return matches

    def _parse_sofascore_event(self, event: Dict) -> Optional[Dict]:
        """解析 SofaScore 事件数据"""
        home_team = event.get("homeTeam", {}).get("name", "")
        away_team = event.get("awayTeam", {}).get("name", "")

        if not home_team or not away_team:
            return None

        # 获取比分
        home_score = event.get("homeScore", {}).get("current", 0)
        away_score = event.get("awayScore", {}).get("current", 0)

        # 获取比赛状态
        status_code = event.get("status", {}).get("code", 0)
        status_desc = event.get("status", {}).get("description", "")
        minute = event.get("time", {}).get("current", 0)

        # 映射状态
        if status_code == 3:  # In Progress
            match_status = "live"
        elif status_code == 100:  # Finished
            match_status = "finished"
        else:
            match_status = "scheduled"

        # 获取事件
        events = []
        for incident in event.get("incidents", []):
            incident_type = incident.get("incidentType", "")
            team = "home" if incident.get("isHome") else "away"
            player = incident.get("player", {}).get("name", "")
            minute = incident.get("time", 0)

            if incident_type == "goal":
                events.append({
                    "type": "goal",
                    "team": team,
                    "player": player,
                    "minute": minute,
                })
            elif incident_type == "yellowCard":
                events.append({
                    "type": "yellow_card",
                    "team": team,
                    "player": player,
                    "minute": minute,
                })
            elif incident_type == "redCard":
                events.append({
                    "type": "red_card",
                    "team": team,
                    "player": player,
                    "minute": minute,
                })

        return {
            "match_id": str(event.get("id", "")),
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "status": match_status,
            "status_detail": status_desc,
            "minute": minute,
            "events": events,
            "start_time": event.get("startTimestamp", ""),
            "venue": event.get("venue", {}).get("stadium", {}).get("name", ""),
            "source": "sofascore",
        }

    def get_match_detail(self, match_id: str) -> Optional[Dict]:
        """获取比赛详情"""
        # 尝试 ESPN
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world.cup/summary?event={match_id}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"获取比赛详情失败: {e}")

        return None


def get_live_fetcher() -> LiveDataFetcher:
    """获取 LiveDataFetcher 实例"""
    return LiveDataFetcher()
