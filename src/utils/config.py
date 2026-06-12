"""
World Cup 2026 configuration constants.
48 teams, 12 groups (A-L), 4 teams per group.
"""

import os

# ── Paths ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
BUNDLED_DIR = os.path.join(DATA_DIR, "bundled")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# ── Tournament ──────────────────────────────────────
TOURNAMENT_NAME = "FIFA World Cup 2026"
HOSTS = ["USA", "Canada", "Mexico"]
N_TEAMS = 48
N_GROUPS = 12
TEAMS_PER_GROUP = 4
N_GROUP_MATCHES = 72  # 12 groups × 6 matches each
N_KNOCKOUT_MATCHES = 32  # R32(16) + R16(8) + QF(4) + SF(2) + 3rd(1) + Final(1)
TOTAL_MATCHES = 104

# ── Elo Configuration ───────────────────────────────
ELO_DEFAULT = 1500
ELO_HOME_ADVANTAGE = 100  # Elo points added for host nation at home
K_WORLD_CUP = 60
K_QUALIFIER = 40
K_FRIENDLY = 30

# Goal difference multiplier for Elo updates
def goal_diff_multiplier(gd: int) -> float:
    """Weight Elo update by goal margin."""
    gd = abs(gd)
    if gd <= 1:
        return 1.0
    elif gd == 2:
        return 1.5
    else:
        return (11.0 + gd) / 8.0  # 3→1.75, 4→1.875, 5→2.0

# ── Poisson Model Configuration ─────────────────────
LEAGUE_AVG_HOME_GOALS = 1.55
LEAGUE_AVG_AWAY_GOALS = 1.15
MAX_GOALS = 10  # Truncate Poisson PMF at 10 goals
ELO_TO_GOALS_FACTOR = 1.0 / 400.0  # 400 Elo points ≈ 1 goal
FORM_WEIGHT = 0.4  # Recent form weight (vs 0.6 Elo prior)
TIME_HALF_LIFE_YEARS = 4.0  # Match weight half-life

# ── Monte Carlo Configuration ───────────────────────
DEFAULT_N_SIMULATIONS = 10000
EXTRA_TIME_GOAL_REDUCTION = 0.70  # Goals drop ~30% in extra time

# ── Confederation Codes ─────────────────────────────
CONFEDERATIONS = {
    "UEFA": "Europe",
    "CONMEBOL": "South America",
    "CONCACAF": "North/Central America & Caribbean",
    "CAF": "Africa",
    "AFC": "Asia",
    "OFC": "Oceania",
}

# ── 2026 World Cup Groups (official draw, 12 groups × 4 teams) ────
GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# ── Team metadata ───────────────────────────────────
TEAMS = {
    "USA":           {"code": "USA", "confederation": "CONCACAF", "elo_seed": 1780, "flag": "🇺🇸"},
    "Canada":        {"code": "CAN", "confederation": "CONCACAF", "elo_seed": 1750, "flag": "🇨🇦"},
    "Mexico":        {"code": "MEX", "confederation": "CONCACAF", "elo_seed": 1800, "flag": "🇲🇽"},
    "Argentina":     {"code": "ARG", "confederation": "CONMEBOL", "elo_seed": 2120, "flag": "🇦🇷"},
    "Brazil":        {"code": "BRA", "confederation": "CONMEBOL", "elo_seed": 2080, "flag": "🇧🇷"},
    "Uruguay":       {"code": "URU", "confederation": "CONMEBOL", "elo_seed": 1900, "flag": "🇺🇾"},
    "Colombia":      {"code": "COL", "confederation": "CONMEBOL", "elo_seed": 1860, "flag": "🇨🇴"},
    "Peru":          {"code": "PER", "confederation": "CONMEBOL", "elo_seed": 1700, "flag": "🇵🇪"},
    "Chile":         {"code": "CHI", "confederation": "CONMEBOL", "elo_seed": 1720, "flag": "🇨🇱"},
    "Ecuador":       {"code": "ECU", "confederation": "CONMEBOL", "elo_seed": 1740, "flag": "🇪🇨"},
    "Paraguay":      {"code": "PAR", "confederation": "CONMEBOL", "elo_seed": 1680, "flag": "🇵🇾"},
    "France":        {"code": "FRA", "confederation": "UEFA", "elo_seed": 2100, "flag": "🇫🇷"},
    "England":       {"code": "ENG", "confederation": "UEFA", "elo_seed": 2020, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "Spain":         {"code": "ESP", "confederation": "UEFA", "elo_seed": 2050, "flag": "🇪🇸"},
    "Germany":       {"code": "GER", "confederation": "UEFA", "elo_seed": 1980, "flag": "🇩🇪"},
    "Portugal":      {"code": "POR", "confederation": "UEFA", "elo_seed": 2000, "flag": "🇵🇹"},
    "Netherlands":   {"code": "NED", "confederation": "UEFA", "elo_seed": 1960, "flag": "🇳🇱"},
    "Italy":         {"code": "ITA", "confederation": "UEFA", "elo_seed": 1950, "flag": "🇮🇹"},
    "Belgium":       {"code": "BEL", "confederation": "UEFA", "elo_seed": 1920, "flag": "🇧🇪"},
    "Croatia":       {"code": "CRO", "confederation": "UEFA", "elo_seed": 1940, "flag": "🇭🇷"},
    "Denmark":       {"code": "DEN", "confederation": "UEFA", "elo_seed": 1840, "flag": "🇩🇰"},
    "Switzerland":   {"code": "SUI", "confederation": "UEFA", "elo_seed": 1820, "flag": "🇨🇭"},
    "Sweden":        {"code": "SWE", "confederation": "UEFA", "elo_seed": 1760, "flag": "🇸🇪"},
    "Norway":        {"code": "NOR", "confederation": "UEFA", "elo_seed": 1780, "flag": "🇳🇴"},
    "Austria":       {"code": "AUT", "confederation": "UEFA", "elo_seed": 1800, "flag": "🇦🇹"},
    "Wales":         {"code": "WAL", "confederation": "UEFA", "elo_seed": 1700, "flag": "🏴󠁧󠁢󠁷󠁬󠁳󠁿"},
    "Serbia":        {"code": "SRB", "confederation": "UEFA", "elo_seed": 1740, "flag": "🇷🇸"},
    "Morocco":       {"code": "MAR", "confederation": "CAF", "elo_seed": 1880, "flag": "🇲🇦"},
    "Senegal":       {"code": "SEN", "confederation": "CAF", "elo_seed": 1820, "flag": "🇸🇳"},
    "Tunisia":       {"code": "TUN", "confederation": "CAF", "elo_seed": 1700, "flag": "🇹🇳"},
    "Algeria":       {"code": "ALG", "confederation": "CAF", "elo_seed": 1740, "flag": "🇩🇿"},
    "Egypt":         {"code": "EGY", "confederation": "CAF", "elo_seed": 1760, "flag": "🇪🇬"},
    "Nigeria":       {"code": "NGA", "confederation": "CAF", "elo_seed": 1720, "flag": "🇳🇬"},
    "Cameroon":      {"code": "CMR", "confederation": "CAF", "elo_seed": 1680, "flag": "🇨🇲"},
    "Ivory Coast":   {"code": "CIV", "confederation": "CAF", "elo_seed": 1700, "flag": "🇨🇮"},
    "South Africa":  {"code": "RSA", "confederation": "CAF", "elo_seed": 1640, "flag": "🇿🇦"},
    "Japan":         {"code": "JPN", "confederation": "AFC", "elo_seed": 1840, "flag": "🇯🇵"},
    "South Korea":   {"code": "KOR", "confederation": "AFC", "elo_seed": 1800, "flag": "🇰🇷"},
    "Iran":          {"code": "IRN", "confederation": "AFC", "elo_seed": 1760, "flag": "🇮🇷"},
    "Saudi Arabia":  {"code": "KSA", "confederation": "AFC", "elo_seed": 1700, "flag": "🇸🇦"},
    "Australia":     {"code": "AUS", "confederation": "AFC", "elo_seed": 1740, "flag": "🇦🇺"},
    "Qatar":         {"code": "QAT", "confederation": "AFC", "elo_seed": 1660, "flag": "🇶🇦"},
    "Iraq":          {"code": "IRQ", "confederation": "AFC", "elo_seed": 1640, "flag": "🇮🇶"},
    "United Arab Emirates": {"code": "UAE", "confederation": "AFC", "elo_seed": 1660, "flag": "🇦🇪"},
    "Costa Rica":    {"code": "CRC", "confederation": "CONCACAF", "elo_seed": 1680, "flag": "🇨🇷"},
    "Jamaica":       {"code": "JAM", "confederation": "CONCACAF", "elo_seed": 1660, "flag": "🇯🇲"},
    "Panama":        {"code": "PAN", "confederation": "CONCACAF", "elo_seed": 1640, "flag": "🇵🇦"},
    "New Zealand":   {"code": "NZL", "confederation": "OFC", "elo_seed": 1580, "flag": "🇳🇿"},
    # ── 竞彩实际出现但不在预设48队的球队 ──
    "Bosnia":        {"code": "BIH", "confederation": "UEFA", "elo_seed": 1680, "flag": "🇧🇦"},
    "Scotland":      {"code": "SCO", "confederation": "UEFA", "elo_seed": 1760, "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    "Turkey":        {"code": "TUR", "confederation": "UEFA", "elo_seed": 1780, "flag": "🇹🇷"},
    "Iceland":       {"code": "ISL", "confederation": "UEFA", "elo_seed": 1640, "flag": "🇮🇸"},
    "Greece":        {"code": "GRE", "confederation": "UEFA", "elo_seed": 1720, "flag": "🇬🇷"},
    "Ireland":       {"code": "IRL", "confederation": "UEFA", "elo_seed": 1660, "flag": "🇮🇪"},
    "Slovakia":      {"code": "SVK", "confederation": "UEFA", "elo_seed": 1700, "flag": "🇸🇰"},
    "Slovenia":      {"code": "SVN", "confederation": "UEFA", "elo_seed": 1680, "flag": "🇸🇮"},
    "Romania":       {"code": "ROU", "confederation": "UEFA", "elo_seed": 1700, "flag": "🇷🇴"},
    "Finland":       {"code": "FIN", "confederation": "UEFA", "elo_seed": 1640, "flag": "🇫🇮"},
    "Georgia":       {"code": "GEO", "confederation": "UEFA", "elo_seed": 1660, "flag": "🇬🇪"},
    "Albania":       {"code": "ALB", "confederation": "UEFA", "elo_seed": 1640, "flag": "🇦🇱"},
    "North Macedonia": {"code": "MKD", "confederation": "UEFA", "elo_seed": 1600, "flag": "🇲🇰"},
    "Bulgaria":      {"code": "BUL", "confederation": "UEFA", "elo_seed": 1620, "flag": "🇧🇬"},
    "Haiti":         {"code": "HAI", "confederation": "CONCACAF", "elo_seed": 1560, "flag": "🇭🇹"},
    "Curacao":       {"code": "CUW", "confederation": "CONCACAF", "elo_seed": 1520, "flag": "🇨🇼"},
    "Honduras":      {"code": "HON", "confederation": "CONCACAF", "elo_seed": 1580, "flag": "🇭🇳"},
    "Guatemala":     {"code": "GUA", "confederation": "CONCACAF", "elo_seed": 1540, "flag": "🇬🇹"},
    "Trinidad and Tobago": {"code": "TRI", "confederation": "CONCACAF", "elo_seed": 1520, "flag": "🇹🇹"},
    "Cape Verde":    {"code": "CPV", "confederation": "CAF", "elo_seed": 1600, "flag": "🇨🇻"},
    "Congo":         {"code": "CGO", "confederation": "CAF", "elo_seed": 1560, "flag": "🇨🇬"},
    "Ghana":         {"code": "GHA", "confederation": "CAF", "elo_seed": 1740, "flag": "🇬🇭"},
    "DR Congo":      {"code": "COD", "confederation": "CAF", "elo_seed": 1620, "flag": "🇨🇩"},
    "Guinea":        {"code": "GUI", "confederation": "CAF", "elo_seed": 1580, "flag": "🇬🇳"},
    "Mali":          {"code": "MLI", "confederation": "CAF", "elo_seed": 1620, "flag": "🇲🇱"},
    "Burkina Faso":  {"code": "BFA", "confederation": "CAF", "elo_seed": 1600, "flag": "🇧🇫"},
    "Zambia":        {"code": "ZAM", "confederation": "CAF", "elo_seed": 1560, "flag": "🇿🇲"},
    "Uganda":        {"code": "UGA", "confederation": "CAF", "elo_seed": 1520, "flag": "🇺🇬"},
    "Jordan":        {"code": "JOR", "confederation": "AFC", "elo_seed": 1580, "flag": "🇯🇴"},
    "Uzbekistan":    {"code": "UZB", "confederation": "AFC", "elo_seed": 1620, "flag": "🇺🇿"},
    "Oman":          {"code": "OMA", "confederation": "AFC", "elo_seed": 1560, "flag": "🇴🇲"},
    "Bahrain":       {"code": "BHR", "confederation": "AFC", "elo_seed": 1580, "flag": "🇧🇭"},
    "China":         {"code": "CHN", "confederation": "AFC", "elo_seed": 1560, "flag": "🇨🇳"},
    "Syria":         {"code": "SYR", "confederation": "AFC", "elo_seed": 1540, "flag": "🇸🇾"},
    "Thailand":      {"code": "THA", "confederation": "AFC", "elo_seed": 1520, "flag": "🇹🇭"},
    "Vietnam":       {"code": "VIE", "confederation": "AFC", "elo_seed": 1500, "flag": "🇻🇳"},
    "India":         {"code": "IND", "confederation": "AFC", "elo_seed": 1460, "flag": "🇮🇳"},
    "Indonesia":     {"code": "IDN", "confederation": "AFC", "elo_seed": 1480, "flag": "🇮🇩"},
    "North Korea":   {"code": "PRK", "confederation": "AFC", "elo_seed": 1580, "flag": "🇰🇵"},
    "Czech Republic": {"code": "CZE", "confederation": "UEFA", "elo_seed": 1780, "flag": "🇨🇿"},
}

# ── Knockout bracket slot mapping ───────────────────
# R32 matches: winner_group vs runner_up or best_third
# Standard 1-32 bracket with group-to-slot mappings
# Format: (slot_seed, description, source_description)
BRACKET_SLOTS = [
    (1,  "Winner Group A", "1A"),
    (2,  "Best 3rd Place 1", "3rd-1"),
    (3,  "Winner Group C", "1C"),
    (4,  "Runner-up Group B", "2B"),
    (5,  "Winner Group E", "1E"),
    (6,  "Best 3rd Place 2", "3rd-2"),
    (7,  "Winner Group G", "1G"),
    (8,  "Runner-up Group H", "2H"),
    (9,  "Winner Group I", "1I"),
    (10, "Best 3rd Place 3", "3rd-3"),
    (11, "Winner Group K", "1K"),
    (12, "Runner-up Group L", "2L"),
    (13, "Winner Group B", "1B"),
    (14, "Best 3rd Place 4", "3rd-4"),
    (15, "Winner Group D", "1D"),
    (16, "Runner-up Group A", "2A"),
    (17, "Winner Group F", "1F"),
    (18, "Best 3rd Place 5", "3rd-5"),
    (19, "Winner Group H", "1H"),
    (20, "Runner-up Group G", "2G"),
    (21, "Winner Group J", "1J"),
    (22, "Best 3rd Place 6", "3rd-6"),
    (23, "Winner Group L", "1L"),
    (24, "Runner-up Group K", "2K"),
    (25, "Runner-up Group C", "2C"),
    (26, "Best 3rd Place 7", "3rd-7"),
    (27, "Runner-up Group E", "2E"),
    (28, "Runner-up Group D", "2D"),
    (29, "Runner-up Group F", "2F"),
    (30, "Best 3rd Place 8", "3rd-8"),
    (31, "Runner-up Group I", "2I"),
    (32, "Runner-up Group J", "2J"),
]

# Knockout tree: each match is (match_name, slot_a, slot_b) → winner advances
KNOCKOUT_TREE = {
    # Round of 32 (16 matches)
    "R32-1":  (1, 2),   "R32-2":  (3, 4),   "R32-3":  (5, 6),   "R32-4":  (7, 8),
    "R32-5":  (9, 10),  "R32-6":  (11, 12), "R32-7":  (13, 14), "R32-8":  (15, 16),
    "R32-9":  (17, 18), "R32-10": (19, 20), "R32-11": (21, 22), "R32-12": (23, 24),
    "R32-13": (25, 26), "R32-14": (27, 28), "R32-15": (29, 30), "R32-16": (31, 32),
    # Round of 16 (8 matches)
    "R16-1": ("R32-1", "R32-2"),   "R16-2": ("R32-3", "R32-4"),
    "R16-3": ("R32-5", "R32-6"),   "R16-4": ("R32-7", "R32-8"),
    "R16-5": ("R32-9", "R32-10"),  "R16-6": ("R32-11", "R32-12"),
    "R16-7": ("R32-13", "R32-14"), "R16-8": ("R32-15", "R32-16"),
    # Quarterfinals (4 matches)
    "QF-1": ("R16-1", "R16-2"), "QF-2": ("R16-3", "R16-4"),
    "QF-3": ("R16-5", "R16-6"), "QF-4": ("R16-7", "R16-8"),
    # Semifinals (2 matches)
    "SF-1": ("QF-1", "QF-2"), "SF-2": ("QF-3", "QF-4"),
    # Third place (losers of semifinals)
    "3rd": ("L-SF-1", "L-SF-2"),
    # Final (winners of semifinals)
    "Final": ("SF-1", "SF-2"),
}

KNOCKOUT_ROUNDS = ["R32", "R16", "QF", "SF", "Final"]
