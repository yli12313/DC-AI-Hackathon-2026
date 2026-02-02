# World Cup 2026 Prediction Workflow

Autonomous AI workflow that predicts 2026 World Cup outcomes through **API-driven data** and **interpretable scoring**. Choose a goal, run the workflow, and see top-five predictions with descriptions and reasons for each result.

<img width="383" height="430" alt="image" src="https://github.com/user-attachments/assets/a7f98757-cc1d-4bf9-b457-6687d3c57c73" />

## Features

- **Five prediction types**
  - **World Cup winner** — Teams ranked by FIFA ranking, historical performance, recent form, squad strength, and home advantage (hosts USA, Mexico, Canada get a bonus).
  - **Golden Ball** — Best player (forwards and midfielders) by honours (e.g. Ballon d'Or, World Cup Golden Ball), rating, and goals/assists.
  - **Golden Boot** — Top scorers by international goals (80%) and rating (20%).
  - **Golden Glove** — Goalkeepers by clean sheets (50%) and rating (50%).
  - **Young Player Award** — U21 standouts by age bonus, rating, goals, and assists.

- **Data sources**
  - **Wikipedia API**: Qualified teams (2026 FIFA World Cup qualification), FIFA Men's World Ranking, national team rosters and squad positions, individual player pages (honours, caps, goals), historical World Cup results (2014, 2018, 2022). Responses are cached under `data/cache/`.
  - **Curated fallbacks**: When the API returns empty or fails, built-in lists of teams and star players (with honours and stats) ensure predictions still run.

- **Interpretable results**
  - Each prediction shows a **description** (who they are, key stats) and a **reason** (how the algorithm scored them).
  - Country flags (crests) appear next to each team or player.
  - In the Select goal box, each prediction type has a short **bullet-list explanation**: where the data comes from, how the algorithm works, and how the prediction is made.

- **Workflow**
  - **Planning**: Goal is turned into a concrete plan (up to 10 steps).
  - **Execution**: Steps run in order; outputs are passed between steps and logged to memory.
  - **Memory**: JSON-based (`memory.json`) with goal, plan, execution log (step, action, result, timestamp), and final output.
  - **Reports**: Top-five results and metadata saved to `predictions/` (e.g. `world_cup_winner.json`, `player_predictions.json`).

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

Open **http://localhost:8000** in your browser.

1. **Select a prediction goal** (World Cup winner, Golden Ball, Golden Boot, Golden Glove, or Young Player). Read the bullet-list description for that goal.
2. Click **Run workflow**.
3. Watch **step-by-step execution** (current step, action, result).
4. View **results**: top five with country picture, description, reason, and probability. Use the report links for full JSON.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/plan` | Body: `{"goal": "..."}` — returns plan (up to 10 steps). |
| `POST` | `/api/execute` | Body: `{"goal": "..."}` — runs full workflow; returns status, memory, output. |
| `GET` | `/api/memory` | Current memory state (goal, plan, execution_log, final_output). |
| `POST` | `/api/reset` | Resets workflow and memory. |
| `GET` | `/api/report/{filename}` | Serves `predictions/world_cup_winner.json` or `player_predictions.json`. |
| `GET` | `/api/health` | Health check. |

## Project structure

```
backend/
  main.py            # FastAPI app, routes, serves frontend and static assets
  workflow_engine.py # plan(goal), execute(plan, goal), max 10 steps
  memory.py          # JSON memory (goal, plan, execution_log, final_output)
  tools.py           # fetch_*, calculate_*_predictions, enrich, report, save; team/player fallbacks
  wikipedia.py       # Wikipedia API client: qualified teams, FIFA ranking, rosters, player info,
                      # historical World Cup; caching; FLAG_BY_CODE, known players for awards
frontend/
  index.html         # Goal selector, goal description box, Run workflow, execution, results
  styles.css         # Layout, cards, result cards, bullet lists, crests
  app.js             # Goal descriptions (bullet lists), API calls, step animation, result render
data/
  cache/             # Wikipedia API cache (wiki_*.json), 24h TTL
predictions/         # world_cup_winner.json, player_predictions.json (after run)
memory.json          # Workflow memory (created in project root after run)
run.py               # Sets cwd and runs uvicorn
requirements.txt    # fastapi, uvicorn, pydantic, requests
```

## Data and algorithms

- **Team winner**: Weighted model — FIFA ranking 25%, historical performance 20%, recent form 25%, squad strength 20%, home advantage 10%. Data from Wikipedia (qualification, FIFA ranking, historical World Cup) and cached team info.
- **Golden Ball / Boot / Glove / Young Player**: Candidates from Wikipedia rosters (with position) and curated lists; player stats from Wikipedia player pages or known data. Each award has a dedicated scoring formula (honours+rating+goals for Golden Ball; goals+rating for Boot; clean sheets+rating for Glove; age bonus+rating+goals+assists for Young Player). Crests (country flags) are resolved from team name via a fallback map so every result shows the correct flag.

No API keys required. Wikipedia responses are cached under `data/cache/` to reduce requests and improve load times.
