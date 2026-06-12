"""
中国体育彩票竞彩网 — 世界杯赔率 & 赛果实时爬虫

数据来源：webapi.sporttery.cn（中国体彩官方API）
- 实时赔率：getMatchCalculatorV1.qry
- 赛果：getMatchResultV1.qry
- 赛事列表：getMatchListV1.qry

用法：
    scraper = SportteryScraper()
    matches = scraper.get_world_cup_odds()       # 实时赔率
    results = scraper.get_world_cup_results()     # 已完场赛果
    all_data = scraper.get_all_world_cup_data()   # 全部数据
"""

import requests
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── API 端点 ─────────────────────────────────────
BASE_URL = "https://webapi.sporttery.cn/gateway/jc/football"
ODDS_URL = f"{BASE_URL}/getMatchCalculatorV1.qry"
RESULT_URL = f"{BASE_URL}/getMatchResultV1.qry"
MATCH_LIST_URL = f"{BASE_URL}/getMatchListV1.qry"

# World Cup league IDs
WC_LEAGUE_ID = 72  # 世界杯
WC_LEAGUE_CODE = "WCC"

# ── 标准浏览器头 ───────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.sporttery.cn/",
    "Origin": "https://www.sporttery.cn",
}

# ── 球队名称映射（中文→英文）───────────────────
# 基于竞彩网缩写反查
TEAM_NAME_MAP = {
    # UEFA
    "法国": "France", "英格兰": "England", "西班牙": "Spain", "德国": "Germany",
    "葡萄牙": "Portugal", "荷兰": "Netherlands", "意大利": "Italy", "比利时": "Belgium",
    "克罗地亚": "Croatia", "丹麦": "Denmark", "瑞士": "Switzerland", "瑞典": "Sweden",
    "挪威": "Norway", "奥地利": "Austria", "威尔士": "Wales", "塞尔维亚": "Serbia",
    "乌克兰": "Ukraine", "波兰": "Poland", "捷克": "Czech Republic", "匈牙利": "Hungary",
    "捷克共和国": "Czech Republic", "捷克(中)": "Czech Republic",
    "苏格兰": "Scotland", "土耳其": "Turkey", "俄罗斯": "Russia",
    # CONMEBOL
    "阿根廷": "Argentina", "巴西": "Brazil", "乌拉圭": "Uruguay", "哥伦比亚": "Colombia",
    "秘鲁": "Peru", "智利": "Chile", "厄瓜多尔": "Ecuador", "巴拉圭": "Paraguay",
    "玻利维亚": "Bolivia", "委内瑞拉": "Venezuela",
    # CAF
    "摩洛哥": "Morocco", "塞内加尔": "Senegal", "突尼斯": "Tunisia", "阿尔及利亚": "Algeria",
    "埃及": "Egypt", "尼日利亚": "Nigeria", "喀麦隆": "Cameroon", "科特迪瓦": "Ivory Coast",
    "南非": "South Africa", "加纳": "Ghana", "马里": "Mali", "布基纳法索": "Burkina Faso",
    # AFC
    "日本": "Japan", "韩国": "South Korea", "伊朗": "Iran", "沙特阿拉伯": "Saudi Arabia",
    "澳大利亚": "Australia", "卡塔尔": "Qatar", "伊拉克": "Iraq",
    "阿联酋": "United Arab Emirates", "乌兹别克斯坦": "Uzbekistan",
    "约旦": "Jordan", "阿曼": "Oman", "巴林": "Bahrain", "中国": "China",
    "叙利亚": "Syria", "泰国": "Thailand", "越南": "Vietnam", "朝鲜": "North Korea",
    # Additional
    "波黑": "Bosnia", "苏格兰": "Scotland", "土耳其": "Turkey", "冰岛": "Iceland",
    "希腊": "Greece", "爱尔兰": "Ireland", "北爱尔兰": "Northern Ireland",
    "斯洛伐克": "Slovakia", "斯洛文尼亚": "Slovenia", "罗马尼亚": "Romania",
    "保加利亚": "Bulgaria", "芬兰": "Finland", "以色列": "Israel",
    "格鲁吉亚": "Georgia", "黑山": "Montenegro", "阿尔巴尼亚": "Albania",
    "北马其顿": "North Macedonia", "白俄罗斯": "Belarus",
    "科索沃": "Kosovo", "塞浦路斯": "Cyprus", "卢森堡": "Luxembourg",
    "刚果": "Congo", "民主刚果": "DR Congo", "刚果(金)": "DR Congo",
    "刚果民主共和国": "DR Congo", "几内亚": "Guinea",
    "赞比亚": "Zambia", "乌干达": "Uganda", "加蓬": "Gabon", "贝宁": "Benin",
    "佛得角": "Cape Verde", "马达加斯加": "Madagascar", "肯尼亚": "Kenya",
    "安哥拉": "Angola", "多哥": "Togo", "莫桑比克": "Mozambique",
    "利比亚": "Libya", "苏丹": "Sudan", "津巴布韦": "Zimbabwe",
    "印度": "India", "印尼": "Indonesia", "马来西亚": "Malaysia",
    "菲律宾": "Philippines", "新加坡": "Singapore", "科威特": "Kuwait",
    "黎巴嫩": "Lebanon", "塔吉克斯坦": "Tajikistan", "吉尔吉斯斯坦": "Kyrgyzstan",
    "土库曼斯坦": "Turkmenistan", "也门": "Yemen", "缅甸": "Myanmar",
    "危地马拉": "Guatemala", "海地": "Haiti", "库拉索": "Curacao",
    "特立尼达和多巴哥": "Trinidad and Tobago", "苏里南": "Suriname",
    # Equivalents
    "美国(女)": "USA", "日本(女)": "Japan", "德国(女)": "Germany",
    "英格兰(女)": "England", "法国(女)": "France", "西班牙(女)": "Spain",
    "加拿大(女)": "Canada", "荷兰(女)": "Netherlands", "巴西(女)": "Brazil",
    "澳大利亚(女)": "Australia", "瑞典(女)": "Sweden", "挪威(女)": "Norway",
    "中国(女)": "China", "韩国(女)": "South Korea",
    "意大利(女)": "Italy", "丹麦(女)": "Denmark",
    # CONCACAF
    "美国": "USA", "加拿大": "Canada", "墨西哥": "Mexico",
    "哥斯达黎加": "Costa Rica", "牙买加": "Jamaica", "巴拿马": "Panama",
    "洪都拉斯": "Honduras", "萨尔瓦多": "El Salvador",
    # OFC
    "新西兰": "New Zealand",
}

# ESPN英文名 → 标准英文名映射
ESPN_NAME_MAP = {
    "Türkiye": "Turkey",
    "Czechia": "Czech Republic",
    "Congo DR": "DR Congo",
    "Bosnia-Herzegovina": "Bosnia",
    "Curaçao": "Curacao",
    "Korea Republic": "South Korea",
    "USA": "USA",
    "United States": "USA",
}

def normalize_english_name(name: str) -> str:
    """标准化英文队名（处理 ESPN/FIFA 等不同来源的命名差异）"""
    return ESPN_NAME_MAP.get(name, name)


# 反向映射
def to_english_name(cn_name: str) -> Optional[str]:
    """中文队名→英文队名"""
    if cn_name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[cn_name]
    # Try partial match
    for cn, en in TEAM_NAME_MAP.items():
        if cn in cn_name or cn_name in cn:
            return en
    return None


class SportteryScraper:
    """中国竞彩网爬虫 — 世界杯数据"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}
        self._cache_time = {}

    def _get_json(self, url: str, params: dict = None, cache_ttl: int = 60) -> Optional[dict]:
        """带缓存的JSON请求"""
        cache_key = url + json.dumps(params or {}, sort_keys=True)
        now = datetime.now()

        if cache_key in self._cache:
            age = (now - self._cache_time[cache_key]).total_seconds()
            if age < cache_ttl:
                return self._cache[cache_key]

        try:
            r = self.session.get(url, params=params, timeout=15)
            r.encoding = 'utf-8'
            if r.status_code == 200 and r.text.strip().startswith('{'):
                data = r.json()
                if data.get("success"):
                    self._cache[cache_key] = data
                    self._cache_time[cache_key] = now
                    return data
            logger.warning(f"API failed: status={r.status_code}, text_preview={r.text[:200]}")
        except Exception as e:
            logger.error(f"Request error: {e}")
        return None

    def get_world_cup_odds(self) -> List[Dict]:
        """
        获取世界杯比赛实时赔率。
        包含：胜平负(HAD) + 让球胜平负(HHAD)

        Returns:
            [{
                "match_num": "5003",
                "date": "2026-06-12",
                "league": "世界杯",
                "home_team": "Canada",
                "away_team": "Bosnia",
                "home_team_cn": "加拿大",
                "away_team_cn": "波黑",
                "odds_had": {"h": 1.62, "d": 3.32, "a": 4.75},
                "odds_hhad": {"h": 3.58, "d": 2.90, "a": 1.98, "goal_line": "-1"},
                "update_time": "21:52:31",
            }, ...]
        """
        data = self._get_json(ODDS_URL, {"poolCode": "hhad,had,ttg", "channel": "c"}, cache_ttl=120)
        if not data:
            return []

        matches = []
        for day_data in data["value"]["matchInfoList"]:
            for m in day_data["subMatchList"]:
                # 只取世界杯
                if m.get("leagueCode") != WC_LEAGUE_CODE and m.get("leagueId") != WC_LEAGUE_ID:
                    continue

                had = m.get("had", {})
                hhad = m.get("hhad", {})

                home_cn = m.get("homeTeamAllName", "")
                away_cn = m.get("awayTeamAllName", "")
                home_en = to_english_name(home_cn) or home_cn
                away_en = to_english_name(away_cn) or away_cn

                # 仅保留2026世界杯48支正赛球队（双方都必须在）
                if home_en not in WC2026_TEAMS or away_en not in WC2026_TEAMS:
                    continue

                # businessDate 是销售日，真实比赛日 = businessDate + 1天
                from datetime import datetime as _dt, timedelta as _td
                _biz = _dt.strptime(day_data["businessDate"], "%Y-%m-%d")
                _real = (_biz + _td(days=1)).strftime("%Y-%m-%d")

                match_info = {
                    "match_num": m.get("matchNum", ""),
                    "date": _real,
                    "match_time": m.get("matchTime", "")[:5],
                    "league": m.get("leagueAllName", "世界杯"),
                    "league_code": m.get("leagueCode", ""),
                    "home_team_cn": home_cn,
                    "away_team_cn": away_cn,
                    "home_team": home_en,
                    "away_team": away_en,
                    "home_team_code": m.get("homeTeamCode", ""),
                    "away_team_code": m.get("awayTeamCode", ""),
                    "is_hot": m.get("isHot", 0),
                }

                # HAD 赔率
                if had and had.get("h"):
                    match_info["odds_had"] = {
                        "h": float(had["h"]),
                        "d": float(had["d"]),
                        "a": float(had["a"]),
                        "update_time": had.get("updateTime", ""),
                    }

                # HHAD 让球赔率
                if hhad and hhad.get("h"):
                    match_info["odds_hhad"] = {
                        "h": float(hhad["h"]),
                        "d": float(hhad["d"]),
                        "a": float(hhad["a"]),
                        "goal_line": hhad.get("goalLine", "0"),
                        "update_time": hhad.get("updateTime", ""),
                    }

                # TTG 大小球赔率
                ttg = m.get("ttg", {})
                if ttg and ttg.get("lines"):
                    ttg_odds = {}
                    for line_data in ttg["lines"]:
                        line_value = line_data.get("line", "")
                        over_odds = line_data.get("over")
                        under_odds = line_data.get("under")

                        if over_odds and under_odds:
                            # 标准化盘口键名
                            line_key = line_value.replace(".", "_")
                            ttg_odds[f"over_{line_key}"] = float(over_odds)
                            ttg_odds[f"under_{line_key}"] = float(under_odds)

                    if ttg_odds:
                        match_info["odds_ttg"] = ttg_odds

                matches.append(match_info)

        return matches

    def get_world_cup_results(self, days_back: int = 7) -> List[Dict]:
        """
        获取已完场世界杯比赛结果。

        Returns:
            [{
                "match_num": "5001",
                "date": "2026-06-12",
                "home_team": "USA",
                "away_team": "England",
                "home_score": 2,
                "away_score": 1,
                "result": "H",  # H=主胜 D=平 A=客胜
                "half_score": "1-0",
            }, ...]
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        data = self._get_json(RESULT_URL, {
            "matchPage": 1,
            "matchBeginDate": start_date.strftime("%Y-%m-%d"),
            "matchEndDate": end_date.strftime("%Y-%m-%d"),
            "leagueId": WC_LEAGUE_ID,
        }, cache_ttl=300)

        if not data:
            return []

        results = []
        for r in data["value"].get("matchResult", []):
            home_cn = r.get("homeTeamAllName", "")
            away_cn = r.get("awayTeamAllName", "")

            # 解析比分
            score_str = r.get("sectionsNo999", "0:0")
            parts = score_str.split(":")
            home_score = int(parts[0]) if len(parts) >= 2 and parts[0].isdigit() else 0
            away_score = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0

            # 半场比分
            half_score = r.get("sectionsNo1", "")

            result_code = r.get("winFlag", "")  # H/D/A

            results.append({
                "match_num": r.get("matchNum", ""),
                "date": r.get("matchDate", ""),
                "home_team_cn": home_cn,
                "away_team_cn": away_cn,
                "home_team": to_english_name(home_cn) or home_cn,
                "away_team": to_english_name(away_cn) or away_cn,
                "home_score": home_score,
                "away_score": away_score,
                "result": result_code,
                "half_score": half_score,
                "league": r.get("leagueAllName", ""),
                "goal_line": r.get("goalLine", "0"),
            })

        return results

    def get_world_cup_schedule(self) -> List[Dict]:
        """
        获取世界杯全部赛程（包含未开赛和已完场）。

        Returns match list with match status.
        """
        data = self._get_json(MATCH_LIST_URL, {
            "leagueId": WC_LEAGUE_ID,
        }, cache_ttl=600)

        if not data:
            return []

        matches = []
        for m in data["value"].get("matchList", []):
            home_cn = m.get("homeTeamAllName", "")
            away_cn = m.get("awayTeamAllName", "")

            match_info = {
                "match_num": m.get("matchNum", ""),
                "date": m.get("matchDate", ""),
                "time": m.get("matchTime", ""),
                "home_team_cn": home_cn,
                "away_team_cn": away_cn,
                "home_team": to_english_name(home_cn) or home_cn,
                "away_team": to_english_name(away_cn) or away_cn,
                "status": m.get("matchStatus", ""),  # 0=未开始 1=进行中 2=已结束
                "league": m.get("leagueAllName", ""),
            }

            # Add score if available
            if m.get("homeScore") is not None:
                match_info["home_score"] = int(m.get("homeScore", 0))
                match_info["away_score"] = int(m.get("awayScore", 0))

            matches.append(match_info)

        return matches

    def get_all_world_cup_data(self) -> Dict:
        """
        获取完整世界杯数据：赛程+赔率+赛果

        根据赔率状态推断比赛进度：
        - 有HAD赔率 + 今天日期 → 即将开赛/未开始
        - 仅有HHAD赔率无HAD → 可能正在进行中
        - 日期在过去 + 无赔率 → 已完场
        """
        odds = self.get_world_cup_odds()
        results = self.get_world_cup_results()

        today = date.today().isoformat()
        now = datetime.now()
        live_matches = []      # 今天正在进行/即将开始
        completed_matches = [] # 已完场
        upcoming_matches = []  # 未来几天

        # 将赛果转为查找表
        result_map = {r["match_num"]: r for r in results}

        for m in odds:
            match_num = m["match_num"]
            had = m.get("odds_had")

            if match_num in result_map:
                # 官方标记已完场
                res = result_map[match_num]
                m["home_score"] = res["home_score"]
                m["away_score"] = res["away_score"]
                m["result_code"] = res["result"]
                m["match_status"] = "completed"
                completed_matches.append(m)
            elif m["date"] < today:
                # 过去日期的比赛，可能已结束
                m["match_status"] = "likely_completed"
                completed_matches.append(m)
            elif m["date"] == today:
                # 今天：有HAD赔率=未开赛, 仅有HHAD=可能在踢
                if had:
                    m["match_status"] = "upcoming"
                else:
                    m["match_status"] = "possibly_live"
                live_matches.append(m)
            else:
                m["match_status"] = "upcoming"
                upcoming_matches.append(m)

        # 分类汇总
        by_date = {}
        for m in odds:
            d = m["date"]
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(m)

        return {
            "live_today": live_matches,
            "upcoming": upcoming_matches,
            "completed": completed_matches,
            "all_odds": odds,
            "all_results": results,
            "by_date": by_date,
            "fetched_at": datetime.now().isoformat(),
        }


# ── 全局单例 ───────────────────────────────────
_scraper_instance: Optional[SportteryScraper] = None


def get_scraper() -> SportteryScraper:
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = SportteryScraper()
    return _scraper_instance


# ── 2026 世界杯 48 队白名单 ──────────────────────
WC2026_TEAMS = {
    # UEFA (16)
    "England", "France", "Croatia", "Norway", "Portugal", "Germany", "Netherlands",
    "Switzerland", "Scotland", "Spain", "Austria", "Belgium", "Bosnia", "Sweden",
    "Turkey", "Czech Republic",
    # CAF (9 + 1 playoff)
    "Algeria", "Cape Verde", "DR Congo", "Egypt", "Ghana", "Ivory Coast", "Morocco",
    "Senegal", "South Africa", "Tunisia",
    # AFC (8+1)
    "Australia", "Iran", "Japan", "Jordan", "Uzbekistan", "Qatar", "Saudi Arabia",
    "South Korea", "Iraq",
    # CONMEBOL (6)
    "Argentina", "Brazil", "Colombia", "Ecuador", "Paraguay", "Uruguay",
    # CONCACAF (3+3)
    "Panama", "Curacao", "Haiti", "USA", "Canada", "Mexico",
    # OFC (1)
    "New Zealand",
}


def odds_to_win_probability(h: float, d: float, a: float) -> Dict[str, float]:
    """
    赔率 → 隐含概率（去水后）

    竞彩返奖率约 86-89%，这里用简单归一化。
    """
    # 隐含概率 (1/odds)，保护零值/负值
    if h <= 0 or d <= 0 or a <= 0:
        return {"home_win": 0.0, "draw": 0.0, "away_win": 0.0}
    imp_h = 1.0 / h
    imp_d = 1.0 / d
    imp_a = 1.0 / a

    total = imp_h + imp_d + imp_a

    return {
        "home_win": round(imp_h / total, 4),
        "draw": round(imp_d / total, 4),
        "away_win": round(imp_a / total, 4),
    }


def odds_to_expected_goals(h: float, d: float, a: float) -> Tuple[float, float]:
    """
    根据赔率粗略推算预期进球。

    启发式方法：
    - 胜率差距 ≈ 预期进球差距
    - 赔率隐含概率映射到lambda
    """
    probs = odds_to_win_probability(h, d, a)
    home_prob = probs["home_win"]
    away_prob = probs["away_win"]

    # 用胜率差估算进球差
    prob_diff = home_prob - away_prob

    # 映射到预期进球 (基线 ~1.4-1.1 per team)
    base_total = 2.5
    home_share = 0.5 + prob_diff * 0.5
    away_share = 0.5 - prob_diff * 0.5

    lambda_h = base_total * home_share
    lambda_a = base_total * away_share

    return round(lambda_h, 2), round(lambda_a, 2)
