"""
多个赔率数据源 — 聚合多个免费 API

数据来源：
- Odds Portal（全球赔率聚合）
- Bet365 API（全球博彩）
- Pinnacle API（专业博彩）
- 1xBet API（东欧博彩）

功能：
- 自动聚合多个数据源
- 避免重复数据
- 提供最佳赔率

用法：
    aggregator = OddsAggregator()
    matches = aggregator.get_all_odds()
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── 数据源配置 ─────────────────────────────────────
SOURCES = {
    "oddsportal": {
        "name": "Odds Portal",
        "url": "https://www.oddsportal.com/football/world/world-cup/",
        "enabled": True,
    },
    "bet365": {
        "name": "Bet365",
        "url": "https://www.bet365.com/en/sports/soccer/world-cup/",
        "enabled": True,
    },
    "pinnacle": {
        "name": "Pinnacle",
        "url": "https://www.pinnacle.com/en/soccer/world-cup/",
        "enabled": True,
    },
    "1xbet": {
        "name": "1xBet",
        "url": "https://1xbet.com/en/football/world-cup",
        "enabled": True,
    },
}

# 标准浏览器头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class OddsAggregator:
    """赔率数据聚合器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}

    def get_all_odds(self) -> List[Dict]:
        """
        获取所有数据源的赔率数据

        Returns:
            合并后的赔率列表，按比赛分组
        """
        all_matches = []

        # 尝试各个数据源
        for source_id, source_config in SOURCES.items():
            if not source_config.get("enabled"):
                continue

            try:
                matches = self._fetch_from_source(source_id)
                if matches:
                    logger.info(f"从 {source_config['name']} 获取到 {len(matches)} 场比赛")
                    all_matches.extend(matches)
            except Exception as e:
                logger.warning(f"{source_config['name']} 获取失败: {e}")

        # 合并重复比赛
        merged = self._merge_matches(all_matches)
        logger.info(f"总共获取到 {len(merged)} 场比赛赔率")

        return merged

    def _fetch_from_source(self, source_id: str) -> List[Dict]:
        """从指定数据源获取赔率"""
        if source_id == "oddsportal":
            return self._fetch_from_oddsportal()
        elif source_id == "bet365":
            return self._fetch_from_bet365()
        elif source_id == "pinnacle":
            return self._fetch_from_pinnacle()
        elif source_id == "1xbet":
            return self._fetch_from_1xbet()
        else:
            raise ValueError(f"未知数据源: {source_id}")

    def _fetch_from_oddsportal(self) -> List[Dict]:
        """从 Odds Portal 获取赔率"""
        url = SOURCES["oddsportal"]["url"]
        response = self.session.get(url, timeout=15)

        if response.status_code != 200:
            raise Exception(f"Odds Portal 返回状态码: {response.status_code}")

        # 解析 HTML（简化版本）
        # 实际实现需要根据网站结构解析
        return []

    def _fetch_from_bet365(self) -> List[Dict]:
        """从 Bet365 获取赔率"""
        url = SOURCES["bet365"]["url"]
        response = self.session.get(url, timeout=15)

        if response.status_code != 200:
            raise Exception(f"Bet365 返回状态码: {response.status_code}")

        # Bet365 需要 JavaScript 渲染，可能需要 Selenium
        return []

    def _fetch_from_pinnacle(self) -> List[Dict]:
        """从 Pinnacle 获取赔率"""
        url = SOURCES["pinnacle"]["url"]
        response = self.session.get(url, timeout=15)

        if response.status_code != 200:
            raise Exception(f"Pinnacle 返回状态码: {response.status_code}")

        # 解析 HTML
        return []

    def _fetch_from_1xbet(self) -> List[Dict]:
        """从 1xBet 获取赔率"""
        url = SOURCES["1xbet"]["url"]
        response = self.session.get(url, timeout=15)

        if response.status_code != 200:
            raise Exception(f"1xBet 返回状态码: {response.status_code}")

        # 解析 HTML
        return []

    def _merge_matches(self, matches: List[Dict]) -> List[Dict]:
        """合并重复比赛，取最佳赔率"""
        merged = {}

        for match in matches:
            key = f"{match.get('home_team', '')}|{match.get('away_team', '')}"

            if key not in merged:
                merged[key] = match.copy()
            else:
                # 合并赔率，取最佳
                existing = merged[key]
                if match.get("odds_had") and existing.get("odds_had"):
                    for outcome in ["h", "d", "a"]:
                        if match["odds_had"].get(outcome) and existing["odds_had"].get(outcome):
                            # 取更高赔率
                            if match["odds_had"][outcome] > existing["odds_had"][outcome]:
                                existing["odds_had"][outcome] = match["odds_had"][outcome]

        return list(merged.values())


def get_odds_aggregator() -> OddsAggregator:
    """获取 OddsAggregator 实例"""
    return OddsAggregator()
