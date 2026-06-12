"""
Monte Carlo Tournament Simulator for World Cup 2026.

Runs N full tournament simulations:
1. Group stage: Simulate all 72 group matches
2. Rank 3rd place teams: Top 8 advance
3. Knockout: R32 → R16 → QF → SF → Final
4. Aggregate: Championship probability for each team
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import itertools

from ..utils.config import GROUPS, TEAMS, DEFAULT_N_SIMULATIONS, EXTRA_TIME_GOAL_REDUCTION, HOSTS
from ..utils.tournament import (
    TeamStanding, get_group_teams, compute_standings,
    rank_third_place_teams, MatchResult,
)
from .predictor import MatchPredictor


class TournamentSimulator:
    """
    Monte Carlo simulation of the full World Cup tournament.
    """

    def __init__(self, predictor: MatchPredictor):
        self.predictor = predictor
        self.results_cache: Dict = {}

    def simulate_match(self, home: str, away: str,
                       neutral: bool = True,
                       extra_time: bool = False) -> Tuple[int, int, str]:
        """
        Simulate one match.

        Returns (home_goals, away_goals, winner).
        For knockout matches that end in a draw, simulates extra time + penalties.

        Args:
            extra_time: If True, simulate extra time for draws (knockout mode).
        """
        # Use fast Elo-only lambdas for Monte Carlo performance
        lambda_h, lambda_a = self.predictor._compute_lambdas_fast(home, away, neutral)

        home_g = np.random.poisson(lambda_h)
        away_g = np.random.poisson(lambda_a)

        if extra_time and home_g == away_g:
            # Simulate extra time (reduced goals)
            et_home = np.random.poisson(lambda_h * EXTRA_TIME_GOAL_REDUCTION)
            et_away = np.random.poisson(lambda_a * EXTRA_TIME_GOAL_REDUCTION)
            home_g += et_home
            away_g += et_away

            if home_g == away_g:
                # Penalties: slight Elo advantage
                elo_diff = self.predictor.get_team_elo(home) - self.predictor.get_team_elo(away)
                pen_prob = 1.0 / (1.0 + np.exp(-elo_diff / 200.0))
                if np.random.random() < pen_prob:
                    home_g += 1  # Home wins on penalties
                else:
                    away_g += 1  # Away wins on penalties

        if home_g > away_g:
            winner = home
        elif away_g > home_g:
            winner = away
        else:
            winner = "draw"

        return home_g, away_g, winner

    def simulate_group(self, group: str,
                       existing_results: List[MatchResult] = None) -> List[TeamStanding]:
        """
        Simulate all matches in a group, respecting any already-completed matches.

        Returns standings sorted by (points, GD, GS).
        """
        teams = get_group_teams(group)
        standings = {t: TeamStanding(team=t) for t in teams}

        # Apply existing results first
        completed_matches = set()
        if existing_results:
            for mr in existing_results:
                if mr.home in teams and mr.away in teams and mr.completed:
                    standings[mr.home].add_result(mr.home_goals, mr.away_goals)
                    standings[mr.away].add_result(mr.away_goals, mr.home_goals)
                    completed_matches.add((mr.home, mr.away))

        # Simulate remaining matches
        all_pairs = list(itertools.combinations(teams, 2))
        for home, away in all_pairs:
            if (home, away) in completed_matches or (away, home) in completed_matches:
                continue
            hg, ag, _ = self.simulate_match(home, away, neutral=True)
            standings[home].add_result(hg, ag)
            standings[away].add_result(ag, hg)

        return sorted(
            standings.values(),
            key=lambda s: (s.points, s.goal_diff, s.goals_for),
            reverse=True,
        )

    def simulate_tournament(self, group_results: Dict[str, List[MatchResult]] = None) -> Dict:
        """
        Run one full tournament simulation.

        Returns dict with winner and stage results.
        """
        if group_results is None:
            group_results = {}

        # ── Group Stage ──────────────────────────────
        all_standings = {}
        for group in GROUPS:
            existing = group_results.get(group, [])
            all_standings[group] = self.simulate_group(group, existing)

        # Group winners and runners-up
        group_winners = {}
        group_runners_up = {}
        for group, standings in all_standings.items():
            group_winners[group] = standings[0].team
            group_runners_up[group] = standings[1].team

        # Best 8 third-place teams
        thirds = rank_third_place_teams(all_standings)
        third_teams = [t.team for t in thirds]

        # ── Fill Bracket Slots ───────────────────────
        # Slot order from BRACKET_SLOTS in config
        from ..utils.config import BRACKET_SLOTS
        slot_teams = {}

        for slot_id, _, source in BRACKET_SLOTS:
            if source.startswith("1"):  # Group winner
                group_letter = source[1]
                slot_teams[slot_id] = group_winners.get(group_letter, "TBD")
            elif source.startswith("2"):  # Runner-up
                group_letter = source[1]
                slot_teams[slot_id] = group_runners_up.get(group_letter, "TBD")
            elif source.startswith("3rd"):  # Best 3rd place
                idx = int(source.split("-")[1]) - 1
                if idx < len(third_teams):
                    slot_teams[slot_id] = third_teams[idx]
                else:
                    slot_teams[slot_id] = "TBD"

        # ── Knockout Stage ───────────────────────────
        winners = {}  # match_name → winning team
        stage_results = {round_name: [] for round_name in ["R32", "R16", "QF", "SF"]}
        stage_results["Third"] = []
        stage_results["Final"] = []

        # R32 matches
        r32_matches = [
            ("R32-1", slot_teams[1], slot_teams[2]),
            ("R32-2", slot_teams[3], slot_teams[4]),
            ("R32-3", slot_teams[5], slot_teams[6]),
            ("R32-4", slot_teams[7], slot_teams[8]),
            ("R32-5", slot_teams[9], slot_teams[10]),
            ("R32-6", slot_teams[11], slot_teams[12]),
            ("R32-7", slot_teams[13], slot_teams[14]),
            ("R32-8", slot_teams[15], slot_teams[16]),
            ("R32-9", slot_teams[17], slot_teams[18]),
            ("R32-10", slot_teams[19], slot_teams[20]),
            ("R32-11", slot_teams[21], slot_teams[22]),
            ("R32-12", slot_teams[23], slot_teams[24]),
            ("R32-13", slot_teams[25], slot_teams[26]),
            ("R32-14", slot_teams[27], slot_teams[28]),
            ("R32-15", slot_teams[29], slot_teams[30]),
            ("R32-16", slot_teams[31], slot_teams[32]),
        ]

        for match_name, home, away in r32_matches:
            if home == "TBD" or away == "TBD":
                winners[match_name] = home if home != "TBD" else away
                continue
            hg, ag, winner = self.simulate_match(home, away, neutral=True, extra_time=True)
            winners[match_name] = winner
            stage_results["R32"].append({
                "match": match_name, "home": home, "away": away,
                "home_goals": hg, "away_goals": ag, "winner": winner,
            })

        # R16 matches
        def knockout_round(round_name: str, match_pairs: List[Tuple[str, str, str]]):
            for match_name, ref_a, ref_b in match_pairs:
                team_a = winners.get(ref_a, ref_a)
                team_b = winners.get(ref_b, ref_b)
                # Remove W- prefix for winner references
                if team_a.startswith("W-"):
                    team_a = winners.get(team_a[2:], team_a[2:])
                if team_b.startswith("W-"):
                    team_b = winners.get(team_b[2:], team_b[2:])

                if team_a == "TBD" or team_b == "TBD":
                    winners[match_name] = team_a if team_a != "TBD" else team_b
                    continue
                if team_a == team_b:
                    winners[match_name] = team_a
                    continue

                hg, ag, winner = self.simulate_match(team_a, team_b, neutral=True, extra_time=True)
                winners[match_name] = winner
                stage_results[round_name].append({
                    "match": match_name, "home": team_a, "away": team_b,
                    "home_goals": hg, "away_goals": ag, "winner": winner,
                })

        knockout_round("R16", [
            ("R16-1", "R32-1", "R32-2"),
            ("R16-2", "R32-3", "R32-4"),
            ("R16-3", "R32-5", "R32-6"),
            ("R16-4", "R32-7", "R32-8"),
            ("R16-5", "R32-9", "R32-10"),
            ("R16-6", "R32-11", "R32-12"),
            ("R16-7", "R32-13", "R32-14"),
            ("R16-8", "R32-15", "R32-16"),
        ])

        knockout_round("QF", [
            ("QF-1", "R16-1", "R16-2"),
            ("QF-2", "R16-3", "R16-4"),
            ("QF-3", "R16-5", "R16-6"),
            ("QF-4", "R16-7", "R16-8"),
        ])

        knockout_round("SF", [
            ("SF-1", "QF-1", "QF-2"),
            ("SF-2", "QF-3", "QF-4"),
        ])

        # Third place match
        sf1_loser = None
        sf2_loser = None
        for m in stage_results["SF"]:
            if m["match"] == "SF-1":
                sf1_loser = m["home"] if m["winner"] == m["away"] else m["away"]
            if m["match"] == "SF-2":
                sf2_loser = m["home"] if m["winner"] == m["away"] else m["away"]

        if sf1_loser and sf2_loser:
            hg, ag, winner = self.simulate_match(sf1_loser, sf2_loser, neutral=True, extra_time=True)
            stage_results["Third"].append({
                "match": "3rd", "home": sf1_loser, "away": sf2_loser,
                "home_goals": hg, "away_goals": ag, "winner": winner,
            })

        # Final
        w_sf1 = winners.get("SF-1", "TBD")
        w_sf2 = winners.get("SF-2", "TBD")
        if w_sf1 != "TBD" and w_sf2 != "TBD":
            hg, ag, winner = self.simulate_match(w_sf1, w_sf2, neutral=True, extra_time=True)
            winners["Final"] = winner
            stage_results["Final"].append({
                "match": "Final", "home": w_sf1, "away": w_sf2,
                "home_goals": hg, "away_goals": ag, "winner": winner,
            })

        champion = winners.get("Final", "TBD")
        return {
            "champion": champion,
            "group_standings": all_standings,
            "stage_results": stage_results,
        }

    def run(self, n_simulations: int = DEFAULT_N_SIMULATIONS,
            progress_callback=None) -> Dict:
        """
        Run N full tournament simulations and aggregate results.

        Args:
            n_simulations: Number of simulations to run
            progress_callback: Optional callable(i, n) for progress updates

        Returns:
            Dict with aggregated probabilities
        """
        # Track results
        champion_counts = defaultdict(int)
        final_counts = defaultdict(int)
        sf_counts = defaultdict(int)
        qf_counts = defaultdict(int)
        r16_counts = defaultdict(int)
        r32_counts = defaultdict(int)

        all_teams = list(TEAMS.keys())

        for sim_idx in range(n_simulations):
            result = self.simulate_tournament()

            champ = result["champion"]
            champion_counts[champ] += 1

            # Track stage reached
            for round_name, matches in result["stage_results"].items():
                for m in matches:
                    if round_name == "R32":
                        r32_counts[m["home"]] += 1
                        r32_counts[m["away"]] += 1
                    if round_name == "R16":
                        r16_counts[m["home"]] += 1
                        r16_counts[m["away"]] += 1
                    if round_name == "QF":
                        qf_counts[m["home"]] += 1
                        qf_counts[m["away"]] += 1
                    if round_name == "SF":
                        sf_counts[m["home"]] += 1
                        sf_counts[m["away"]] += 1
                    if round_name == "Final":
                        final_counts[m["home"]] += 1
                        final_counts[m["away"]] += 1

            if progress_callback and (sim_idx + 1) % max(1, n_simulations // 100) == 0:
                progress_callback(sim_idx + 1, n_simulations)

        # Compute probabilities
        def prob_dict(counts, n):
            return {
                team: round(counts.get(team, 0) / n, 4)
                for team in all_teams
            }

        results = {
            "n_simulations": n_simulations,
            "champion": prob_dict(champion_counts, n_simulations),
            "final": prob_dict(final_counts, n_simulations),
            "semifinal": prob_dict(sf_counts, n_simulations),
            "quarterfinal": prob_dict(qf_counts, n_simulations),
            "r16": prob_dict(r16_counts, n_simulations),
            "r32": prob_dict(r32_counts, n_simulations),
        }

        # Sort teams by championship probability
        results["top_contenders"] = sorted(
            [(team, results["champion"][team]) for team in all_teams
             if results["champion"][team] > 0],
            key=lambda x: x[1], reverse=True
        )[:20]

        self.results_cache = results
        return results

    def get_team_path_probability(self, team: str) -> Dict:
        """
        Get a team's probability of reaching each stage.
        """
        if not self.results_cache:
            return {}

        return {
            "champion": self.results_cache["champion"].get(team, 0),
            "final": self.results_cache["final"].get(team, 0),
            "semifinal": self.results_cache["semifinal"].get(team, 0),
            "quarterfinal": self.results_cache["quarterfinal"].get(team, 0),
            "r16": self.results_cache["r16"].get(team, 0),
        }
