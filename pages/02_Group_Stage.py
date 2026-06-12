"""
🏟️ 小组赛 — 查看小组积分、赛程预测和晋级概率
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from src.data.loader import load_all
from src.models.predictor import MatchPredictor
from src.models.monte_carlo import TournamentSimulator
from src.utils.config import GROUPS, TEAMS

# ── 初始化 ────────────────────────────────────────
st.set_page_config(page_title="小组赛分析", page_icon="🏟️", layout="wide")

@st.cache_resource
def get_engine():
    data = load_all()
    predictor = MatchPredictor()
    if not data["historical"].empty:
        predictor.load_historical_data(data["historical"])
    return predictor, data

predictor, data = get_engine()

# ── 界面 ──────────────────────────────────────────
st.title("🏟️ 小组赛分析")
st.markdown("逐组查看积分榜预测、晋级概率和赛程分析。")

all_groups = list(GROUPS.keys())
selected_group = st.selectbox("选择小组", all_groups)

st.markdown("---")

# ── 小组详情 ─────────────────────────────────────
teams = GROUPS[selected_group]
team_flags = {t: TEAMS.get(t, {}).get("flag", "") for t in teams}

st.subheader(f"{selected_group} 组")
flag_str = "  ".join([f"{team_flags[t]} **{t}**" for t in teams])
st.markdown(flag_str)

# 模拟小组晋级概率（通过完整锦标赛模拟获取准确的第三名晋级率）
@st.cache_data(ttl=300)
def simulate_group_advancement(group: str, _predictor):
    sim = TournamentSimulator(_predictor)
    team_set = set(GROUPS[group])
    advances = {t: 0 for t in GROUPS[group]}
    third_advances = {t: 0 for t in GROUPS[group]}
    third_actually_qualified = {t: 0 for t in GROUPS[group]}

    n = 2000
    for _ in range(n):
        result = sim.simulate_tournament()
        standings = result["group_standings"][group]
        # 晋级32强的球队集合（通过淘汰赛阶段判断）
        r32_teams = set()
        for m in result["stage_results"].get("R32", []):
            r32_teams.add(m["home"])
            r32_teams.add(m["away"])

        for s in standings[:2]:
            advances[s.team] += 1
        if len(standings) >= 3:
            third_team = standings[2].team
            third_advances[third_team] += 1
            if third_team in r32_teams:
                third_actually_qualified[third_team] += 1

    return {
        t: {
            "top2": advances[t] / n,
            "third": third_advances[t] / n,
            "combined": (advances[t] + third_actually_qualified[t]) / n,
        }
        for t in GROUPS[group]
    }

advance_probs = simulate_group_advancement(selected_group, predictor)

# 晋级概率
st.markdown("### 晋级概率")
adv_cols = st.columns(len(teams))
for i, team in enumerate(teams):
    with adv_cols[i]:
        prob = advance_probs.get(team, {}).get("combined", 0)
        st.metric(
            f"{team_flags[team]} {team}",
            f"{prob:.1%}",
            delta="晋级32强",
        )
        st.progress(prob)

# 预测积分榜
st.markdown("### 预测积分榜")

simulator = TournamentSimulator(predictor)
standings = simulator.simulate_group(selected_group)

table_data = []
for s in standings:
    table_data.append({
        "球队": f"{team_flags.get(s.team, '')} {s.team}",
        "场次": s.played,
        "胜": s.wins,
        "平": s.draws,
        "负": s.losses,
        "进球": s.goals_for,
        "失球": s.goals_against,
        "净胜": s.goal_diff,
        "积分": s.points,
        "晋级概率": f"{advance_probs.get(s.team, {}).get('combined', 0):.1%}",
    })

st.dataframe(
    pd.DataFrame(table_data),
    use_container_width=True,
    hide_index=True,
    column_config={
        "球队": st.column_config.TextColumn("球队", width="large"),
        "积分": st.column_config.NumberColumn("积分", format="%d"),
        "净胜": st.column_config.NumberColumn("净胜", format="%+d"),
        "晋级概率": st.column_config.TextColumn("晋级32强概率"),
    },
)

# 小组赛程
st.markdown("### 小组赛程")

schedule = data["schedule"]
group_matches = schedule[
    (schedule["group"] == selected_group) &
    (schedule["home_team"] != "TBD")
]

if not group_matches.empty:
    for _, match in group_matches.iterrows():
        home = match["home_team"]
        away = match["away_team"]
        match_date = match["match_date"]

        try:
            pred = predictor.predict(home, away, neutral=True)
        except Exception:
            pred = None

        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            date_str = match_date.strftime("%m月%d日") if hasattr(match_date, "strftime") else str(match_date)
            st.markdown(f"**{date_str}**")
        with col2:
            hf = team_flags.get(home, "")
            af = team_flags.get(away, "")
            if pred:
                st.markdown(
                    f"{hf} **{home}** {pred['expected_home_goals']:.1f} — "
                    f"{pred['expected_away_goals']:.1f} **{away}** {af}"
                )
        with col3:
            if pred:
                st.markdown(
                    f"主胜: {pred['home_win']:.0%} | 平: {pred['draw']:.0%} | 客胜: {pred['away_win']:.0%}"
                )
else:
    st.info(f"{selected_group} 组暂无赛程数据。")
