"""
⚽ 比赛预测 — 预测胜率、进球数和比分概率
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np

from src.data.shared import load_schedule_data
from src.models.predictor import MatchPredictor
from src.utils.viz_helpers import create_win_prob_gauge, create_scoreline_heatmap, create_expected_goals_chart
from src.utils.config import TEAMS, GROUPS

# ── 初始化 ────────────────────────────────────────
st.set_page_config(page_title="比赛预测", page_icon="⚽", layout="wide")

data = load_schedule_data()

@st.cache_resource
def init_predictor():
    pred = MatchPredictor()
    if not data["historical"].empty:
        pred.load_historical_data(data["historical"])
    return pred

predictor = init_predictor()
# 只显示2026世界杯48支参赛队伍
wc_teams = set()
for teams in GROUPS.values():
    wc_teams.update(teams)
all_teams = sorted(list(wc_teams))

# ── 界面 ──────────────────────────────────────────
st.title("⚽ 比赛预测")
st.markdown("选择两支球队，预测比赛胜率、预期进球和比分概率。")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    search_home = st.text_input("🔍 搜索主队", placeholder="输入队名，如 Bosnia、波黑...", key="search_home")
    if search_home:
        home_filtered = [t for t in all_teams
                         if search_home.lower() in t.lower()
                         or search_home in TEAMS.get(t, {}).get("flag", "")]
    else:
        home_filtered = all_teams
    home_team = st.selectbox("主队", home_filtered,
                             index=home_filtered.index("Argentina") if "Argentina" in home_filtered else 0,
                             format_func=lambda t: f"{TEAMS.get(t, {}).get('flag', '')} {t}")
with col2:
    search_away = st.text_input("🔍 搜索客队", placeholder="输入队名，如 Brazil、巴西...", key="search_away")
    if search_away:
        away_filtered = [t for t in all_teams
                         if search_away.lower() in t.lower()
                         or search_away in TEAMS.get(t, {}).get("flag", "")]
    else:
        away_filtered = all_teams
    default_away = "Brazil" if home_team != "Brazil" else "France"
    away_team = st.selectbox("客队", away_filtered,
                             index=away_filtered.index(default_away) if default_away in away_filtered else 0,
                             format_func=lambda t: f"{TEAMS.get(t, {}).get('flag', '')} {t}")
with col3:
    neutral = st.checkbox("中立场地", value=True)
    st.markdown("<br>", unsafe_allow_html=True)
    predict_btn = st.button("🔮 开始预测", type="primary", use_container_width=True)

if home_team == away_team:
    st.warning("请选择两支不同的球队。")
else:
    # 仅在点击按钮时运行预测，结果存入 session_state 以跨 rerun 保持
    pred_key = f"pred_{home_team}_{away_team}_{neutral}"
    if predict_btn:
        st.session_state[pred_key] = predictor.predict(home_team, away_team, neutral=neutral)
    pred = st.session_state.get(pred_key)
    if pred is None:
        st.info("点击「开始预测」按钮查看预测结果。")
        st.stop()

    st.markdown("---")

    # ── 第一行：概率 + 预期进球 ────────────────
    row1_col1, row1_col2 = st.columns([1, 1])

    with row1_col1:
        st.subheader("比赛结果概率")
        st.plotly_chart(
            create_win_prob_gauge(
                pred["home_win"], pred["draw"], pred["away_win"],
                home_team, away_team
            ),
            use_container_width=True,
        )

        pcol1, pcol2, pcol3 = st.columns(3)
        pcol1.metric(f"{TEAMS.get(home_team, {}).get('flag', '')} {home_team} 胜", f"{pred['home_win']:.1%}")
        pcol2.metric("🤝 平局", f"{pred['draw']:.1%}")
        pcol3.metric(f"{TEAMS.get(away_team, {}).get('flag', '')} {away_team} 胜", f"{pred['away_win']:.1%}")

    with row1_col2:
        st.subheader("预期进球数")
        st.plotly_chart(
            create_expected_goals_chart(
                home_team, away_team,
                pred["expected_home_goals"], pred["expected_away_goals"]
            ),
            use_container_width=True,
        )

    st.markdown("---")

    # ── 比分热力图 ──────────────────────────────
    st.subheader(f"🎯 比分概率矩阵")
    st.markdown(f"最可能比分：**{pred['most_likely_score']}**（概率 {pred['most_likely_prob']:.1%}）")

    st.plotly_chart(
        create_scoreline_heatmap(
            pred["scoreline_matrix"], home_team, away_team
        ),
        use_container_width=True,
    )

    # ── 市场数据 ────────────────────────────────
    st.subheader("📊 进球市场概率")
    market_col1, market_col2, market_col3, market_col4 = st.columns(4)

    with market_col1:
        st.metric("总进球 > 2.5", f"{pred['over_2_5']:.1%}")
    with market_col2:
        st.metric("总进球 < 2.5", f"{pred['under_2_5']:.1%}")
    with market_col3:
        st.metric("双方都进球", f"{pred['btts_yes']:.1%}")
    with market_col4:
        st.metric("至少一方零封", f"{pred['btts_no']:.1%}")

    # ── Elo 对比 ────────────────────────────────
    st.markdown("---")
    st.subheader("📈 球队实力对比")
    elo_col1, elo_col2 = st.columns(2)
    with elo_col1:
        st.metric(
            f"{TEAMS.get(home_team, {}).get('flag', '')} {home_team} Elo",
            f"{pred['elo_home']:.0f}",
            delta=f"{pred['elo_diff']:+.0f}" if pred['elo_diff'] > 0 else None,
        )
    with elo_col2:
        st.metric(
            f"{TEAMS.get(away_team, {}).get('flag', '')} {away_team} Elo",
            f"{pred['elo_away']:.0f}",
            delta=f"{-pred['elo_diff']:+.0f}" if pred['elo_diff'] < 0 else None,
        )

    max_elo = max(pred["elo_home"], pred["elo_away"])
    min_elo = min(pred["elo_home"], pred["elo_away"])
    st.progress(
        (pred["elo_home"] - min_elo) / max(1, max_elo - min_elo),
        text=f"Elo 差距：{abs(pred['elo_diff']):.0f} 分（{'偏向 ' + home_team if pred['elo_diff'] > 0 else '偏向 ' + away_team if pred['elo_diff'] < 0 else '势均力敌'}）"
    )
