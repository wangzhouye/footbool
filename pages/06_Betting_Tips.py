"""
💰 投注价值分析 — 结合模型预测与竞彩赔率，筛选正期望值投注选项

功能：
- 自动扫描所有比赛，计算期望值 (EV)
- 支持胜平负、让球、大小球等多种玩法
- 按 EV 排序，推荐最有价值的投注选项
- 提供详细的概率对比和置信度评估
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime, date

from src.data.loader import load_all
from src.models.predictor import MatchPredictor
from src.models.value_analyzer import (
    scan_all_matches, analyze_match_value, get_summary_stats,
    calculate_ev, calculate_kelly
)
from src.data.sporttery_scraper import SportteryScraper, odds_to_win_probability
from src.utils.viz_helpers import (
    create_ev_comparison_chart, create_ev_heatmap, create_opportunity_bar_chart
)
from src.utils.config import TEAMS, GROUPS

# ── 页面设置 ────────────────────────────────────────
st.set_page_config(page_title="投注价值分析", page_icon="💰", layout="wide")

# ── 样式 ───────────────────────────────────────────
st.markdown("""
<style>
.main .block-container { padding-top: 2rem; }
.stMetric { background-color: #1e293b; padding: 1rem; border-radius: 0.5rem; }
.stMetric label { color: #94a3b8 !important; }
h1 { color: #fbbf24 !important; }
h2, h3 { color: #e2e8f0 !important; }
.value-high { color: #22c55e; font-weight: bold; }
.value-medium { color: #fbbf24; font-weight: bold; }
.value-low { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)


# ── 初始化 ────────────────────────────────────────
@st.cache_resource
def init():
    data = load_all()
    pred = MatchPredictor()
    if not data["historical"].empty:
        pred.load_historical_data(data["historical"])
    return pred, data


predictor, data = init()


@st.cache_data(ttl=120)
def fetch_odds():
    try:
        return SportteryScraper().get_world_cup_odds()
    except Exception:
        return []


odds_list = fetch_odds()


# ── 侧边栏 ─────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/money-bag--v1.png", width=64)
    st.title("💰 投注价值分析")

    if odds_list:
        st.markdown(f"🟢 **赔率数据已连接** — {len(odds_list)} 场比赛")
    else:
        st.markdown("🔴 赔率数据未连接")

    st.markdown("---")

    # 筛选选项
    st.subheader("📊 筛选选项")

    min_ev = st.slider(
        "最低 EV 阈值",
        min_value=0.0,
        max_value=0.15,
        value=0.02,
        step=0.01,
        format="%.2f",
        help="只显示 EV 大于此值的投注选项"
    )

    markets = st.multiselect(
        "玩法选择",
        options=["HAD", "HHAD", "TTG"],
        default=["HAD", "HHAD"],
        format_func=lambda x: {
            "HAD": "胜平负",
            "HHAD": "让球胜平负",
            "TTG": "大小球"
        }.get(x, x),
        help="选择要分析的投注市场"
    )

    top_n = st.selectbox(
        "显示数量",
        options=[10, 20, 50, 100],
        index=1,
        help="显示前 N 个最佳投注机会"
    )

    sort_by = st.selectbox(
        "排序方式",
        options=["ev", "kelly", "confidence"],
        index=0,
        format_func=lambda x: {
            "ev": "期望值 (EV)",
            "kelly": "Kelly 系数",
            "confidence": "置信度"
        }.get(x, x),
    )

    st.markdown("---")
    st.caption(f"🔄 每120秒自动刷新 | {datetime.now().strftime('%H:%M:%S')}")


# ── 主页面 ──────────────────────────────────────────
st.title("💰 投注价值分析")
st.markdown("结合模型预测与竞彩赔率，筛选正期望值投注选项。**正 EV 表示模型认为实际概率高于市场隐含概率。**")

# ── 数据处理 ─────────────────────────────────────────
if not odds_list:
    st.warning("⚠️ 无法获取赔率数据，请检查网络连接或稍后重试。")
    st.stop()

# 扫描所有比赛
with st.spinner("正在分析所有比赛的投注价值..."):
    opportunities = scan_all_matches(
        odds_list, predictor,
        min_ev=min_ev,
        markets=markets
    )

# 排序
if sort_by == "ev":
    opportunities.sort(key=lambda x: x.get("ev", 0) or 0, reverse=True)
elif sort_by == "kelly":
    opportunities.sort(key=lambda x: x.get("kelly", 0) or 0, reverse=True)
elif sort_by == "confidence":
    conf_order = {"high": 0, "medium": 1, "low": 2, "model_only": 3}
    opportunities.sort(key=lambda x: conf_order.get(x.get("confidence", "low"), 3))

# 限制显示数量
display_opps = opportunities[:top_n]

# ── 概览统计 ─────────────────────────────────────────
st.markdown("---")
st.subheader("📊 概览统计")

stats = get_summary_stats(opportunities)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("正 EV 选项", f"{stats['positive_ev_count']} 个")
with col2:
    st.metric("平均 EV", f"{stats['avg_ev']*100:+.2f}%")
with col3:
    st.metric("最高 EV", f"{stats['max_ev']*100:+.2f}%")
with col4:
    st.metric("高置信度", f"{stats['high_confidence']} 个")

# ── 最佳投注推荐 ─────────────────────────────────────
st.markdown("---")
st.subheader("🏆 最佳投注推荐")

if not display_opps:
    st.info("暂无符合条件的投注机会。请尝试调整筛选条件。")
else:
    # EV 条形图
    st.plotly_chart(
        create_opportunity_bar_chart(display_opps, top_n=15),
        use_container_width=True
    )

    # 详细表格
    st.markdown("### 📋 详细投注机会")

    # 准备表格数据
    table_data = []
    for opp in display_opps:
        # 置信度颜色
        conf = opp.get("confidence", "low")
        conf_display = {
            "high": "🟢 高",
            "medium": "🟡 中",
            "low": "⚪ 低",
            "model_only": "🔵 模型"
        }.get(conf, conf)

        # EV 颜色
        ev = opp.get("ev")
        ev_display = f"{ev*100:+.2f}%" if ev is not None else "N/A"

        # 赔率显示
        odds = opp.get("odds")
        odds_display = f"{odds:.2f}" if odds is not None else "N/A"

        # Kelly 显示
        kelly = opp.get("kelly")
        kelly_display = f"{kelly*100:.1f}%" if kelly is not None else "N/A"

        table_data.append({
            "比赛": opp["match_label"],
            "日期": opp.get("date", ""),
            "时间": opp.get("match_time", ""),
            "玩法": opp.get("market_cn", ""),
            "选项": opp.get("selection", ""),
            "模型概率": f"{opp.get('model_prob', 0)*100:.1f}%",
            "赔率": odds_display,
            "EV": ev_display,
            "Kelly": kelly_display,
            "置信度": conf_display,
        })

    df = pd.DataFrame(table_data)

    # 样式化表格
    def highlight_ev(val):
        if isinstance(val, str) and val != "N/A":
            try:
                ev_float = float(val.replace('%', '').replace('+', ''))
                if ev_float > 5:
                    return 'color: #22c55e; font-weight: bold'
                elif ev_float > 0:
                    return 'color: #fbbf24'
                else:
                    return 'color: #ef4444'
            except:
                pass
        return ''

    styled_df = df.style.applymap(highlight_ev, subset=['EV'])
    st.dataframe(styled_df, hide_index=True, use_container_width=True)

# ── 详细分析 ─────────────────────────────────────────
st.markdown("---")
st.subheader("📈 详细分析")

if display_opps:
    # 选择比赛进行详细分析
    match_labels = list(set(opp["match_label"] for opp in display_opps))
    selected_match = st.selectbox(
        "选择比赛查看详细分析",
        options=match_labels,
        format_func=lambda x: x
    )

    if selected_match:
        # 获取该比赛的所有投注机会
        match_opps = [o for o in display_opps if o["match_label"] == selected_match]

        if match_opps:
            opp = match_opps[0]
            home_team = opp["home_team"]
            away_team = opp["away_team"]

            st.markdown(f"#### 🏟️ {home_team} vs {away_team}")

            # 获取模型预测
            try:
                prediction = predictor.predict(home_team, away_team, neutral=True)

                # 概率对比图
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("##### 胜平负概率对比")
                    model_probs = {
                        "home_win": prediction["home_win"],
                        "draw": prediction["draw"],
                        "away_win": prediction["away_win"]
                    }

                    # 从赔率获取市场概率
                    odds_match = None
                    for o in odds_list:
                        if o["home_team"] == home_team and o["away_team"] == away_team:
                            odds_match = o
                            break

                    if odds_match and odds_match.get("odds_had"):
                        had = odds_match["odds_had"]
                        market_probs = odds_to_win_probability(had["h"], had["d"], had["a"])
                    else:
                        market_probs = {"home_win": 0, "draw": 0, "away_win": 0}

                    fig = create_ev_comparison_chart(
                        f"{home_team} vs {away_team}",
                        model_probs,
                        market_probs,
                        [f"{home_team} 胜", "平局", f"{away_team} 胜"]
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("##### 预期进球")
                    xg_home = prediction["expected_home_goals"]
                    xg_away = prediction["expected_away_goals"]
                    total_xg = prediction["total_expected_goals"]

                    st.metric(f"{home_team} 预期进球", f"{xg_home:.2f}")
                    st.metric(f"{away_team} 预期进球", f"{xg_away:.2f}")
                    st.metric("总预期进球", f"{total_xg:.2f}")

                    # 大小球概率
                    st.markdown("##### 大小球概率")
                    st.metric("大 2.5", f"{prediction['over_2_5']*100:.1f}%")
                    st.metric("小 2.5", f"{prediction['under_2_5']*100:.1f}%")

                # 比分概率矩阵
                st.markdown("##### 🎯 比分概率矩阵")
                st.markdown(f"最可能比分：**{prediction['most_likely_score']}**（概率 {prediction['most_likely_prob']*100:.1f}%）")

                from src.utils.viz_helpers import create_scoreline_heatmap
                st.plotly_chart(
                    create_scoreline_heatmap(
                        prediction["scoreline_matrix"], home_team, away_team
                    ),
                    use_container_width=True
                )

                # 所有投注机会详情
                st.markdown("##### 💰 该比赛所有投注机会")
                for opp in match_opps:
                    ev = opp.get("ev")
                    ev_display = f"{ev*100:+.2f}%" if ev is not None else "N/A"

                    with st.expander(f"{opp['market_cn']} - {opp['selection']} (EV: {ev_display})"):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("模型概率", f"{opp.get('model_prob', 0)*100:.1f}%")
                        with col_b:
                            odds = opp.get("odds")
                            st.metric("赔率", f"{odds:.2f}" if odds else "N/A")
                        with col_c:
                            st.metric("EV", ev_display)

                        # Kelly 建议
                        kelly = opp.get("kelly")
                        if kelly:
                            st.markdown(f"**Kelly 建议投注比例：** {kelly*100:.1f}%")

                        # 置信度说明
                        conf = opp.get("confidence", "low")
                        conf_explain = {
                            "high": "✅ 高置信度：EV ≥ 10% 且模型概率 ≥ 30%",
                            "medium": "⚠️ 中置信度：EV ≥ 5% 且模型概率 ≥ 20%",
                            "low": "ℹ️ 低置信度：EV 或模型概率较低",
                            "model_only": "🔵 仅模型推荐：无市场赔率对比"
                        }.get(conf, "")
                        st.markdown(conf_explain)

            except Exception as e:
                st.error(f"获取预测数据时出错：{e}")

# ── EV 热力图 ─────────────────────────────────────────
st.markdown("---")
st.subheader("🔥 EV 热力图")

if display_opps and len(display_opps) > 1:
    # 只显示有 EV 的机会
    ev_opps = [o for o in display_opps if o.get("ev") is not None]
    if ev_opps:
        st.plotly_chart(
            create_ev_heatmap(ev_opps[:30]),  # 限制数量避免图表过大
            use_container_width=True
        )
    else:
        st.info("暂无足够的数据生成热力图。")
else:
    st.info("需要更多投注机会才能生成热力图。")

# ── 风险提示 ─────────────────────────────────────────
st.markdown("---")
st.subheader("⚠️ 风险提示")

st.markdown("""
<div style="background:#1e293b;padding:1.5rem;border-radius:0.5rem;border-left:4px solid #ef4444;">
    <h4 style="color:#ef4444;margin-top:0;">理性投注，量力而行</h4>
    <ul style="color:#94a3b8;">
        <li>本工具仅供参考，不构成任何投注建议</li>
        <li>模型预测基于历史数据，无法保证未来结果</li>
        <li>正 EV 不意味着一定盈利，存在方差和风险</li>
        <li>请根据自身经济状况理性投注，切勿沉迷</li>
        <li>未满18周岁禁止参与体育彩票</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# ── 页脚 ─────────────────────────────────────────────
st.markdown("---")
st.caption("⚽ 2026 世界杯投注价值分析 | 赔率：中国体育彩票竞彩网 | 预测仅供参考")
