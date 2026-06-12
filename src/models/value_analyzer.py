"""
投注价值分析器 — 计算期望值、Kelly系数、让球/大小球概率

核心功能：
- Expected Value (EV) 计算
- Kelly Criterion 计算
- 让球概率计算（从比分矩阵）
- 大小球概率计算（从比分矩阵）
- 综合价值分析
"""

from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_ev(model_prob: float, odds: float) -> float:
    """
    计算期望值 (Expected Value)

    EV = (model_probability * decimal_odds) - 1

    Args:
        model_prob: 模型估计的概率 (0-1)
        odds: 十进制赔率

    Returns:
        期望值，正值表示有投注价值
    """
    if odds <= 0 or model_prob <= 0:
        return 0.0
    return round(model_prob * odds - 1, 4)


def calculate_kelly(model_prob: float, odds: float) -> float:
    """
    计算 Kelly Criterion（凯利公式）

    f* = (model_probability * decimal_odds - 1) / (decimal_odds - 1)

    使用 1/4 Kelly 以降低风险，上限 25%

    Args:
        model_prob: 模型估计的概率 (0-1)
        odds: 十进制赔率

    Returns:
        建议投注比例 (0-0.25)
    """
    if odds <= 1 or model_prob <= 0:
        return 0.0

    ev = model_prob * odds - 1
    if ev <= 0:
        return 0.0

    kelly = ev / (odds - 1)
    # 使用 1/4 Kelly 并限制上限
    kelly = min(kelly * 0.25, 0.25)
    return round(max(0.0, kelly), 4)


def get_confidence(ev: float, model_prob: float) -> str:
    """
    根据 EV 和模型概率评估置信度

    Args:
        ev: 期望值
        model_prob: 模型概率

    Returns:
        "high" / "medium" / "low"
    """
    if ev >= 0.10 and model_prob >= 0.30:
        return "high"
    elif ev >= 0.05 and model_prob >= 0.20:
        return "medium"
    else:
        return "low"


def compute_handicap_probabilities(scoreline_matrix: List[List[float]],
                                   goal_line: float) -> Dict[str, float]:
    """
    从比分矩阵计算让球概率

    Args:
        scoreline_matrix: NxN 矩阵，scoreline_matrix[i][j] = P(home=i, away=j)
        goal_line: 让球数，负数表示主队让球
                   例如：-1.0 表示主队让1球，+0.5 表示主队受让0.5球

    Returns:
        {"home": P, "draw": P, "away": P}
    """
    home_prob = 0.0
    draw_prob = 0.0
    away_prob = 0.0

    for i in range(len(scoreline_matrix)):
        for j in range(len(scoreline_matrix[i])):
            p = scoreline_matrix[i][j]
            # 让球结果 = 主队进球 + 让球数 - 客队进球
            # goal_line 为负表示主队让球
            result = i + goal_line - j

            if abs(result) < 0.01:  # 平局（考虑浮点误差）
                draw_prob += p
            elif result > 0:  # 主队赢盘
                home_prob += p
            else:  # 客队赢盘
                away_prob += p

    return {
        "home": round(home_prob, 4),
        "draw": round(draw_prob, 4),
        "away": round(away_prob, 4)
    }


def compute_over_under_from_matrix(scoreline_matrix: List[List[float]],
                                   line: float) -> Dict[str, float]:
    """
    从比分矩阵计算大小球概率

    Args:
        scoreline_matrix: NxN 矩阵
        line: 大小球盘口，如 2.5, 3.5

    Returns:
        {"over": P, "under": P}
    """
    over_prob = 0.0
    under_prob = 0.0

    for i in range(len(scoreline_matrix)):
        for j in range(len(scoreline_matrix[i])):
            total = i + j
            p = scoreline_matrix[i][j]
            if total > line:
                over_prob += p
            else:
                under_prob += p

    return {
        "over": round(over_prob, 4),
        "under": round(under_prob, 4)
    }


def analyze_match_value(match_odds: Dict, prediction: Dict) -> List[Dict]:
    """
    分析单场比赛的所有投注价值

    Args:
        match_odds: 比赛赔率数据（来自 SportteryScraper）
        prediction: 模型预测数据（来自 MatchPredictor.predict()）

    Returns:
        投注机会列表，按 EV 降序排列
    """
    opportunities = []

    home_team = match_odds.get("home_team", "")
    away_team = match_odds.get("away_team", "")
    match_label = f"{home_team} vs {away_team}"
    match_date = match_odds.get("date", "")
    match_time = match_odds.get("match_time", "")

    # ── 胜平负 (HAD) 市场 ─────────────────────────
    had_odds = match_odds.get("odds_had", {})
    if had_odds:
        for selection_key, selection_cn, odds_key in [
            ("home_win", "主胜", "h"),
            ("draw", "平局", "d"),
            ("away_win", "客胜", "a")
        ]:
            odds = had_odds.get(odds_key)
            if odds and odds > 0:
                model_prob = prediction.get(selection_key, 0)
                ev = calculate_ev(model_prob, odds)
                kelly = calculate_kelly(model_prob, odds)

                opportunities.append({
                    "match_label": match_label,
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": match_date,
                    "match_time": match_time,
                    "market": "HAD",
                    "market_cn": "胜平负",
                    "selection": selection_cn,
                    "selection_key": selection_key,
                    "model_prob": model_prob,
                    "implied_prob": round(1.0 / odds, 4),
                    "odds": odds,
                    "ev": ev,
                    "kelly": kelly,
                    "confidence": get_confidence(ev, model_prob),
                })

    # ── 让球胜平负 (HHAD) 市场 ─────────────────────
    hhad_odds = match_odds.get("odds_hhad", {})
    if hhad_odds and "scoreline_matrix" in prediction:
        goal_line_str = hhad_odds.get("goal_line", "0")
        try:
            goal_line = float(goal_line_str)
        except (ValueError, TypeError):
            goal_line = 0.0

        # 从比分矩阵计算让球概率
        handicap_probs = compute_handicap_probabilities(
            prediction["scoreline_matrix"], goal_line
        )

        for selection_key, selection_cn, odds_key in [
            ("home", "主胜", "h"),
            ("draw", "平局", "d"),
            ("away", "客胜", "a")
        ]:
            odds = hhad_odds.get(odds_key)
            if odds and odds > 0:
                model_prob = handicap_probs.get(selection_key, 0)
                ev = calculate_ev(model_prob, odds)
                kelly = calculate_kelly(model_prob, odds)

                # 构建显示标签
                if goal_line < 0:
                    line_display = f"让{abs(goal_line)}球"
                elif goal_line > 0:
                    line_display = f"受让{goal_line}球"
                else:
                    line_display = "平手"

                opportunities.append({
                    "match_label": match_label,
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": match_date,
                    "match_time": match_time,
                    "market": "HHAD",
                    "market_cn": f"让球({goal_line})",
                    "selection": f"{selection_cn}({goal_line})",
                    "selection_key": f"handicap_{selection_key}",
                    "model_prob": model_prob,
                    "implied_prob": round(1.0 / odds, 4),
                    "odds": odds,
                    "ev": ev,
                    "kelly": kelly,
                    "confidence": get_confidence(ev, model_prob),
                })

    # ── 大小球 (TTG) 市场 ─────────────────────────
    # 如果有 TTG 赔率数据
    ttg_odds = match_odds.get("odds_ttg", {})
    if ttg_odds and "scoreline_matrix" in prediction:
        for line_key, line_value in [("over_2_5", 2.5), ("under_2_5", 2.5),
                                     ("over_3_5", 3.5), ("under_3_5", 3.5)]:
            odds = ttg_odds.get(line_key)
            if odds and odds > 0:
                ou_probs = compute_over_under_from_matrix(
                    prediction["scoreline_matrix"], line_value
                )
                is_over = line_key.startswith("over")
                model_prob = ou_probs["over"] if is_over else ou_probs["under"]
                ev = calculate_ev(model_prob, odds)
                kelly = calculate_kelly(model_prob, odds)

                selection_cn = f"大{line_value}" if is_over else f"小{line_value}"
                opportunities.append({
                    "match_label": match_label,
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": match_date,
                    "match_time": match_time,
                    "market": "TTG",
                    "market_cn": "大小球",
                    "selection": selection_cn,
                    "selection_key": line_key,
                    "model_prob": model_prob,
                    "implied_prob": round(1.0 / odds, 4),
                    "odds": odds,
                    "ev": ev,
                    "kelly": kelly,
                    "confidence": get_confidence(ev, model_prob),
                })

    # ── 大小球（无赔率，仅模型推荐）────────────────
    # 即使没有 TTG 赔率，也可以提供模型预测
    if "scoreline_matrix" in prediction and not ttg_odds:
        for line_value in [2.5, 3.5]:
            ou_probs = compute_over_under_from_matrix(
                prediction["scoreline_matrix"], line_value
            )
            # 只推荐概率 > 60% 的选项
            if ou_probs["over"] > 0.6:
                opportunities.append({
                    "match_label": match_label,
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": match_date,
                    "match_time": match_time,
                    "market": "TTG_MODEL",
                    "market_cn": "大小球(模型)",
                    "selection": f"大{line_value}",
                    "selection_key": f"over_{line_value}",
                    "model_prob": ou_probs["over"],
                    "implied_prob": None,
                    "odds": None,
                    "ev": None,
                    "kelly": None,
                    "confidence": "model_only",
                })
            elif ou_probs["under"] > 0.6:
                opportunities.append({
                    "match_label": match_label,
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": match_date,
                    "match_time": match_time,
                    "market": "TTG_MODEL",
                    "market_cn": "大小球(模型)",
                    "selection": f"小{line_value}",
                    "selection_key": f"under_{line_value}",
                    "model_prob": ou_probs["under"],
                    "implied_prob": None,
                    "odds": None,
                    "ev": None,
                    "kelly": None,
                    "confidence": "model_only",
                })

    # 按 EV 降序排序（None 排最后）
    opportunities.sort(key=lambda x: x["ev"] if x["ev"] is not None else -999, reverse=True)
    return opportunities


def scan_all_matches(odds_list: List[Dict], predictor,
                     min_ev: float = 0.0,
                     markets: Optional[List[str]] = None) -> List[Dict]:
    """
    扫描所有比赛，筛选有价值的投注选项

    Args:
        odds_list: 赔率列表（来自 SportteryScraper.get_world_cup_odds()）
        predictor: MatchPredictor 实例
        min_ev: 最低 EV 阈值
        markets: 要分析的市场类型，如 ["HAD", "HHAD", "TTG"]

    Returns:
        所有正 EV 投注机会，按 EV 降序排列
    """
    if markets is None:
        markets = ["HAD", "HHAD", "TTG"]

    all_opportunities = []

    for match_odds in odds_list:
        home_team = match_odds.get("home_team")
        away_team = match_odds.get("away_team")

        if not home_team or not away_team:
            continue

        try:
            # 运行模型预测
            prediction = predictor.predict(home_team, away_team, neutral=True)

            # 分析价值
            opportunities = analyze_match_value(match_odds, prediction)

            # 按市场类型筛选
            for opp in opportunities:
                market_type = opp["market"]
                if market_type in markets or (market_type == "TTG_MODEL" and "TTG" in markets):
                    if opp["ev"] is not None and opp["ev"] >= min_ev:
                        all_opportunities.append(opp)

        except Exception as e:
            logger.warning(f"分析比赛 {home_team} vs {away_team} 时出错: {e}")
            continue

    # 按 EV 降序排序
    all_opportunities.sort(key=lambda x: x["ev"] if x["ev"] is not None else -999, reverse=True)
    return all_opportunities


def get_summary_stats(opportunities: List[Dict]) -> Dict:
    """
    计算投注机会的汇总统计

    Args:
        opportunities: 投注机会列表

    Returns:
        汇总统计字典
    """
    if not opportunities:
        return {
            "total": 0,
            "positive_ev_count": 0,
            "avg_ev": 0,
            "max_ev": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "model_only": 0,
        }

    # 过滤掉仅模型推荐（无 EV）
    with_ev = [o for o in opportunities if o["ev"] is not None]

    return {
        "total": len(opportunities),
        "positive_ev_count": len([o for o in with_ev if o["ev"] > 0]),
        "avg_ev": round(sum(o["ev"] for o in with_ev) / len(with_ev), 4) if with_ev else 0,
        "max_ev": round(max(o["ev"] for o in with_ev), 4) if with_ev else 0,
        "high_confidence": len([o for o in opportunities if o["confidence"] == "high"]),
        "medium_confidence": len([o for o in opportunities if o["confidence"] == "medium"]),
        "low_confidence": len([o for o in opportunities if o["confidence"] == "low"]),
        "model_only": len([o for o in opportunities if o["confidence"] == "model_only"]),
    }
