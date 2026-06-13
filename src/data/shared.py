"""
共享数据模块 — 统一数据获取和缓存

所有页面使用相同的数据获取逻辑，确保数据一致性
"""

import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import streamlit as st

from .loader import load_all
from .sporttery_scraper import SportteryScraper, odds_to_win_probability
from .odds_scraper import get_odds_scraper
from .live_data import get_live_fetcher
from .squad_fetcher import get_squad_fetcher
from ..utils.config import TEAMS

logger = logging.getLogger(__name__)

# 北京时间
BEIJING_TZ = ZoneInfo("Asia/Shanghai")

# ── 队伍名称标准化 ─────────────────────────────────────
TEAM_NAME_MAP = {
    "Bosnia-Herzegovina": "Bosnia",
    "United States": "USA",
    "Czechia": "Czech Republic",
    "Korea Republic": "South Korea",
    "Türkiye": "Turkey",
    "Congo DR": "DR Congo",
    "Curaçao": "Curacao",
}

def normalize_team_name(name: str) -> str:
    """标准化队伍名称"""
    return TEAM_NAME_MAP.get(name, name)


# ── 数据获取函数 ─────────────────────────────────────

@st.cache_data(ttl=600)
def load_schedule_data() -> Dict:
    """加载赛程数据（10分钟更新）"""
    return load_all()


@st.cache_data(ttl=30)
def fetch_live_odds() -> Optional[Dict]:
    """获取实时赔率数据，优先中国体彩"""
    all_odds = []
    source = "none"

    # 优先尝试中国体彩（竞彩网）
    try:
        sporttery_data = SportteryScraper().get_all_world_cup_data()
        if sporttery_data and sporttery_data.get("all_odds"):
            all_odds.extend(sporttery_data["all_odds"])
            source = "sporttery"
            logger.info(f"从中国竞彩网获取到 {len(sporttery_data['all_odds'])} 场比赛赔率")
    except Exception as e:
        logger.warning(f"中国竞彩网获取失败（可能在国外）: {e}")

    # 如果中国体彩失败，尝试海外数据源
    if not all_odds:
        logger.info("中国体彩无法访问，尝试海外数据源...")
        try:
            scraper = get_odds_scraper()
            odds_list = scraper.get_world_cup_odds()
            if odds_list:
                all_odds.extend(odds_list)
                source = "oddsportal"
                logger.info(f"从 Odds Portal 获取到 {len(odds_list)} 场比赛赔率")
        except Exception as e:
            logger.warning(f"Odds Portal 获取失败: {e}")

    if all_odds:
        return {
            "source": source,
            "all_odds": all_odds,
            "live_today": [],
            "upcoming": all_odds,
            "completed": [],
        }

    return None


@st.cache_data(ttl=30)
def fetch_live_matches() -> List[Dict]:
    """获取实时比赛数据（每30秒更新）"""
    try:
        fetcher = get_live_fetcher()
        matches = fetcher.get_live_matches()
        if matches:
            logger.info(f"成功获取 {len(matches)} 场实时比赛")
        return matches
    except Exception as e:
        logger.error(f"实时数据获取失败: {e}")
        return []


def load_results_file() -> Dict:
    """从 live_results.json 读取比赛结果"""
    results_file = Path(__file__).parent.parent.parent / "data" / "bundled" / "live_results.json"
    if results_file.exists():
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"读取比赛结果文件失败: {e}")
    return {"events": []}


def build_live_match_map(live_matches: List[Dict]) -> Dict:
    """
    构建实时比赛数据映射

    合并实时数据和结果文件数据
    """
    match_map = {}
    today = datetime.now(BEIJING_TZ).date()
    today_str = today.isoformat()

    # 从实时数据构建
    for m in live_matches:
        home = normalize_team_name(m.get("home_team", ""))
        away = normalize_team_name(m.get("away_team", ""))
        if home and away:
            key = f"{home}|{away}"
            match_map[key] = m

    # 从结果文件补充
    results = load_results_file()
    for event in results.get("events", []):
        name = event.get("name", "")
        if " at " not in name:
            continue

        parts = name.split(" at ")
        away_team = normalize_team_name(parts[0].strip())
        home_team = normalize_team_name(parts[1].strip())
        key = f"{home_team}|{away_team}"

        if key not in match_map:
            # 检查比赛日期
            event_date = event.get("date", "")
            if event_date:
                # 解析日期（格式：2026-06-13T19:00Z）
                try:
                    match_date = event_date[:10]  # 取日期部分
                except:
                    match_date = ""
            else:
                match_date = ""

            # 只有今天或之前的比赛才标记为已结束
            if match_date and match_date <= today_str:
                competitors = event.get("competitions", [{}])[0].get("competitors", [])
                if len(competitors) == 2:
                    home_score = int(competitors[0].get("score", "0"))
                    away_score = int(competitors[1].get("score", "0"))

                    # 检查比赛状态
                    status_type = event.get("competitions", [{}])[0].get("status", {}).get("type", {})
                    status_name = status_type.get("name", "")

                    if status_name == "STATUS_FULL_TIME" or (home_score > 0 or away_score > 0):
                        # 已结束的比赛
                        match_map[key] = {
                            "home_team": home_team,
                            "away_team": away_team,
                            "home_score": home_score,
                            "away_score": away_score,
                            "status": "finished",
                            "status_detail": "FT",
                            "minute": "90'",
                            "events": [],
                            "source": "results_file",
                        }
                    else:
                        # 未开始或进行中的比赛
                        match_map[key] = {
                            "home_team": home_team,
                            "away_team": away_team,
                            "home_score": home_score,
                            "away_score": away_score,
                            "status": "scheduled",
                            "status_detail": "Scheduled",
                            "minute": "0",
                            "events": [],
                            "source": "results_file",
                        }

    return match_map


def get_finished_matches_from_schedule(schedule: pd.DataFrame) -> pd.DataFrame:
    """从赛程获取今天之前的比赛"""
    today = datetime.now(BEIJING_TZ).date()
    past = schedule[schedule["match_date"] < pd.Timestamp(today)]
    return past[past["home_team"] != "TBD"]


def get_finished_count(schedule: pd.DataFrame, live_matches: List[Dict]) -> int:
    """计算已完场比赛数量"""
    finished_count = len(get_finished_matches_from_schedule(schedule))

    # 加上今天已结束的比赛
    today_finished = len([m for m in live_matches if m.get("status") == "finished"])
    finished_count += today_finished

    return finished_count


@st.cache_data(ttl=3600)
def fetch_team_squad(team: str) -> List[Dict]:
    """获取球队阵容数据（1小时缓存）"""
    try:
        fetcher = get_squad_fetcher()
        return fetcher.get_team_squad(team)
    except Exception as e:
        logger.warning(f"获取 {team} 阵容失败: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_match_squads(home_team: str, away_team: str) -> Dict:
    """获取比赛双方阵容（1小时缓存）"""
    try:
        fetcher = get_squad_fetcher()
        return fetcher.get_match_squad(home_team, away_team)
    except Exception as e:
        logger.warning(f"获取 {home_team} vs {away_team} 阵容失败: {e}")
        return {"home": {"squad": [], "injuries": []}, "away": {"squad": [], "injuries": []}}
