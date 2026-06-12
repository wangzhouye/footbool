# 🏆 World Cup 2026 Prediction Tool

A data-driven World Cup prediction application with interactive visualizations. Predicts match outcomes (win/draw/loss probabilities), expected goals, and full tournament results using **Elo ratings** + **Poisson goal models** + **Monte Carlo simulations**.

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Configure live data API

Register for a free API key at [football-data.org](https://www.football-data.org/client/register), then:

```bash
cp .env.example .env
# Edit .env and add your API key: FOOTBALL_DATA_API_KEY=your_key
```

The app works fully offline using bundled historical data — the API key is only needed for live match results.

### 3. Launch the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## 📊 Features

| Page | Description |
|------|-------------|
| **🏠 Home Dashboard** | Today's matches, championship odds, group overview |
| **⚽ Match Predictor** | Select two teams → win/draw/loss %, expected goals, scoreline heatmap |
| **🏟️ Group Stage** | Group-by-group standings, advancement probabilities, match predictions |
| **🏆 Knockout Bracket** | Full 32-team bracket with simulated results |
| **📈 Team Analysis** | Elo history, strength radar chart, recent form, tournament prospects |
| **🎲 Simulation** | Run Monte Carlo simulations (100–10,000) for championship odds |
| **💰 Betting Tips** | Value analysis combining model predictions with live odds from China Sports Lottery |

## 🔬 Prediction Model

### Three-Layer Architecture

1. **Elo Rating Engine** — Team strength based on historical results. K-factor varies by tournament importance. Goal-difference weighting rewards dominant wins.

2. **Poisson Goal Model** — Dixon-Coles adjusted Poisson distribution models exact scorelines. Attack/defense strengths blend Elo prior (60%) with recent form (40%). Time-weighted with 4-year half-life.

3. **Monte Carlo Simulator** — Runs N full tournament simulations:
   - Group stage: 72 matches, top 2 + 8 best 3rd → R32
   - Knockout: R32 → R16 → QF → SF → Final
   - Extra time & penalties for tied knockout matches

## 📁 Project Structure

```
footbool/
├── app.py                          # Streamlit entry point
├── pages/
│   ├── 01_Match_Predictor.py       # Single match prediction
│   ├── 02_Group_Stage.py           # Group stage analysis
│   ├── 03_Knockout_Bracket.py      # Knockout bracket
│   ├── 04_Team_Analysis.py         # Team deep dive
│   ├── 05_Simulation.py            # Monte Carlo simulation
│   └── 06_Betting_Tips.py          # Betting value analysis
├── src/
│   ├── data/
│   │   ├── loader.py               # CSV data loading
│   │   ├── preprocessor.py         # Feature engineering
│   │   ├── live_fetcher.py         # Live API client
│   │   └── sporttery_scraper.py    # China Sports Lottery odds scraper
│   ├── models/
│   │   ├── elo.py                  # Elo rating engine
│   │   ├── poisson_model.py        # Poisson goal model
│   │   ├── predictor.py            # Unified prediction interface
│   │   ├── monte_carlo.py          # Tournament simulator
│   │   └── value_analyzer.py       # EV/Kelly betting value calculator
│   └── utils/
│       ├── config.py               # Constants & configuration
│       ├── tournament.py           # Tournament structure
│       └── viz_helpers.py          # Plotly chart builders
├── data/bundled/                   # Bundled CSV data
├── requirements.txt
├── Procfile                        # Deployment config
└── README.md
```

## 🎯 Usage Tips

- **Match Predictor**: Best for single-match analysis. See the scoreline heatmap for most likely exact scores.
- **Simulation**: Start with 1000 simulations for a quick overview. Use 10,000 for more stable probabilities.
- **Team Analysis**: Use comparison mode to overlay two teams on the radar chart.
- **Group Stage**: Simulate each group independently to see advancement odds.

## ⚠️ Disclaimer

This tool is for **educational and entertainment purposes only**. Predictions are probabilistic estimates based on historical data — they do not guarantee future outcomes. Not for gambling or betting purposes.

## 📄 License

MIT License — see LICENSE file for details.
