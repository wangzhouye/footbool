"""
🏆 淘汰赛对阵 — 32强完整对阵图
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo

from src.data.shared import (
    load_schedule_data, fetch_live_matches, build_live_match_map, normalize_team_name
)
from src.models.predictor import MatchPredictor
from src.models.monte_carlo import TournamentSimulator
from src.utils.config import GROUPS, TEAMS, BRACKET_SLOTS

# ── 初始化 ────────────────────────────────────────
st.set_page_config(page_title="淘汰赛对阵", page_icon="🏆", layout="wide")

data = load_schedule_data()

@st.cache_resource
def init_predictor():
    pred = MatchPredictor()
    if not data["historical"].empty:
        pred.load_historical_data(data["historical"])
    return pred

predictor = init_predictor()

# 加载实时比赛数据
live_matches = fetch_live_matches()
live_match_map = build_live_match_map(live_matches)

# 北京时间
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
today = datetime.now(BEIJING_TZ).date()

# ── 界面 ──────────────────────────────────────────
st.title("🏆 淘汰赛对阵图")
st.markdown("2026 世界杯 32 强淘汰赛对阵 — 从 1/16 决赛到决赛。")

# ── 小组排名预览 ──────────────────────────────────
with st.expander("📋 12 组小组排名预览（模拟结果）", expanded=False):
    sim = TournamentSimulator(predictor)
    group_cols = st.columns(4)
    for idx, group in enumerate(GROUPS):
        with group_cols[idx % 4]:
            standings = sim.simulate_group(group)
            st.markdown(f"**{group} 组**")
            for i, s in enumerate(standings):
                flag = TEAMS.get(s.team, {}).get("flag", "")
                rank_label = ["🥇", "🥈", "🥉", "4️⃣"][i] if i < 4 else f"{i+1}."
                st.caption(f"{rank_label} {flag} {s.team} — {s.points}分 ({s.goal_diff:+d})")

st.markdown("---")

# ── 模拟淘汰赛 ───────────────────────────────────
@st.cache_data(ttl=300)
def get_bracket_preview():
    sim = TournamentSimulator(predictor)
    result = sim.simulate_tournament()
    return result

result = get_bracket_preview()

# ── 淘汰赛对阵表 ─────────────────────────────────
rounds_info = [
    ("R32", "1/16 决赛", "🔵"),
    ("R16", "1/8 决赛", "🟢"),
    ("QF",  "1/4 决赛", "🟡"),
    ("SF",  "半决赛",   "🟠"),
    ("Third", "三四名决赛", "🥉"),
    ("Final", "决赛",     "🏆"),
]

for round_name, cn_name, icon in rounds_info:
    st.markdown(f"### {icon} {cn_name}")

    matches = result["stage_results"].get(round_name, [])
    if not matches:
        st.caption(f"暂无 {cn_name} 数据。")
        continue

    n_cols = min(4, len(matches))
    cols = st.columns(n_cols)

    for i, match in enumerate(matches):
        with cols[i % n_cols]:
            home = match["home"]
            away = match["away"]
            hf = TEAMS.get(home, {}).get("flag", "⚽")
            af = TEAMS.get(away, {}).get("flag", "⚽")
            winner = match.get("winner", "")

            # 查找实时比赛数据
            key = f"{home}|{away}"
            live_m = live_match_map.get(key)

            # 判断比赛状态
            if live_m:
                if live_m.get("status") == "finished":
                    # 已结束的比赛
                    hg = live_m.get("home_score", 0)
                    ag = live_m.get("away_score", 0)
                    status_text = "✅ 已结束"
                    status_color = "#22c55e"

                    # 确定胜者
                    if hg > ag:
                        winner = home
                    elif ag > hg:
                        winner = away
                    else:
                        winner = "平局（加时/点球）"
                elif live_m.get("status") == "live":
                    # 进行中的比赛
                    hg = live_m.get("home_score", 0)
                    ag = live_m.get("away_score", 0)
                    minute = live_m.get("minute", "")
                    status_text = f"🔴 进行中 {minute}'"
                    status_color = "#ef4444"
                    winner = ""
                else:
                    # 未开始的比赛
                    hg = "-"
                    ag = "-"
                    status_text = "⏳ 未开始"
                    status_color = "#94a3b8"
                    winner = ""
            else:
                # 没有实时数据，使用模拟数据
                hg = match.get('home_goals', '-')
                ag = match.get('away_goals', '-')
                status_text = "📋 模拟预测"
                status_color = "#60a5fa"

            # 预测概率
            try:
                pred = predictor.predict(home, away, neutral=True)
                prob_home = pred["home_win"]
                prob_draw = pred["draw"]
                prob_away = pred["away_win"]
                prob_text = f"主{prob_home:.0%} 平{prob_draw:.0%} 客{prob_away:.0%}"
            except Exception:
                prob_home = 0.5
                prob_text = "—"

            # 胜者高亮
            home_style = "color:#fbbf24;font-weight:bold;" if winner == home else ""
            away_style = "color:#fbbf24;font-weight:bold;" if winner == away else ""
            border_color = '#fbbf24' if winner == home else '#ef4444' if winner == away else '#64748b'

            # 构建显示内容
            winner_text = ""
            if winner and winner != "平局（加时/点球）":
                winner_flag = TEAMS.get(winner, {}).get('flag', '')
                winner_text = f'<small style="color:#22c55e;">🏆 胜者：{winner_flag} {winner}</small><br>'
            elif winner == "平局（加时/点球）":
                winner_text = f'<small style="color:#fbbf24;">⚽ {winner}</small><br>'

            st.markdown(f"""
            <div style="background-color:#1e293b;padding:0.8rem;border-radius:0.5rem;margin-bottom:0.5rem;
                        border-left:3px solid {border_color}">
                <small style="color:{status_color};">{status_text}</small><br>
                <span style="{home_style}">{hf} {home}</span> <b>{hg}</b><br>
                <span style="{away_style}">{af} {away}</span> <b>{ag}</b><br>
                {winner_text}
                <small style="color:#94a3b8;">{prob_text}</small>
            </div>
            """, unsafe_allow_html=True)

# ── 冠军 ──────────────────────────────────────────
st.markdown("---")
champion = result.get("champion", "待定")
champion_flag = TEAMS.get(champion, {}).get("flag", "")
st.markdown(f"""
<div style="background:linear-gradient(135deg, #1a365d, #2d1b69);padding:2rem;border-radius:1rem;text-align:center;">
    <h1 style="color:#fbbf24;margin:0;">{champion_flag} {champion}</h1>
    <p style="color:#e2e8f0;font-size:1.2em;">🏆 模拟冠军（单次模拟）</p>
</div>
""", unsafe_allow_html=True)

# ── 对阵结构说明 ──────────────────────────────────
with st.expander("📋 2026 世界杯淘汰赛赛制说明"):
    st.markdown("""
    **2026 世界杯淘汰赛共 32 支球队参加：**
    - 12 个小组第一（自动晋级）
    - 12 个小组第二（自动晋级）
    - 8 个成绩最好的小组第三（按积分、净胜球、进球数排名）

    **赛制：**
    - 1/16 决赛（16 场）→ 1/8 决赛（8 场）→ 1/4 决赛（4 场）→ 半决赛（2 场）→ 三四名决赛 + 决赛
    - 淘汰赛平局将进行加时赛（30 分钟），仍平则点球大战

    **对阵规则：**
    - 小组第一 vs 小组第三/第二（避免同组球队在同半区相遇）
    - 具体对阵由 FIFA 官方抽签确定
    """)

    bracket_data = []
    for slot_id, desc, source in BRACKET_SLOTS:
        desc_cn = (desc
                   .replace("Winner Group ", "小组第一 ")
                   .replace("Runner-up Group ", "小组第二 ")
                   .replace("Best 3rd Place ", "最佳第三 "))
        bracket_data.append({"签位": slot_id, "说明": desc_cn, "来源": source})
    st.dataframe(pd.DataFrame(bracket_data), hide_index=True, use_container_width=True)
