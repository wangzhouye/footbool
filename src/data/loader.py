"""
Data loader — reads bundled CSV files into pandas DataFrames.
Uses @st.cache_data for Streamlit caching.
"""

import os
import pandas as pd

from ..utils.config import BUNDLED_DIR, GROUPS, TEAMS


def _resolve_path(filename: str) -> str:
    """Resolve path to a bundled CSV file."""
    return os.path.join(BUNDLED_DIR, filename)


def load_teams() -> pd.DataFrame:
    """Load team metadata. Falls back to config constants if CSV missing."""
    path = _resolve_path("wc2026_teams.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        # Fallback: build from config
        rows = []
        for name, info in TEAMS.items():
            group = None
            for g, teams in GROUPS.items():
                if name in teams:
                    group = g
                    break
            rows.append({
                "team": name,
                "code": info["code"],
                "group": group,
                "confederation": info["confederation"],
                "elo_seed": info["elo_seed"],
                "flag": info["flag"],
            })
        df = pd.DataFrame(rows)
    return df


def load_groups() -> pd.DataFrame:
    """Load group assignments."""
    path = _resolve_path("wc2026_groups.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    # Fallback
    rows = []
    for g, teams in GROUPS.items():
        rows.append({"group": g, "team1": teams[0], "team2": teams[1],
                      "team3": teams[2], "team4": teams[3]})
    return pd.DataFrame(rows)


def load_schedule() -> pd.DataFrame:
    """Load the 104-match schedule."""
    path = _resolve_path("wc2026_schedule.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["match_date"] = pd.to_datetime(df["match_date"])
        return df
    return pd.DataFrame()


def load_historical_matches() -> pd.DataFrame:
    """Load historical international matches."""
    path = _resolve_path("international_matches.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        return df
    return pd.DataFrame()


def load_all():
    """Load all data at once. Returns dict of DataFrames."""
    return {
        "teams": load_teams(),
        "groups": load_groups(),
        "schedule": load_schedule(),
        "historical": load_historical_matches(),
    }
