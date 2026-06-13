"""
🏆 2026 世界杯预测工具 — 首页
数据来源：赛程 CSV + 中国竞彩网实时赔率
"""

import sys, os, math
import logging
import subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import defaultdict

logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

from src.data.shared import (
    load_schedule_data, fetch_live_odds, fetch_live_matches,
    build_live_match_map, get_finished_count, normalize_team_name
)
from src.models.predictor import MatchPredictor
from src.data.sporttery_scraper import odds_to_win_probability
from src.utils.viz_helpers import create_champion_bar_chart, create_confederation_pie
from src.utils.config import TEAMS, GROUPS

# ── 页面设置 ────────────────────────────────────────
st.set_page_config(page_title="2026 世界杯预测工具", page_icon="🏆", layout="wide")

# 自动刷新（30秒）
st_autorefresh(interval=30000, key="main_autorefresh")

# ── 样式 ───────────────────────────────────────────
st.markdown("""
<style>
.main .block-container { padding-top: 2rem; }
.stMetric { background-color: #1e293b; padding: 1rem; border-radius: 0.5rem; }
.stMetric label { color: #94a3b8 !important; }
h1 { color: #fbbf24 !important; }
h2, h3 { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── 加载数据 ───────────────────────────────────────
data = load_schedule_data()
schedule = data["schedule"]

@st.cache_resource
def init_predictor():
    pred = MatchPredictor()
    if not data["historical"].empty:
        pred.load_historical_data(data["historical"])
    return pred

predictor = init_predictor()

live = fetch_live_odds()
data_source = live.get("source", "none") if live else "none"

live_matches = fetch_live_matches()
live_match_map = build_live_match_map(live_matches)

# ── 常量 ───────────────────────────────────────────
TOURNAMENT_START = date(2026, 6, 12)
TOURNAMENT_END = date(2026, 7, 20)
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
today = datetime.now(BEIJING_TZ).date()
now_beijing = datetime.now(BEIJING_TZ)

# ── 计算已完场数 ───────────────────────────────────
finished_count = get_finished_count(schedule, live_matches)

# ── 侧边栏 ─────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/football2--v1.png", width=64)
    st.title("🏆 2026 世界杯预测")

    if live:
        n = len(live.get("all_odds", []))
        source_name = {
            "sporttery": "中国体彩",
            "multi_source": "海外数据源",
            "oddsportal": "Odds Portal",
        }.get(live.get("source"), "赔率数据")
        st.markdown(f"🟢 **{source_name}已连接** — {n} 场比赛")
    else:
        st.markdown("🔴 赔率数据未连接")

    st.markdown("---")
    st.markdown(f"**赛事时间：** 2026.6.12 – 7.20（北京时间）")
    st.markdown(f"**主办国：** 🇺🇸 美国 · 🇨🇦 加拿大 · 🇲🇽 墨西哥")
    st.markdown(f"**参赛队伍：** 48 支 · 12 组 · 104 场比赛")

    st.markdown("---")
    st.markdown(f"**实时状态：** ✅已完场 {finished_count} 场")

    # 可展开的已结束比赛列表
    with st.expander("✅ 已结束比赛", expanded=False):
        # 从赛程获取今天之前的比赛
        if not schedule.empty:
            past = schedule[schedule["match_date"] < pd.Timestamp(today)]
            past_real = past[past["home_team"] != "TBD"]

            # 按日期分组
            dates_shown = set()
            for _, match in past_real.iterrows():
                home = match["home_team"]
                away = match["away_team"]
                match_date = match["match_date"].strftime("%m月%d日") if hasattr(match["match_date"], "strftime") else ""

                if match_date and match_date not in dates_shown:
                    st.markdown(f"**📅 {match_date}**")
                    dates_shown.add(match_date)

                key = f"{home}|{away}"
                if key in live_match_map:
                    m = live_match_map[key]
                    score = f"{m.get('home_score', 0)} - {m.get('away_score', 0)}"
                    st.markdown(f"- {home} {score} {away}")
                else:
                    st.markdown(f"- {home} vs {away}")

        # 显示今天已结束的比赛
        finished_today = [m for m in live_matches if m.get("status") == "finished"]
        if finished_today:
            st.markdown(f"**📅 {today.strftime('%m月%d日')}**")
            for match in finished_today:
                home = match.get("home_team", "")
                away = match.get("away_team", "")
                score = f"{match.get('home_score', 0)} - {match.get('away_score', 0)}"
                st.markdown(f"- {home} {score} {away}")

    st.markdown("---")
    st.caption(f"🔄 每30秒自动刷新 | {now_beijing.strftime('%H:%M:%S')} (北京时间)")

# ── 头部 ──────────────────────────────────────────
day = max(1, (today - TOURNAMENT_START).days + 1)
is_tournament = TOURNAMENT_START <= today <= TOURNAMENT_END

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    st.title("🏆 2026 世界杯预测工具")
with c2:
    if is_tournament:
        st.metric("赛事第几天", f"第 {day} 天")
    else:
        st.metric("距开赛", f"{(TOURNAMENT_START - today).days} 天" if today < TOURNAMENT_START else "已结束")
with c3:
    st.metric("已完场", f"{finished_count} 场")

st.markdown("---")

# ── 今日比赛 ───────────────────────────────────────
st.subheader("📅 今日比赛 & 赔率")

# 合并 CSV 赛程 + 竞彩实时数据
live_odds_map = {}
if live and live.get("all_odds"):
    for m in live["all_odds"]:
        key = f"{m['home_team']}|{m['away_team']}"
        live_odds_map[key] = m

# 从 CSV 取最近几天的比赛
if not schedule.empty:
    # 按日期分组
    csv_by_date = defaultdict(list)
    for _, row in schedule.iterrows():
        h, a = row["home_team"], row["away_team"]
        if h == "TBD" or a == "TBD":
            continue
        d = row["match_date"].strftime("%Y-%m-%d") if hasattr(row["match_date"], "strftime") else str(row["match_date"])
        t = row.get("match_time", "")
        csv_by_date[d].append({"home": h, "away": a, "time": t, "group": row["group"]})

    # 显示最近 4 天
    all_dates = sorted(csv_by_date.keys())
    today_str = today.isoformat()
    start_idx = 0
    for i, d in enumerate(all_dates):
        if d >= today_str:
            start_idx = max(0, i - 1)
            break
    show_dates = all_dates[start_idx:start_idx + 4]

    for d in show_dates:
        matches = csv_by_date[d]
        label = f"🟢 今天 ({d})" if d == today_str else f"📅 {d}"
        st.markdown(f"**{label}** — {len(matches)} 场")

        cols = st.columns(min(3, len(matches)))
        for i, item in enumerate(matches):
            with cols[i % 3]:
                h, a, mt = item["home"], item["away"], item["time"]
                hf = TEAMS.get(h, {}).get("flag", "⚽")
                af = TEAMS.get(a, {}).get("flag", "⚽")

                # 查找实时比赛数据（优先）
                key = f"{h}|{a}"
                live_m = live_match_map.get(key)

                # 查找竞彩赔率
                odds_m = live_odds_map.get(key, {})
                had = odds_m.get("odds_had", {})

                # 判断比赛状态
                if live_m:
                    if live_m.get("status") == "live":
                        status = "🔴 进行中"
                    elif live_m.get("status") == "finished":
                        status = "✅ 已完场"
                    else:
                        status = "⏳ 未开赛"
                elif d < today_str:
                    status = "✅ 已完场"
                elif d == today_str:
                    status = "🔴 今日"
                else:
                    status = "⏳ 未开赛"

                if had:
                    sp = odds_to_win_probability(had["h"], had["d"], had["a"])
                    odds_text = f"赔率 {had['h']}/{had['d']}/{had['a']}"
                    prob_text = f"主{sp['home_win']:.0%} 平{sp['draw']:.0%} 客{sp['away_win']:.0%}"
                else:
                    odds_text = "暂无赔率"
                    prob_text = "—"

                # 模型预测
                try:
                    pred = predictor.predict(h, a, neutral=True)
                    model_text = f"主{pred['home_win']:.0%} 平{pred['draw']:.0%} 客{pred['away_win']:.0%}"
                except Exception:
                    model_text = "—"

                # 比分
                score = ""
                if live_m and live_m.get("home_score") is not None:
                    score = f" | {live_m['home_score']}-{live_m['away_score']}"

                st.markdown(f"""
                <div style="background:#1e293b;padding:0.8rem;border-radius:0.5rem;margin-bottom:0.5rem;font-size:0.9em;">
                    <small style="color:#94a3b8;">{mt} {status}{score}</small><br>
                    <b>{hf} {h}</b> vs <b>{a} {af}</b><br>
                    <small style="color:#94a3b8;">{odds_text}</small><br>
                    <small><span style="color:#fbbf24;">市场:</span> <span style="color:#22c55e;">{prob_text}</span></small><br>
                    <small><span style="color:#60a5fa;">模型:</span> <span style="color:#60a5fa;">{model_text}</span></small>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("暂无赛程数据。")

# ── 实时比赛 ─────────────────────────────────────────
if live_matches:
    st.markdown("---")
    st.subheader("🔴 实时比赛")

    live_now = [m for m in live_matches if m.get("status") == "live"]
    if live_now:
        for match in live_now:
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            home_score = match.get("home_score", 0)
            away_score = match.get("away_score", 0)
            minute = match.get("minute", "")

            home_flag = TEAMS.get(home, {}).get("flag", "⚽")
            away_flag = TEAMS.get(away, {}).get("flag", "⚽")

            st.markdown(f"""
            <div style="background:#1e293b;padding:1rem;border-radius:0.5rem;margin-bottom:1rem;border-left:4px solid #ef4444;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <b style="font-size:1.2em;">{home_flag} {home}</b>
                        <span style="font-size:1.5em;font-weight:bold;margin:0 1rem;color:#fbbf24;">{home_score} - {away_score}</span>
                        <b style="font-size:1.2em;">{away} {away_flag}</b>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:#ef4444;font-weight:bold;">🔴 {minute}'</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    finished = [m for m in live_matches if m.get("status") == "finished"]
    if finished:
        for match in finished[:5]:
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            home_score = match.get("home_score", 0)
            away_score = match.get("away_score", 0)

            home_flag = TEAMS.get(home, {}).get("flag", "⚽")
            away_flag = TEAMS.get(away, {}).get("flag", "⚽")

            st.markdown(f"""
            <div style="background:#1e293b;padding:0.8rem;border-radius:0.5rem;margin-bottom:0.5rem;">
                <b>{home_flag} {home}</b>
                <span style="font-size:1.2em;font-weight:bold;margin:0 0.5rem;">{home_score} - {away_score}</span>
                <b>{away} {away_flag}</b>
                <span style="color:#94a3b8;margin-left:0.5rem;">✅ 已结束</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("---")
    st.subheader("🔴 实时比赛")
    st.info("暂无正在进行的比赛")

st.markdown("---")

# ── 冠军概率 ──────────────────────────────────────
st.subheader("🏆 冠军概率排行")

all_elos = predictor.get_all_elos()
elo_sorted = sorted(all_elos.items(), key=lambda x: x[1], reverse=True)
avg_elo = sum(all_elos.values()) / len(all_elos)
raw = [(t, 1.0 / (1.0 + math.exp(-(r - avg_elo) / 200.0))) for t, r in elo_sorted[:15]]
total = sum(p for _, p in raw)
elo_probs = [(t, p / total) for t, p in raw]

c1, c2 = st.columns([2, 1])
with c1:
    st.plotly_chart(create_champion_bar_chart(elo_probs[:15], "冠军热门（Elo评级）"), use_container_width=True)
with c2:
    team_conf = {n: i["confederation"] for n, i in TEAMS.items()}
    st.plotly_chart(create_confederation_pie(dict(elo_probs), team_conf), use_container_width=True)

# ── 完整赛程表 ─────────────────────────────────────
st.markdown("---")
st.subheader("📋 完整赛程（北京时间）")

if not schedule.empty:
    groups_only = schedule[schedule["group"].isin(list("ABCDEFGHIJKL"))].copy()
    groups_only = groups_only.sort_values(["match_date", "match_time", "group"])

    for g in "ABCDEFGHIJKL":
        g_matches = groups_only[groups_only["group"] == g]
        if g_matches.empty:
            continue
        teams = GROUPS.get(g, [])
        flags = " ".join([f"{TEAMS.get(t,{}).get('flag','')} {t}" for t in teams])
        with st.expander(f"{g} 组 — {flags}", expanded=False):
            rows = []
            for _, r in g_matches.iterrows():
                h, a = r["home_team"], r["away_team"]
                hf = TEAMS.get(h,{}).get("flag","")
                af = TEAMS.get(a,{}).get("flag","")
                rows.append({
                    "日期": r["match_date"].strftime("%m/%d"),
                    "时间": r.get("match_time", ""),
                    "主队": f"{hf} {h}",
                    "客队": f"{af} {a}",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

st.markdown("---")
source_text = {
    "sporttery": "中国体育彩票竞彩网",
    "multi_source": "海外数据源聚合",
    "oddsportal": "Odds Portal",
}.get(data_source, "赔率数据")
st.caption(f"⚽ 2026 世界杯预测工具 | 赔率：{source_text} | 预测仅供参考")
