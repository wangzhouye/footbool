"""
Shared Plotly chart builders for Streamlit pages.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Tuple


def create_win_prob_gauge(home_win: float, draw: float, away_win: float,
                          home_team: str, away_team: str) -> go.Figure:
    """Create a horizontal bar chart showing win/draw/loss probabilities."""
    labels = [f"{home_team} 胜", "平局", f"{away_team} 胜"]
    values = [home_win * 100, draw * 100, away_win * 100]
    colors = ["#22c55e", "#94a3b8", "#ef4444"]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition='outside',
        textfont=dict(size=16, color='#e2e8f0'),
        hovertemplate='%{x:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(range=[0, max(values) * 1.3], showticklabels=False, showgrid=False),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=40, t=10, b=10),
        height=180,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', size=14),
        showlegend=False,
    )
    return fig


def create_scoreline_heatmap(matrix: List[List[float]],
                              home_team: str, away_team: str) -> go.Figure:
    """Create annotated heatmap of scoreline probabilities."""
    n_rows = min(len(matrix), 8)
    n_cols = min(len(matrix[0]), 8)

    # Extract sub-matrix and convert to percentages
    data = np.array([row[:n_cols] for row in matrix[:n_rows]]) * 100

    fig = go.Figure(go.Heatmap(
        z=data,
        x=[str(i) for i in range(n_cols)],
        y=[str(i) for i in range(n_rows)],
        colorscale=[[0, '#0f172a'], [0.3, '#1e3a5f'], [0.6, '#e11d48'], [1, '#fbbf24']],
        text=[[f"{v:.1f}%" for v in row] for row in data],
        texttemplate="%{text}",
        textfont=dict(size=11, color='#e2e8f0'),
        hovertemplate=f'{home_team} %{{y}} - {away_team} %{{x}}<br>Probability: %{{z:.1f}}%<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(title=f"{away_team} Goals", side='bottom', tickfont=dict(color='#94a3b8')),
        yaxis=dict(title=f"{home_team} Goals", tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=10, b=40),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
    )
    return fig


def create_champion_bar_chart(top_teams: List[Tuple[str, float]],
                              title: str = "Championship Probability") -> go.Figure:
    """Horizontal bar chart of championship probabilities."""
    if not top_teams:
        return go.Figure()

    teams, probs = zip(*top_teams)
    probs_pct = [p * 100 for p in probs]

    # Color gradient from gold to bronze
    colors = ['#fbbf24'] * len(teams)

    fig = go.Figure(go.Bar(
        x=probs_pct,
        y=list(teams),
        orientation='h',
        marker_color=colors,
        text=[f"{p:.1f}%" for p in probs_pct],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='%{y}: %{x:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        title=title,
        xaxis=dict(title="Probability (%)", showgrid=True, gridcolor='#334155',
                    tickfont=dict(color='#94a3b8')),
        yaxis=dict(autorange="reversed", tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=60, t=40, b=20),
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
    )
    return fig


def create_radar_chart(team: str, stats: Dict[str, float], compare_team: str = None,
                       compare_stats: Dict[str, float] = None) -> go.Figure:
    """Create a radar/spider chart for team strength dimensions."""
    categories = list(stats.keys())
    values = list(stats.values())

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=team,
        line=dict(color='#3b82f6', width=2),
        fillcolor='rgba(59, 130, 246, 0.3)',
    ))

    if compare_team and compare_stats:
        fig.add_trace(go.Scatterpolar(
            r=list(compare_stats.values()),
            theta=categories,
            fill='toself',
            name=compare_team,
            line=dict(color='#ef4444', width=2),
            fillcolor='rgba(239, 68, 68, 0.3)',
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor='#334155'),
            angularaxis=dict(gridcolor='#334155', tickfont=dict(color='#94a3b8')),
            bgcolor='rgba(0,0,0,0)',
        ),
        margin=dict(l=40, r=40, t=40, b=40),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        showlegend=True,
        legend=dict(font=dict(color='#94a3b8')),
    )
    return fig


def create_elo_history_chart(team: str, elo_history: List[Dict]) -> go.Figure:
    """Line chart showing Elo rating history."""
    if not elo_history:
        return go.Figure()

    dates = [e["date"] for e in elo_history]
    ratings = [e["rating"] for e in elo_history]

    fig = go.Figure(go.Scatter(
        x=dates,
        y=ratings,
        mode='lines+markers',
        name=team,
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=4, color='#60a5fa'),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
        hovertemplate='%{x}<br>Elo: %{y:.0f}<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(title="Date", gridcolor='#334155', tickfont=dict(color='#94a3b8')),
        yaxis=dict(title="Elo Rating", gridcolor='#334155', tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=10, b=40),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
    )
    return fig


def create_confederation_pie(champion_probs: Dict[str, float],
                             team_confederation: Dict[str, str]) -> go.Figure:
    """Donut chart of championship probability by confederation."""
    confed_probs = {}
    for team, prob in champion_probs.items():
        conf = team_confederation.get(team, "Unknown")
        confed_probs[conf] = confed_probs.get(conf, 0) + prob

    confed_names = {
        "UEFA": "欧足联", "CONMEBOL": "南美足联", "CONCACAF": "中北美足联",
        "CAF": "非洲足联", "AFC": "亚足联", "OFC": "大洋洲足联",
    }
    labels = [confed_names.get(c, c) for c in confed_probs.keys()]
    values = [v * 100 for v in confed_probs.values()]

    confed_colors = {
        "UEFA": "#3b82f6",
        "CONMEBOL": "#22c55e",
        "CONCACAF": "#f59e0b",
        "CAF": "#ef4444",
        "AFC": "#8b5cf6",
        "OFC": "#06b6d4",
    }
    colors = [confed_colors.get(c, "#94a3b8") for c in confed_probs.keys()]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo='label+percent',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='%{label}: %{value:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=10),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
    )
    return fig


def create_expected_goals_chart(home: str, away: str, xg_home: float, xg_away: float) -> go.Figure:
    """预期进球对比柱状图"""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[f"{home}"],
        y=[xg_home],
        name=home,
        marker_color='#3b82f6',
        text=[f"{xg_home:.2f}"],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=18),
    ))

    fig.add_trace(go.Bar(
        x=[f"{away}"],
        y=[xg_away],
        name=away,
        marker_color='#ef4444',
        text=[f"{xg_away:.2f}"],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=18),
    ))

    fig.update_layout(
        yaxis=dict(title="预期进球", range=[0, max(xg_home, xg_away) * 1.5],
                    gridcolor='#334155', tickfont=dict(color='#94a3b8')),
        xaxis=dict(tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=10, b=20),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        showlegend=False,
    )
    return fig


def create_stage_reach_chart(stage_probs: Dict[str, Dict[str, float]],
                              top_n: int = 10) -> go.Figure:
    """Grouped bar chart showing probability of reaching each stage."""
    teams_sorted = sorted(stage_probs.keys(),
                          key=lambda t: stage_probs[t].get("champion", 0),
                          reverse=True)[:top_n]

    stages = ["16强", "8强", "4强", "决赛", "冠军"]
    colors_map = {"16强": "#64748b", "8强": "#3b82f6", "4强": "#22c55e",
                   "决赛": "#f59e0b", "冠军": "#ef4444"}

    fig = go.Figure()
    for stage in stages:
        key = "champion" if stage == "冠军" else stage
        probs = [stage_probs[t].get(key, 0) * 100
                 for t in teams_sorted]
        fig.add_trace(go.Bar(
            name=stage,
            x=teams_sorted,
            y=probs,
            marker_color=colors_map.get(stage, "#94a3b8"),
            hovertemplate='%{x}: %{y:.1f}%<extra></extra>',
        ))

    fig.update_layout(
        barmode='group',
        xaxis=dict(tickangle=-45, tickfont=dict(color='#94a3b8')),
        yaxis=dict(title="Probability (%)", gridcolor='#334155',
                    tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=10, b=60),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        legend=dict(font=dict(color='#94a3b8')),
    )
    return fig


def create_ev_comparison_chart(match_label: str,
                               model_probs: Dict[str, float],
                               market_probs: Dict[str, float],
                               selections: List[str]) -> go.Figure:
    """
    模型概率 vs 市场隐含概率对比条形图

    Args:
        match_label: 比赛标签
        model_probs: 模型概率字典 {"selection_key": prob}
        market_probs: 市场隐含概率字典 {"selection_key": prob}
        selections: 选项显示名称列表

    Returns:
        Plotly 图表对象
    """
    fig = go.Figure()

    selection_keys = list(model_probs.keys())
    selection_labels = selections[:len(selection_keys)]

    # 模型概率
    model_values = [model_probs.get(k, 0) * 100 for k in selection_keys]
    fig.add_trace(go.Bar(
        name='模型概率',
        x=selection_labels,
        y=model_values,
        marker_color='#3b82f6',
        text=[f"{v:.1f}%" for v in model_values],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
    ))

    # 市场隐含概率
    market_values = [market_probs.get(k, 0) * 100 for k in selection_keys]
    fig.add_trace(go.Bar(
        name='市场隐含',
        x=selection_labels,
        y=market_values,
        marker_color='#94a3b8',
        text=[f"{v:.1f}%" for v in market_values],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
    ))

    fig.update_layout(
        barmode='group',
        title=dict(text=match_label, font=dict(color='#fbbf24')),
        xaxis=dict(tickfont=dict(color='#94a3b8')),
        yaxis=dict(title="概率 (%)", gridcolor='#334155', tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        legend=dict(font=dict(color='#94a3b8')),
    )
    return fig


def create_ev_heatmap(opportunities: List[Dict]) -> go.Figure:
    """
    EV 热力图 — 比赛 × 市场类型

    Args:
        opportunities: 投注机会列表

    Returns:
        Plotly 图表对象
    """
    if not opportunities:
        return go.Figure()

    # 按比赛分组
    matches = {}
    for opp in opportunities:
        label = opp["match_label"]
        if label not in matches:
            matches[label] = {}
        market_key = f"{opp['market']}_{opp['selection']}"
        matches[label][market_key] = opp.get("ev", 0)

    # 收集所有市场类型
    all_markets = sorted(set(
        k for m in matches.values() for k in m.keys()
    ))

    # 构建矩阵
    match_labels = list(matches.keys())
    z_data = []
    text_data = []
    for label in match_labels:
        row = []
        text_row = []
        for market in all_markets:
            ev = matches[label].get(market, None)
            if ev is not None:
                row.append(ev * 100)  # 转为百分比
                text_row.append(f"{ev*100:+.1f}%")
            else:
                row.append(None)
                text_row.append("")
        z_data.append(row)
        text_data.append(text_row)

    fig = go.Figure(go.Heatmap(
        z=z_data,
        x=all_markets,
        y=match_labels,
        colorscale=[
            [0, '#ef4444'],      # 负 EV 红色
            [0.5, '#1e293b'],    # 零 EV 深色
            [1, '#22c55e']       # 正 EV 绿色
        ],
        zmid=0,
        text=text_data,
        texttemplate="%{text}",
        textfont=dict(size=10, color='#e2e8f0'),
        hovertemplate='%{y}<br>%{x}<br>EV: %{z:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(tickangle=-45, tickfont=dict(color='#94a3b8', size=9)),
        yaxis=dict(tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=10, b=80),
        height=max(300, len(match_labels) * 40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
    )
    return fig


def create_opportunity_bar_chart(opportunities: List[Dict], top_n: int = 15) -> go.Figure:
    """
    投注机会 EV 条形图

    Args:
        opportunities: 投注机会列表
        top_n: 显示前 N 个机会

    Returns:
        Plotly 图表对象
    """
    if not opportunities:
        return go.Figure()

    # 取前 N 个有 EV 的机会
    with_ev = [o for o in opportunities if o.get("ev") is not None][:top_n]
    if not with_ev:
        return go.Figure()

    labels = [f"{o['match_label']} ({o['selection']})" for o in with_ev]
    evs = [o["ev"] * 100 for o in with_ev]

    # 根据置信度设置颜色
    colors = []
    for o in with_ev:
        if o["confidence"] == "high":
            colors.append("#22c55e")
        elif o["confidence"] == "medium":
            colors.append("#fbbf24")
        else:
            colors.append("#94a3b8")

    fig = go.Figure(go.Bar(
        x=evs,
        y=labels,
        orientation='h',
        marker_color=colors,
        text=[f"{ev:+.1f}%" for ev in evs],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='%{y}<br>EV: %{x:+.1f}%<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(title="期望值 (%)", gridcolor='#334155', tickfont=dict(color='#94a3b8')),
        yaxis=dict(autorange="reversed", tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=60, t=10, b=20),
        height=max(300, len(with_ev) * 35),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
    )
    return fig
