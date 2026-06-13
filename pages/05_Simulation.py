"""
🎲 赛事模拟 — 蒙特卡洛全赛事模拟
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from src.data.shared import load_schedule_data
from src.models.predictor import MatchPredictor
from src.models.monte_carlo import TournamentSimulator
from src.utils.viz_helpers import (
    create_champion_bar_chart, create_confederation_pie,
    create_stage_reach_chart,
)
from src.utils.config import TEAMS

# ── 初始化 ────────────────────────────────────────
st.set_page_config(page_title="赛事模拟", page_icon="🎲", layout="wide")

data = load_schedule_data()

@st.cache_resource
def init_predictor():
    pred = MatchPredictor()
    if not data["historical"].empty:
        pred.load_historical_data(data["historical"])
    return pred

predictor = init_predictor()

# ── 界面 ──────────────────────────────────────────
st.title("🎲 蒙特卡洛赛事模拟")
st.markdown("通过成千上万次模拟整个赛事，估算每支球队的夺冠概率和各阶段晋级概率。")

# ── 控制面板 ──────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    n_sim = st.select_slider(
        "模拟次数",
        options=[100, 500, 1000, 2000, 5000, 10000],
        value=1000,
        help="模拟次数越多，概率越精确，但耗时更长。",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 开始模拟", type="primary", use_container_width=True)
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"约 {n_sim * 104:,} 场比赛模拟")

# ── 执行模拟 ──────────────────────────────────────
if run_btn:
    with st.spinner(f"正在运行 {n_sim:,} 次赛事模拟..."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(i, total):
            progress_bar.progress(i / total)
            if i % 500 == 0:
                status_text.text(f"已完成 {i:,}/{total:,} 次模拟...")

        simulator = TournamentSimulator(predictor)
        start_time = datetime.now()
        results = simulator.run(n_simulations=n_sim, progress_callback=progress_callback)
        elapsed = (datetime.now() - start_time).total_seconds()

        progress_bar.progress(1.0)
        status_text.text(f"✅ 完成 {n_sim:,} 次模拟，耗时 {elapsed:.1f} 秒")

    st.success(f"模拟完成！共 {n_sim:,} 次赛事模拟，耗时 {elapsed:.1f} 秒。")

    st.markdown("---")

    top_contenders = results["top_contenders"]
    if top_contenders:
        st.subheader("🏆 夺冠概率")

        col1, col2 = st.columns([2, 1])

        with col1:
            top_n = min(20, len(top_contenders))
            st.plotly_chart(
                create_champion_bar_chart(top_contenders[:top_n], "夺冠概率排行"),
                use_container_width=True,
            )

        with col2:
            team_conf = {name: info["confederation"] for name, info in TEAMS.items()}
            st.plotly_chart(
                create_confederation_pie(
                    {team: prob for team, prob in top_contenders}, team_conf
                ),
                use_container_width=True,
            )

        # ── 完整概率表 ──────────────────────────────
        st.subheader("📊 完整夺冠概率表")

        all_probs = sorted(
            [(team, results["champion"].get(team, 0)) for team in TEAMS],
            key=lambda x: x[1], reverse=True,
        )

        table_data = []
        for i, (team, prob) in enumerate(all_probs):
            flag = TEAMS.get(team, {}).get("flag", "")
            conf = TEAMS.get(team, {}).get("confederation", "")
            elo = predictor.get_team_elo(team)
            table_data.append({
                "排名": i + 1,
                "球队": f"{flag} {team}",
                "Elo": f"{elo:.0f}",
                "联合会": conf,
                "🏆 夺冠": f"{prob:.2%}",
                "🥈 决赛": f"{results['final'].get(team, 0):.2%}",
                "🥉 四强": f"{results['semifinal'].get(team, 0):.2%}",
                "八强": f"{results['quarterfinal'].get(team, 0):.2%}",
            })

        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
            column_config={
                "排名": st.column_config.NumberColumn("排名"),
                "球队": st.column_config.TextColumn("球队", width="large"),
                "🏆 夺冠": st.column_config.TextColumn("🏆 夺冠"),
                "🥈 决赛": st.column_config.TextColumn("🥈 决赛"),
                "🥉 四强": st.column_config.TextColumn("🥉 四强"),
            },
        )

        # ── 阶段晋级图 ──────────────────────────────
        st.markdown("---")
        st.subheader("📈 各阶段晋级概率（热门球队）")

        stage_probs = {}
        for team, _ in top_contenders[:12]:
            stage_probs[team] = {
                "16强": results["r16"].get(team, 0),
                "8强": results["quarterfinal"].get(team, 0),
                "4强": results["semifinal"].get(team, 0),
                "决赛": results["final"].get(team, 0),
                "champion": results["champion"].get(team, 0),
            }

        st.plotly_chart(
            create_stage_reach_chart(stage_probs, top_n=12),
            use_container_width=True,
        )

        # ── 统计摘要 ────────────────────────────────
        st.markdown("---")
        st.subheader("📈 模拟统计")
        stat_cols = st.columns(4)
        with stat_cols[0]:
            st.metric("总模拟次数", f"{n_sim:,}")
        with stat_cols[1]:
            st.metric("不同冠军数", f"{len([t for t, p in all_probs if p > 0])}")
        with stat_cols[2]:
            top_team = top_contenders[0][0] if top_contenders else "无"
            top_prob = top_contenders[0][1] if top_contenders else 0
            st.metric("最大热门", f"{TEAMS.get(top_team, {}).get('flag', '')} {top_team}",
                     delta=f"{top_prob:.2%}")
        with stat_cols[3]:
            st.metric("计算耗时", f"{elapsed:.1f} 秒")

    else:
        st.warning("未生成结果，请尝试增加模拟次数。")

else:
    # ── 说明 ──────────────────────────────────────
    st.info("👆 点击 **开始模拟** 按钮运行蒙特卡洛赛事模拟。")

    st.markdown("""
    ### 模拟原理

    1. **蒙特卡洛方法**：每次模拟完整进行 104 场比赛
    2. **小组赛**：循环赛制，每组前2名 + 8个最佳第三名晋级
    3. **淘汰赛**：1/16决赛 → 1/8决赛 → 1/4决赛 → 半决赛 → 决赛
    4. **比赛模拟**：基于球队 Elo 评级的泊松分布随机抽取进球数
    5. **结果汇总**：数千次模拟后，统计每队夺冠次数 ÷ 总次数 = 夺冠概率

    ### Elo 评级参考

    - **2100+**：顶级强队（阿根廷、法国、巴西等）
    - **1900-2100**：有力竞争者（西班牙、英格兰、葡萄牙等）
    - **1700-1900**：稳定的国际级球队
    - **1500-1700**：发展中球队
    - **< 1500**：弱队
    """)

# ── 导出 ──────────────────────────────────────────
with st.expander("💾 导出数据"):
    st.caption("运行模拟后，可在此导出结果。")
    if run_btn and top_contenders:
        csv_data = pd.DataFrame([
            {"球队": team, "夺冠概率": prob}
            for team, prob in sorted(
                [(t, results["champion"].get(t, 0)) for t in TEAMS],
                key=lambda x: x[1], reverse=True,
            )
        ])
        st.download_button(
            "📥 下载夺冠概率 (CSV)",
            csv_data.to_csv(index=False),
            f"世界杯2026_模拟{n_sim}次_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv",
        )
