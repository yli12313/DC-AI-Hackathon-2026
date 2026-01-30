# World Cup 2026 AI Prediction Engine

Autonomous AI workflow system with **advanced prediction algorithm** and **Wikipedia integration**.

## 🎯 What Makes It Special

### Advanced Multi-Factor Prediction Algorithm
```
Score = FIFA Ranking (25%) + FIFA Points (20%) + World Cup History (15%) + 
        Squad Rating (20%) + Confederation Strength (10%) + 
        Home Advantage (5%) + Recent Form (5%)
```

### Wikipedia Integration
- Fetches real team articles from Wikipedia
- Includes current squad rosters and player data
- Links to Wikipedia pages for each team/player
- Uses Wikimedia Commons for flag images

### Data Sources
- **Teams**: 20 World Cup teams with full statistics
- **Players**: Key players with ratings and positions
- **History**: World Cup winners from 2014-2022
- **Wikipedia**: Live articles and references

## Features

- **Advanced Prediction Algorithm**: Multi-factor scoring based on real data
- **Wikipedia Integration**: Fetches actual team articles and rosters
- **Autonomous Planning**: Converts goals into executable plans (max 10 steps)
- **Sequential Execution**: Runs steps in order with real-time progress display
- **Memory System**: Persists execution history and results
- **Demo-Ready UI**: Clean, animated interface for live presentations

## Supported Predictions

- World Cup Winner (with confidence scores)
- Golden Ball (Best Player)
- Golden Boot (Top Scorer)
- Golden Glove (Best Goalkeeper)
- Young Player Award

## Setup

### Run the Server

```bash
pip install -r requirements.txt
python run.py
```

### Open in Browser

Navigate to: http://localhost:8000

## How It Works

1. **Select Goal**: Choose a prediction type from the UI
2. **Generate Plan**: AI creates step-by-step execution plan
3. **Fetch Data**: 
   - Get team data from Wikipedia API
   - Retrieve squad rosters and player stats
   - Fetch historical World Cup results
4. **Calculate Predictions**: Use advanced multi-factor algorithm
5. **Store Memory**: Results persisted to JSON
6. **Display Results**: Predictions with confidence scores and Wikipedia links

## Prediction Algorithm Details

### Factors Used

| Factor | Weight | Description |
|--------|--------|-------------|
| FIFA Ranking | 25% | Current FIFA ranking position |
| FIFA Points | 20% | Total FIFA points |
| World Cup History | 15% | Previous wins and appearances |
| Squad Rating | 20% | Team quality (OVR) |
| Confederation | 10% | Regional strength multiplier |
| Home Advantage | 5% | USA/Canada/Mexico hosts |
| Recent Form | 5% | Last World Cup performance |

### Confidence Levels

- **Very High**: Top contender with strong fundamentals
- **High**: Strong candidate with multiple positive factors
- **Medium**: Balanced chances with some concerns
- **Low**: Underdog with potential for upsets
- **Speculative**: Based on limited data or projections

## Data Sources

### Team Data
- FIFA rankings and points
- World Cup appearances and wins
- Confederation membership
- Squad size and average age
- Key players and formations
- Wikipedia article links

### Player Data
- Position and nationality
- Goals and assists
- Player ratings
- Team crest images
- Wikipedia profile links

### Historical Data
- World Cup winners (2014-2022)
- Golden Boot, Ball, Glove winners
- Host nations and final scores

## Architecture

```
backend/
  ├── main.py              # FastAPI server
  ├── workflow_engine.py   # Core execution engine
  └── tools.py             # Wikipedia API + Advanced predictions

frontend/
  ├── index.html    # Main UI
  ├── styles.css    # Premium styling
  └── app.js        # Frontend logic

memory/
  └── workflow_memory.json  # Execution memory
```

## Wikipedia Integration

The system fetches real data from Wikipedia:
- Team descriptions and history
- Current squad information
- Player statistics
- Competition records

Example API call:
```python
tools.fetch_team_article("Argentina")
# Returns: Wikipedia extract, image, URL, and team info
```

## Troubleshooting

**No Data**: Check your internet connection (Wikipedia API required)

**Slow Response**: Wikipedia may be throttling requests (wait and retry)

**Missing Images**: Wikimedia Commons images may be temporarily unavailable

## Tech Stack

- Python + FastAPI (backend)
- HTML/CSS/JavaScript (frontend)
- Wikipedia API (free, no key required)
- JSON (memory storage)

---

Built for the DC AI Hackathon 2026 🏆
