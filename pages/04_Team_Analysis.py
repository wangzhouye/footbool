"""
📈 球队分析 — Elo历史、雷达图、近期状态、球队对比
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from src.data.shared import load_schedule_data
from src.data.preprocessor import compute_team_form
from src.models.predictor import MatchPredictor
from src.models.monte_carlo import TournamentSimulator
from src.utils.viz_helpers import create_radar_chart, create_elo_history_chart
from src.utils.config import TEAMS, GROUPS

# ── 初始化 ────────────────────────────────────────
st.set_page_config(page_title="球队分析", page_icon="📈", layout="wide")

data = load_schedule_data()

@st.cache_resource
def init_predictor():
    pred = MatchPredictor()
    if not data["historical"].empty:
        pred.load_historical_data(data["historical"])
    return pred

predictor = init_predictor()
historical = data["historical"]
all_teams = sorted(list(TEAMS.keys()))

# ── 界面 ──────────────────────────────────────────
st.title("📈 球队深度分析")
st.markdown("深入了解球队实力、近期状态和赛事前景。")

col1, col2 = st.columns([1, 1])
with col1:
    team = st.selectbox("选择球队", all_teams,
                        index=all_teams.index("Argentina") if "Argentina" in all_teams else 0,
                        format_func=lambda t: f"{TEAMS.get(t, {}).get('flag', '')} {t}")
with col2:
    compare_mode = st.checkbox("对比另一支球队")
    if compare_mode:
        compare_team = st.selectbox("对比球队", [t for t in all_teams if t != team],
                                    index=all_teams.index("Brazil") if "Brazil" in all_teams and team != "Brazil" else 0,
                                    format_func=lambda t: f"{TEAMS.get(t, {}).get('flag', '')} {t}")
    else:
        compare_team = None

st.markdown("---")

# ── 球队概览 ─────────────────────────────────────
team_info = TEAMS.get(team, {})
team_elo = predictor.get_team_elo(team)
flag = team_info.get("flag", "")
group = None
for g, teams in GROUPS.items():
    if team in teams:
        group = g
        break

st.subheader(f"{flag} {team}")
overview_cols = st.columns(4)
with overview_cols[0]:
    st.metric("Elo 评级", f"{team_elo:.0f}")
with overview_cols[1]:
    st.metric("所在小组", f"{group} 组" if group else "无")
with overview_cols[2]:
    conf_cn = {
        "UEFA": "欧洲", "CONMEBOL": "南美", "CONCACAF": "中北美",
        "CAF": "非洲", "AFC": "亚洲", "OFC": "大洋洲"
    }
    st.metric("所属联合会", conf_cn.get(team_info.get("confederation", ""), "未知"))
with overview_cols[3]:
    all_elos = predictor.get_all_elos()
    rank = sum(1 for r in all_elos.values() if r > team_elo) + 1
    st.metric("Elo 排名", f"#{rank}/48")

st.markdown("---")

# ── 雷达图 ───────────────────────────────────────
st.subheader("🎯 球队实力雷达图")

def compute_team_stats(t):
    elo_val = predictor.get_team_elo(t)
    avg_elo = predictor.elo.get_avg_rating()
    form = compute_team_form(historical, t) if not historical.empty else {}

    elo_percentile = min(100, max(0, (elo_val - 1300) / 900 * 100))
    attack = min(100, max(0, 50 + (form.get("avg_goals_for", 1.5) - 1.5) * 40))
    defense = min(100, max(0, 50 - (form.get("avg_goals_against", 1.1) - 1.1) * 40))
    experience = min(100, max(0, 50 + (elo_val - avg_elo) / 8))
    form_score = min(100, max(0, 50 + form.get("elo_form_boost", 0) * 2))
    path_difficulty = min(100, max(0, 40 + (elo_val - avg_elo) / 15))

    return {
        "进攻": round(attack, 0),
        "防守": round(defense, 0),
        "经验": round(experience, 0),
        "近期状态": round(form_score, 0),
        "赛程难度": round(path_difficulty, 0),
    }

team_stats = compute_team_stats(team)
compare_stats = compute_team_stats(compare_team) if compare_team else None

st.plotly_chart(
    create_radar_chart(team, team_stats, compare_team, compare_stats),
    use_container_width=True,
)

# ── Elo 走势 ─────────────────────────────────────
st.subheader("📊 Elo 评分走势")

@st.cache_data(ttl=600)
def build_elo_history(hist_df, team_name):
    if hist_df.empty:
        return []

    from src.models.elo import EloEngine
    elo_tracker = EloEngine()
    history = []

    for _, row in hist_df.sort_values("date").iterrows():
        home = row["home_team"]
        away = row["away_team"]
        tournament = row.get("tournament", "Friendly")
        neutral = row.get("neutral", True)
        if isinstance(neutral, str):
            neutral = neutral.lower() == "true"

        elo_tracker.update(home, away, int(row["home_score"]), int(row["away_score"]),
                          tournament=tournament, neutral=neutral)

        if home == team_name or away == team_name:
            history.append({
                "date": row["date"],
                "rating": elo_tracker.get_rating(team_name),
            })

    return history

if not historical.empty:
    elo_history = build_elo_history(historical, team)
    if elo_history:
        st.plotly_chart(create_elo_history_chart(team, elo_history), use_container_width=True)

        if compare_team:
            compare_history = build_elo_history(historical, compare_team)
            if compare_history:
                import plotly.graph_objects as go
                fig = create_elo_history_chart(team, elo_history)
                fig.add_trace(go.Scatter(
                    x=[e["date"] for e in compare_history],
                    y=[e["rating"] for e in compare_history],
                    mode='lines+markers',
                    name=compare_team,
                    line=dict(color='#ef4444', width=2, dash='dash'),
                    marker=dict(size=3),
                ))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无该球队的历史数据。")
else:
    st.info("未加载历史比赛数据。")

# ── 近期状态 ─────────────────────────────────────
st.subheader("📋 近期比赛状态")

if not historical.empty:
    form = compute_team_form(historical, team)

    if form["recent_results"]:
        form_data = []
        for r in form["recent_results"]:
            opp_flag = TEAMS.get(r["opponent"], {}).get("flag", "")
            result_cn = {"W": "胜", "D": "平", "L": "负"}.get(r["result"], r["result"])
            form_data.append({
                "日期": r["date"],
                "对手": f"{opp_flag} {r['opponent']}",
                "比分": r["score"],
                "结果": result_cn,
                "权重": f"{r['weight']:.2f}",
            })

        form_df = pd.DataFrame(form_data)

        def color_result(val):
            if val == "胜":
                return "background-color: #166534; color: #22c55e"
            elif val == "平":
                return "background-color: #475569; color: #94a3b8"
            elif val == "负":
                return "background-color: #7f1d1d; color: #ef4444"
            return ""

        st.dataframe(
            form_df.style.map(color_result, subset=["结果"]),
            use_container_width=True,
            hide_index=True,
        )

        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            st.metric("场均进球（加权）", f"{form['avg_goals_for']:.2f}")
        with fcol2:
            st.metric("场均失球（加权）", f"{form['avg_goals_against']:.2f}")
        with fcol3:
            st.metric("状态 Elo 加成", f"{form['elo_form_boost']:+.1f}")
    else:
        st.info("未找到该球队的近期比赛。")

# ── 赛事前景 ─────────────────────────────────────
st.subheader("🎲 赛事前景模拟")

if st.button("🚀 快速模拟（2000次）"):
    with st.spinner(f"正在进行 2000 次赛事模拟..."):
        sim = TournamentSimulator(predictor)
        results = sim.run(n_simulations=2000)
        path = results["champion"].get(team, 0)

        st.metric("夺冠概率", f"{path:.2%}")

        stages = {
            "1/16决赛": results["r32"].get(team, 0),
            "1/8决赛": results["r16"].get(team, 0),
            "1/4决赛": results["quarterfinal"].get(team, 0),
            "半决赛": results["semifinal"].get(team, 0),
            "决赛": results["final"].get(team, 0),
            "夺冠": results["champion"].get(team, 0),
        }

        import plotly.graph_objects as go
        fig = go.Figure(go.Funnel(
            y=list(stages.keys()),
            x=[v * 100 for v in stages.values()],
            text=[f"{v:.2%}" for v in stages.values()],
            textposition="inside",
            marker=dict(color=['#64748b', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#fbbf24']),
        ))
        fig.update_layout(
            title=f"{team} — 各阶段晋级概率",
            margin=dict(l=20, r=20, t=40, b=10),
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
        )
        st.plotly_chart(fig, use_container_width=True)
