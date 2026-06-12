"""
Tournament structure: groups, standings, bracket logic.
Handles the 2026 format: 12 groups of 4, top 2 + 8 best 3rd → R32.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import itertools

from .config import GROUPS, TEAMS, N_GROUPS, TEAMS_PER_GROUP


@dataclass
class MatchResult:
    """Single match result."""
    home: str
    away: str
    home_goals: int
    away_goals: int
    round_name: str = "Group"
    neutral: bool = True
    completed: bool = False

    @property
    def winner(self) -> Optional[str]:
        if not self.completed:
            return None
        if self.home_goals > self.away_goals:
            return self.home
        elif self.away_goals > self.home_goals:
            return self.away
        return None

    @property
    def is_draw(self) -> bool:
        return self.completed and self.home_goals == self.away_goals


@dataclass
class TeamStanding:
    """Team standing in a group."""
    team: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

    def add_result(self, goals_for: int, goals_against: int):
        """Record a match result for this team."""
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.wins += 1
        elif goals_for < goals_against:
            self.losses += 1
        else:
            self.draws += 1


def get_group_teams(group: str) -> List[str]:
    """Get teams in a group."""
    return GROUPS.get(group, [])


def get_team_group(team: str) -> Optional[str]:
    """Find which group a team is in."""
    for group, teams in GROUPS.items():
        if team in teams:
            return group
    return None


def get_all_teams() -> List[str]:
    """Get list of all 48 teams."""
    return list(TEAMS.keys())


def get_group_matches(group: str) -> List[Tuple[str, str]]:
    """
    Generate all 6 match pairings for a 4-team group.
    Each team plays the other 3 teams once.
    """
    teams = GROUPS.get(group, [])
    if len(teams) != 4:
        return []
    # Round-robin: all combinations of 2 from 4
    return list(itertools.combinations(teams, 2))


def compute_standings(group: str, results: List[MatchResult]) -> List[TeamStanding]:
    """
    Compute group standings from match results.
    Sorted by: points (desc), goal diff (desc), goals for (desc).
    """
    teams = GROUPS.get(group, [])
    standings = {t: TeamStanding(team=t) for t in teams}

    for match in results:
        if match.home in standings and match.away in standings and match.completed:
            standings[match.home].add_result(match.home_goals, match.away_goals)
            standings[match.away].add_result(match.away_goals, match.home_goals)

    sorted_standings = sorted(
        standings.values(),
        key=lambda s: (s.points, s.goal_diff, s.goals_for),
        reverse=True,
    )
    return sorted_standings


def rank_third_place_teams(all_group_standings: Dict[str, List[TeamStanding]]) -> List[TeamStanding]:
    """
    Rank all 12 third-place teams to select the best 8.
    Sorted by: points (desc), goal diff (desc), goals for (desc).
    Returns the top 8 third-place teams.
    """
    thirds = []
    for group, standings in all_group_standings.items():
        if len(standings) >= 3:
            third = standings[2]  # 0-indexed, so index 2 = 3rd place
            # third-place team name preserved as-is
            thirds.append(third)

    sorted_thirds = sorted(
        thirds,
        key=lambda s: (s.points, s.goal_diff, s.goals_for),
        reverse=True,
    )
    return sorted_thirds[:8]  # Best 8 of 12


def get_knockout_bracket() -> Dict:
    """
    Returns the full knockout bracket structure.
    Maps round names to list of match slots.
    """
    return {
        "R32": [
            ("R32-1", "1A", "3rd-1"),
            ("R32-2", "1C", "2B"),
            ("R32-3", "1E", "3rd-2"),
            ("R32-4", "1G", "2H"),
            ("R32-5", "1I", "3rd-3"),
            ("R32-6", "1K", "2L"),
            ("R32-7", "1B", "3rd-4"),
            ("R32-8", "1D", "2A"),
            ("R32-9", "1F", "3rd-5"),
            ("R32-10", "1H", "2G"),
            ("R32-11", "1J", "3rd-6"),
            ("R32-12", "1L", "2K"),
            ("R32-13", "2C", "3rd-7"),
            ("R32-14", "2E", "2D"),
            ("R32-15", "2F", "3rd-8"),
            ("R32-16", "2I", "2J"),
        ],
        "R16": [
            ("R16-1", "W-R32-1", "W-R32-2"),
            ("R16-2", "W-R32-3", "W-R32-4"),
            ("R16-3", "W-R32-5", "W-R32-6"),
            ("R16-4", "W-R32-7", "W-R32-8"),
            ("R16-5", "W-R32-9", "W-R32-10"),
            ("R16-6", "W-R32-11", "W-R32-12"),
            ("R16-7", "W-R32-13", "W-R32-14"),
            ("R16-8", "W-R32-15", "W-R32-16"),
        ],
        "QF": [
            ("QF-1", "W-R16-1", "W-R16-2"),
            ("QF-2", "W-R16-3", "W-R16-4"),
            ("QF-3", "W-R16-5", "W-R16-6"),
            ("QF-4", "W-R16-7", "W-R16-8"),
        ],
        "SF": [
            ("SF-1", "W-QF-1", "W-QF-2"),
            ("SF-2", "W-QF-3", "W-QF-4"),
        ],
        "Third": [("3rd", "L-SF-1", "L-SF-2")],
        "Final": [("Final", "W-SF-1", "W-SF-2")],
    }
