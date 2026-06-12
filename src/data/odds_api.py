"""
海外竞彩数据源 — The Odds API

数据来源：the-odds-api.com（全球博彩赔率聚合）
- 支持 FIFA 世界杯
- 免费额度：每月 500 次请求
- 赔率格式：小数（欧洲格式）

用法：
    api = OddsAPI(api_key="your_key")
    matches = api.get_world_cup_odds()
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── API 配置 ─────────────────────────────────────
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_fifa_world_cup"  # FIFA 世界杯

# 赔率格式
ODDS_FORMAT = "decimal"  # 欧洲小数格式
REGION = "eu"  # 欧洲博彩公司


@dataclass
class MatchOdds:
    """比赛赔率数据"""
    match_id: str
    home_team: str
    away_team: str
    commence_time: str  # ISO 格式
    bookmaker: str
    market: str  # h2h, spreads, totals
    outcomes: Dict[str, float]  # {"home": 2.1, "draw": 3.2, "away": 4.5}


class OddsAPI:
    """The Odds API 客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self._cache = {}
        self._cache_time = {}

    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送 API 请求"""
        url = f"{BASE_URL}/{endpoint}"
        default_params = {
            "apiKey": self.api_key,
            "regions": REGION,
            "oddsFormat": ODDS_FORMAT,
        }
        if params:
            default_params.update(params)

        try:
            response = self.session.get(url, params=default_params, timeout=10)
            if response.status_code == 200:
                # 记录剩余请求次数
                remaining = response.headers.get("x-requests-remaining")
                if remaining:
                    logger.info(f"API 请求剩余次数: {remaining}")
                return response.json()
            else:
                logger.error(f"API 请求失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"API 请求异常: {e}")
            return None

    def get_world_cup_odds(self, market: str = "h2h") -> List[Dict]:
        """
        获取世界杯比赛赔率

        Args:
            market: 市场类型
                   - "h2h": 胜平负（Match Winner）
                   - "spreads": 让球（Asian Handicap）
                   - "totals": 大小球（Over/Under）

        Returns:
            赔率列表，格式：
            [
                {
                    "id": "match_id",
                    "home_team": "Argentina",
                    "away_team": "Brazil",
                    "commence_time": "2026-06-20T03:00:00Z",
                    "bookmakers": [
                        {
                            "name": "Bet365",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": "Argentina", "price": 2.1},
                                        {"name": "Draw", "price": 3.2},
                                        {"name": "Brazil", "price": 4.5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        """
        data = self._request(f"sports/{SPORT_KEY}/odds", {"markets": market})
        if not data:
            return []
        return data

    def get_match_odds(self, match_id: str, market: str = "h2h") -> Optional[Dict]:
        """获取单场比赛赔率"""
        data = self._request(
            f"sports/{SPORT_KEY}/events/{match_id}/odds",
            {"markets": market}
        )
        return data

    def get_events(self) -> List[Dict]:
        """获取所有世界杯赛事（不含赔率）"""
        data = self._request(f"sports/{SPORT_KEY}/events")
        if not data:
            return []
        return data

    def parse_odds(self, raw_data: List[Dict]) -> List[Dict]:
        """
        解析 API 返回的赔率数据，转换为统一格式

        Returns:
            [
                {
                    "match_id": "...",
                    "home_team": "Argentina",
                    "away_team": "Brazil",
                    "date": "2026-06-20",
                    "time": "03:00",
                    "odds_had": {"h": 2.1, "d": 3.2, "a": 4.5},
                    "best_odds": {"h": 2.15, "d": 3.3, "a": 4.6},
                    "bookmakers": ["Bet365", "Betfair", ...]
                }
            ]
        """
        matches = []

        for event in raw_data:
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence_time = event.get("commence_time", "")

            # 解析时间
            try:
                dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")
            except:
                date_str = commence_time[:10]
                time_str = ""

            # 收集所有博彩公司的赔率
            all_odds_h = []
            all_odds_d = []
            all_odds_a = []
            bookmakers = []

            for bookmaker in event.get("bookmakers", []):
                bookmakers.append(bookmaker.get("title", ""))

                for market in bookmaker.get("markets", []):
                    if market.get("key") == "h2h":
                        for outcome in market.get("outcomes", []):
                            name = outcome.get("name", "")
                            price = outcome.get("price", 0)

                            if name == home_team:
                                all_odds_h.append(price)
                            elif name == away_team:
                                all_odds_a.append(price)
                            elif name == "Draw":
                                all_odds_d.append(price)

            # 计算最佳赔率和平均赔率
            if all_odds_h and all_odds_d and all_odds_a:
                matches.append({
                    "match_id": event.get("id", ""),
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": date_str,
                    "time": time_str,
                    "commence_time": commence_time,
                    "odds_had": {
                        "h": round(sum(all_odds_h) / len(all_odds_h), 2),
                        "d": round(sum(all_odds_d) / len(all_odds_d), 2),
                        "a": round(sum(all_odds_a) / len(all_odds_a), 2),
                    },
                    "best_odds": {
                        "h": round(max(all_odds_h), 2),
                        "d": round(max(all_odds_d), 2),
                        "a": round(max(all_odds_a), 2),
                    },
                    "bookmakers": bookmakers,
                })

        return matches


def get_odds_api(api_key: str = None) -> Optional[OddsAPI]:
    """
    获取 OddsAPI 实例

    Args:
        api_key: API Key，如果不提供则从环境变量读取

    Returns:
        OddsAPI 实例或 None
    """
    if not api_key:
        import os
        api_key = os.environ.get("ODDS_API_KEY")

    if not api_key:
        logger.warning("未配置 ODDS_API_KEY，无法获取海外赔率数据")
        return None

    return OddsAPI(api_key)
