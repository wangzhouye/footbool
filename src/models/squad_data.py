"""
球队阵容数据 — 关键球员和阵容深度

功能：
- 各队关键球员信息
- 球员重要性评分
- 阵容深度评估
- 关键球员缺阵影响计算

用法：
    squad = get_squad_data()
    impact = squad.calculate_squad_impact("Argentina", injured_players=["Messi"])
"""

from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class Player:
    """球员信息"""

    def __init__(self, name: str, team: str, position: str,
                 importance: float = 1.0, status: str = "available"):
        """
        Args:
            name: 球员名称
            team: 所属国家队
            position: 位置 (GK/DF/MF/FW)
            importance: 重要性评分 (0.0-1.0)
            status: 状态 (available/injured/suspended/unknown)
        """
        self.name = name
        self.team = team
        self.position = position
        self.importance = importance
        self.status = status


class SquadData:
    """球队阵容数据管理"""

    def __init__(self):
        self.players = self._load_default_players()

    def _load_default_players(self) -> Dict[str, List[Player]]:
        """加载默认球员数据（2026世界杯各队核心球员）"""
        players = {}

        # 阿根廷
        players["Argentina"] = [
            Player("Messi", "Argentina", "FW", 0.95),
            Player("Alvarez", "Argentina", "FW", 0.85),
            Player("Enzo Fernandez", "Argentina", "MF", 0.88),
            Player("Mac Allister", "Argentina", "MF", 0.82),
            Player("Otamendi", "Argentina", "DF", 0.78),
            Player("Martinez", "Argentina", "GK", 0.80),
        ]

        # 法国
        players["France"] = [
            Player("Mbappe", "France", "FW", 0.95),
            Player("Griezmann", "France", "FW", 0.85),
            Player("Tchouameni", "France", "MF", 0.82),
            Player("Rabiot", "France", "MF", 0.78),
            Player("Varane", "France", "DF", 0.80),
            Player("Lloris", "France", "GK", 0.75),
        ]

        # 英格兰
        players["England"] = [
            Player("Kane", "England", "FW", 0.92),
            Player("Bellingham", "England", "MF", 0.90),
            Player("Saka", "England", "FW", 0.85),
            Player("Rice", "England", "MF", 0.85),
            Player("Walker", "England", "DF", 0.78),
            Player("Pickford", "England", "GK", 0.75),
        ]

        # 巴西
        players["Brazil"] = [
            Player("Vinicius Jr", "Brazil", "FW", 0.93),
            Player("Rodrygo", "Brazil", "FW", 0.85),
            Player("Casemiro", "Brazil", "MF", 0.82),
            Player("Bruno Guimaraes", "Brazil", "MF", 0.80),
            Player("Marquinhos", "Brazil", "DF", 0.82),
            Player("Alisson", "Brazil", "GK", 0.85),
        ]

        # 西班牙
        players["Spain"] = [
            Player("Pedri", "Spain", "MF", 0.90),
            Player("Gavi", "Spain", "MF", 0.85),
            Player("Morata", "Spain", "FW", 0.78),
            Player("Yamal", "Spain", "FW", 0.82),
            Player("Rodri", "Spain", "MF", 0.88),
            Player("Simon", "Spain", "GK", 0.75),
        ]

        # 德国
        players["Germany"] = [
            Player("Musiala", "Germany", "MF", 0.90),
            Player("Wirtz", "Germany", "MF", 0.88),
            Player("Havertz", "Germany", "FW", 0.82),
            Player("Gundogan", "Germany", "MF", 0.80),
            Player("Rudiger", "Germany", "DF", 0.82),
            Player("Neuer", "Germany", "GK", 0.78),
        ]

        # 葡萄牙
        players["Portugal"] = [
            Player("Ronaldo", "Portugal", "FW", 0.88),
            Player("Bernardo Silva", "Portugal", "MF", 0.88),
            Player("Bruno Fernandes", "Portugal", "MF", 0.90),
            Player("Dias", "Portugal", "DF", 0.82),
            Player("Cancelo", "Portugal", "DF", 0.80),
            Player("Diogo Costa", "Portugal", "GK", 0.78),
        ]

        # 荷兰
        players["Netherlands"] = [
            Player("Gakpo", "Netherlands", "FW", 0.82),
            Player("Depay", "Netherlands", "FW", 0.80),
            Player("De Jong", "Netherlands", "MF", 0.85),
            Player("Gravenberch", "Netherlands", "MF", 0.78),
            Player("Van Dijk", "Netherlands", "DF", 0.90),
            Player("Bijlow", "Netherlands", "GK", 0.75),
        ]

        # 克罗地亚
        players["Croatia"] = [
            Player("Modric", "Croatia", "MF", 0.88),
            Player("Kovacic", "Croatia", "MF", 0.82),
            Player("Perisic", "Croatia", "FW", 0.78),
            Player("Kramaric", "Croatia", "FW", 0.75),
            Player("Gvardiol", "Croatia", "DF", 0.85),
            Player("Livakovic", "Croatia", "GK", 0.78),
        ]

        # 比利时
        players["Belgium"] = [
            Player("De Bruyne", "Belgium", "MF", 0.95),
            Player("Lukaku", "Belgium", "FW", 0.85),
            Player("Trossard", "Belgium", "FW", 0.80),
            Player("Onana", "Belgium", "MF", 0.78),
            Player("Vertonghen", "Belgium", "DF", 0.75),
            Player("Courtois", "Belgium", "GK", 0.88),
        ]

        # 阿根廷的对手们
        players["Morocco"] = [
            Player("Hakimi", "Morocco", "DF", 0.88),
            Player("Ziyech", "Morocco", "MF", 0.82),
            Player("En-Nesyri", "Morocco", "FW", 0.78),
            Player("Amrabat", "Morocco", "MF", 0.80),
            Player("Mazraoui", "Morocco", "DF", 0.78),
            Player("Bono", "Morocco", "GK", 0.80),
        ]

        players["Japan"] = [
            Player("Kubo", "Japan", "FW", 0.85),
            Player("Mitoma", "Japan", "FW", 0.82),
            Player("Kamada", "Japan", "MF", 0.80),
            Player("Endo", "Japan", "MF", 0.78),
            Player("Itakura", "Japan", "DF", 0.75),
            Player("Gonda", "Japan", "GK", 0.72),
        ]

        players["South Korea"] = [
            Player("Son Heung-min", "South Korea", "FW", 0.92),
            Player("Lee Kang-in", "South Korea", "MF", 0.82),
            Player("Hwang Hee-chan", "South Korea", "FW", 0.78),
            Player("Kim Min-jae", "South Korea", "DF", 0.85),
            Player("Jung Woo-young", "South Korea", "MF", 0.75),
            Player("Kim Seung-gyu", "South Korea", "GK", 0.72),
        ]

        players["USA"] = [
            Player("Pulisic", "USA", "FW", 0.88),
            Player("McKennie", "USA", "MF", 0.82),
            Player("Reyna", "USA", "MF", 0.80),
            Player("Adams", "USA", "MF", 0.78),
            Player("Robinson", "USA", "DF", 0.75),
            Player("Turner", "USA", "GK", 0.72),
        ]

        players["Mexico"] = [
            Player("Lozano", "Mexico", "FW", 0.82),
            Player("Vega", "Mexico", "FW", 0.78),
            Player("Alvarez", "Mexico", "MF", 0.80),
            Player("Guardado", "Mexico", "MF", 0.75),
            Player("Araujo", "Mexico", "DF", 0.78),
            Player("Ochoa", "Mexico", "GK", 0.80),
        ]

        # 补充更多队伍的基本数据
        for team in ["Switzerland", "Australia", "Qatar", "Turkey", "Tunisia",
                      "Ecuador", "Ivory Coast", "Senegal", "Ghana", "Nigeria",
                      "Cameroon", "Egypt", "Paraguay", "Uruguay", "Colombia",
                      "Peru", "Chile", "Canada", "Bosnia", "Czech Republic",
                      "Poland", "Sweden", "Denmark", "Norway", "Austria",
                      "Scotland", "Wales", "Serbia", "Ukraine", "Romania",
                      "Hungary", "Greece", "Cape Verde", "DR Congo",
                      "Iran", "Saudi Arabia", "Iraq", "Jordan", "Uzbekistan",
                      "Panama", "Curacao", "Haiti", "New Zealand"]:
            if team not in players:
                players[team] = []  # 暂无详细数据

        return players

    def get_team_players(self, team: str) -> List[Player]:
        """获取球队球员列表"""
        return self.players.get(team, [])

    def get_key_players(self, team: str, top_n: int = 3) -> List[Player]:
        """获取球队关键球员（按重要性排序）"""
        players = self.get_team_players(team)
        if not players:
            return []
        sorted_players = sorted(players, key=lambda p: p.importance, reverse=True)
        return sorted_players[:top_n]

    def get_team_strength(self, team: str) -> float:
        """
        计算球队阵容强度 (0.0-1.0)

        基于关键球员的重要性评分
        """
        players = self.get_team_players(team)
        if not players:
            return 0.5  # 默认强度

        # 计算加权平均
        total_importance = sum(p.importance for p in players)
        avg_importance = total_importance / len(players)

        # 归一化到 0.5-1.0 范围
        return 0.5 + (avg_importance - 0.5) * 0.5

    def calculate_squad_impact(self, team: str,
                               injured_players: List[str] = None,
                               suspended_players: List[str] = None) -> Dict:
        """
        计算阵容对比赛的影响

        Args:
            team: 球队名称
            injured_players: 受伤球员列表
            suspended_players: 停赛球员列表

        Returns:
            {
                "strength": float,  # 当前阵容强度
                "key_missing": List[str],  # 缺阵的关键球员
                "impact_score": float,  # 缺阵影响分数 (0-1, 0=无影响, 1=严重影响)
            }
        """
        if injured_players is None:
            injured_players = []
        if suspended_players is None:
            suspended_players = []

        missing_players = set(injured_players + suspended_players)
        players = self.get_team_players(team)

        if not players:
            return {
                "strength": 0.5,
                "key_missing": [],
                "impact_score": 0.0,
            }

        # 计算缺阵影响
        impact_score = 0.0
        key_missing = []

        for player in players:
            if player.name in missing_players:
                impact_score += player.importance
                if player.importance >= 0.8:
                    key_missing.append(player.name)

        # 归一化影响分数
        max_impact = sum(p.importance for p in players)
        if max_impact > 0:
            impact_score = min(1.0, impact_score / max_impact)

        # 计算当前阵容强度
        available_players = [p for p in players if p.name not in missing_players]
        if available_players:
            strength = sum(p.importance for p in available_players) / len(available_players)
        else:
            strength = 0.5

        return {
            "strength": round(strength, 4),
            "key_missing": key_missing,
            "impact_score": round(impact_score, 4),
        }

    def get_position_strength(self, team: str, position: str) -> float:
        """
        获取特定位置的强度

        Args:
            team: 球队名称
            position: 位置 (GK/DF/MF/FW)

        Returns:
            位置强度 (0.0-1.0)
        """
        players = self.get_team_players(team)
        position_players = [p for p in players if p.position == position]

        if not position_players:
            return 0.5

        avg_importance = sum(p.importance for p in position_players) / len(position_players)
        return 0.5 + (avg_importance - 0.5) * 0.5


# 全局单例
_squad_data: Optional[SquadData] = None


def get_squad_data() -> SquadData:
    """获取 SquadData 实例"""
    global _squad_data
    if _squad_data is None:
        _squad_data = SquadData()
    return _squad_data
