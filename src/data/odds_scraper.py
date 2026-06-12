"""
海外赔率爬虫 — 无需 API Key

数据来源：oddsportal.com（全球赔率聚合网站）
- 无需注册或 API Key
- 支持多种博彩公司赔率
- 覆盖 FIFA 世界杯

用法：
    scraper = OddsPortalScraper()
    matches = scraper.get_world_cup_odds()
"""

import requests
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── 网站配置 ─────────────────────────────────────
BASE_URL = "https://www.oddsportal.com"
WORLD_CUP_URL = f"{BASE_URL}/football/world/world-cup/"

# 标准浏览器头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class OddsPortalScraper:
    """Odds Portal 赔率爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}

    def _fetch_page(self, url: str) -> Optional[str]:
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"获取页面失败: {url} - {e}")
            return None

    def get_world_cup_odds(self) -> List[Dict]:
        """
        获取世界杯比赛赔率

        Returns:
            [
                {
                    "home_team": "Argentina",
                    "away_team": "Brazil",
                    "date": "2026-06-20",
                    "time": "03:00",
                    "odds_had": {"h": 2.10, "d": 3.20, "a": 4.50},
                    "best_odds": {"h": 2.15, "d": 3.30, "a": 4.60},
                    "bookmakers": ["Bet365", "Betfair", ...]
                }
            ]
        """
        logger.info("正在获取 Odds Portal 世界杯赔率...")

        html = self._fetch_page(WORLD_CUP_URL)
        if not html:
            logger.warning("无法访问 Odds Portal，尝试备用方案...")
            return self._get_odds_from_alternative()

        # 解析 HTML
        matches = self._parse_oddsportal_html(html)

        if not matches:
            logger.warning("Odds Portal 解析失败，尝试备用方案...")
            return self._get_odds_from_alternative()

        logger.info(f"成功获取 {len(matches)} 场比赛赔率")
        return matches

    def _parse_oddsportal_html(self, html: str) -> List[Dict]:
        """解析 Odds Portal HTML"""
        matches = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 查找比赛行
            # Odds Portal 使用特定的 CSS 类来标识比赛
            match_rows = soup.find_all('div', class_=re.compile(r'eventRow'))

            for row in match_rows:
                try:
                    match = self._parse_match_row(row)
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.debug(f"解析比赛行失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"HTML 解析错误: {e}")

        return matches

    def _parse_match_row(self, row) -> Optional[Dict]:
        """解析单个比赛行"""
        # 提取队伍名称
        teams = row.find_all('a', class_=re.compile(r'participant'))
        if len(teams) != 2:
            return None

        home_team = teams[0].get_text(strip=True)
        away_team = teams[1].get_text(strip=True)

        # 提取时间
        time_elem = row.find('div', class_=re.compile(r'time|date'))
        match_time = time_elem.get_text(strip=True) if time_elem else ""

        # 提取赔率
        odds_cells = row.find_all('div', class_=re.compile(r'odds'))
        if len(odds_cells) < 3:
            return None

        try:
            odds_h = float(odds_cells[0].get_text(strip=True))
            odds_d = float(odds_cells[1].get_text(strip=True))
            odds_a = float(odds_cells[2].get_text(strip=True))
        except (ValueError, IndexError):
            return None

        # 解析日期
        date_str = datetime.now().strftime("%Y-%m-%d")
        if match_time:
            # 尝试解析完整日期时间
            try:
                # Odds Portal 格式可能不同，需要根据实际情况调整
                pass
            except:
                pass

        return {
            "home_team": home_team,
            "away_team": away_team,
            "date": date_str,
            "time": match_time,
            "odds_had": {
                "h": odds_h,
                "d": odds_d,
                "a": odds_a,
            },
            "best_odds": {
                "h": odds_h,
                "d": odds_d,
                "a": odds_a,
            },
            "bookmakers": ["OddsPortal"],
            "source": "oddsportal",
        }

    def _get_odds_from_alternative(self) -> List[Dict]:
        """
        备用方案：从其他来源获取赔率
        使用 API-Football 的免费端点
        """
        logger.info("尝试从备用来源获取赔率...")

        # 备用方案 1: 使用 odds-api.com 的免费端点
        try:
            return self._get_from_theoddsapi_free()
        except Exception as e:
            logger.warning(f"备用方案 1 失败: {e}")

        # 备用方案 2: 使用 sportytrader API
        try:
            return self._get_from_sportytrader()
        except Exception as e:
            logger.warning(f"备用方案 2 失败: {e}")

        # 备用方案 3: 使用静态数据（开发测试用）
        logger.warning("所有备用方案失败，使用静态数据")
        return self._get_static_odds()

    def _get_from_theoddsapi_free(self) -> List[Dict]:
        """从 the-odds-api.com 免费端点获取"""
        url = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds"
        params = {
            "regions": "eu",
            "oddsFormat": "decimal",
            "markets": "h2h",
        }

        response = self.session.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return self._parse_theoddsapi_response(data)

        raise Exception(f"API 返回状态码: {response.status_code}")

    def _parse_theoddsapi_response(self, data: List[Dict]) -> List[Dict]:
        """解析 the-odds-api 响应"""
        matches = []

        for event in data:
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence_time = event.get("commence_time", "")

            # 收集所有博彩公司的赔率
            all_odds_h = []
            all_odds_d = []
            all_odds_a = []
            bookmakers = []

            for bookmaker in event.get("bookmakers", []):
                bookmakers.append(bookmaker.get("title", ""))

                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)

                        if name == home_team:
                            all_odds_h.append(price)
                        elif name == away_team:
                            all_odds_a.append(price)
                        elif name == "Draw":
                            all_odds_d.append(price)

            if all_odds_h and all_odds_d and all_odds_a:
                # 解析时间
                try:
                    dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%H:%M")
                except:
                    date_str = commence_time[:10]
                    time_str = ""

                matches.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": date_str,
                    "time": time_str,
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
                    "source": "theoddsapi",
                })

        return matches

    def _get_from_sportytrader(self) -> List[Dict]:
        """从 sportytrader.com 获取"""
        url = "https://www.sportytrader.com/en/odds/football/world-cup/"
        html = self._fetch_page(url)

        if html:
            # 解析 sportytrader HTML
            # 这里需要根据实际网站结构实现
            pass

        raise Exception("Sportytrader 解析未实现")

    def _get_static_odds(self) -> List[Dict]:
        """
        静态赔率数据（开发测试用）
        仅在所有在线源都失败时使用
        """
        logger.warning("使用静态赔率数据（仅用于开发测试）")

        # 2026 世界杯部分比赛的示例赔率
        return [
            {
                "home_team": "Canada",
                "away_team": "Bosnia",
                "date": "2026-06-12",
                "time": "20:00",
                "odds_had": {"h": 2.50, "d": 3.10, "a": 2.90},
                "best_odds": {"h": 2.60, "d": 3.20, "a": 3.00},
                "bookmakers": ["Static"],
                "source": "static",
            },
            {
                "home_team": "USA",
                "away_team": "England",
                "date": "2026-06-13",
                "time": "03:00",
                "odds_had": {"h": 2.80, "d": 3.20, "a": 2.50},
                "best_odds": {"h": 2.90, "d": 3.30, "a": 2.60},
                "bookmakers": ["Static"],
                "source": "static",
            },
            {
                "home_team": "Argentina",
                "away_team": "Brazil",
                "date": "2026-06-20",
                "time": "03:00",
                "odds_had": {"h": 2.10, "d": 3.20, "a": 3.50},
                "best_odds": {"h": 2.15, "d": 3.30, "a": 3.60},
                "bookmakers": ["Static"],
                "source": "static",
            },
        ]


def get_odds_scraper() -> OddsPortalScraper:
    """获取 OddsPortalScraper 实例"""
    return OddsPortalScraper()
