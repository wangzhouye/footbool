"""
Live data fetcher — pulls World Cup match results from football-data.org API.
Uses diskcache for TTL-based caching to respect API rate limits.

If no API key is configured, falls back to bundled static data gracefully.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
import pandas as pd
from diskcache import Cache

from ..utils.config import CACHE_DIR

logger = logging.getLogger(__name__)

# ── API Config ──────────────────────────────────────
API_BASE_URL = "https://api.football-data.org/v4"
CACHE_TTL_RESULTS = 1800   # 30 minutes
CACHE_TTL_SCHEDULE = 86400  # 24 hours
CACHE_TTL_STANDINGS = 900   # 15 minutes

# ── Cache ───────────────────────────────────────────
os.makedirs(CACHE_DIR, exist_ok=True)
cache = Cache(CACHE_DIR)


class LiveDataFetcher:
    """
    Fetches live World Cup data from football-data.org.

    Gracefully degrades: if API unavailable, returns empty results
    and the app works with bundled historical data.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY", "")
        self.client = httpx.Client(
            base_url=API_BASE_URL,
            headers={"X-Auth-Token": self.api_key} if self.api_key else {},
            timeout=30.0,
        )
        self._available = bool(self.api_key)

    @property
    def is_available(self) -> bool:
        return self._available

    def _get(self, endpoint: str, cache_key: str, ttl: int) -> Optional[dict]:
        """Cached GET request to the API."""
        # Check cache first
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from API
        try:
            response = self.client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                cache.set(cache_key, data, expire=ttl)
                return data
            else:
                logger.warning(f"API returned {response.status_code} for {endpoint}")
                return None
        except Exception as e:
            logger.warning(f"API request failed: {e}")
            return None

    def get_world_cup_matches(self, matchday: Optional[int] = None) -> Optional[dict]:
        """
        Fetch World Cup matches.
        Competition code 'WC' = FIFA World Cup.
        """
        endpoint = "/competitions/WC/matches"
        params = {}
        if matchday is not None:
            params["matchday"] = matchday

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        if query_string:
            endpoint += f"?{query_string}"

        cache_key = f"wc_matches_md{matchday}"
        return self._get(endpoint, cache_key, CACHE_TTL_RESULTS)

    def get_world_cup_standings(self) -> Optional[dict]:
        """Fetch World Cup group standings."""
        endpoint = "/competitions/WC/standings"
        return self._get(endpoint, "wc_standings", CACHE_TTL_STANDINGS)

    def get_world_cup_teams(self) -> Optional[dict]:
        """Fetch World Cup team list."""
        endpoint = "/competitions/WC/teams"
        return self._get(endpoint, "wc_teams", CACHE_TTL_SCHEDULE)

    def get_today_matches(self) -> Optional[dict]:
        """Fetch today's matches across all competitions."""
        today = datetime.now().strftime("%Y-%m-%d")
        endpoint = f"/matches?dateFrom={today}&dateTo={today}"
        return self._get(endpoint, f"matches_{today}", 1800)

    def parse_match_results(self, api_data: dict) -> pd.DataFrame:
        """
        Parse API match data into a DataFrame compatible with our format.
        """
        if not api_data or "matches" not in api_data:
            return pd.DataFrame()

        matches = []
        for m in api_data["matches"]:
            if m.get("status") != "FINISHED":
                continue

            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            home_score = m["score"]["fullTime"]["home"]
            away_score = m["score"]["fullTime"]["away"]

            if home_score is None or away_score is None:
                continue

            matches.append({
                "date": m["utcDate"][:10],
                "home_team": home,
                "away_team": away,
                "home_score": home_score,
                "away_score": away_score,
                "tournament": m.get("competition", {}).get("name", "World Cup"),
                "city": m.get("venue", ""),
                "country": "",
                "neutral": True,
            })

        return pd.DataFrame(matches)

    def parse_standings(self, api_data: dict) -> Dict[str, List[dict]]:
        """Parse API standings into group → team list."""
        if not api_data or "standings" not in api_data:
            return {}

        groups = {}
        for standing_group in api_data["standings"]:
            group_name = standing_group["group"]
            teams = []
            for entry in standing_group["table"]:
                teams.append({
                    "team": entry["team"]["name"],
                    "played": entry["playedGames"],
                    "won": entry["won"],
                    "draw": entry["draw"],
                    "lost": entry["lost"],
                    "goals_for": entry["goalsFor"],
                    "goals_against": entry["goalsAgainst"],
                    "goal_diff": entry["goalDifference"],
                    "points": entry["points"],
                })
            groups[group_name] = teams
        return groups


def get_fetcher() -> LiveDataFetcher:
    """Get a LiveDataFetcher instance, loading API key from environment."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return LiveDataFetcher()
