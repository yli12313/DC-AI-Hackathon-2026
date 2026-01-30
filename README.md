# 2026 World Cup Prediction Workflow System

Autonomous AI workflow that predicts 2026 World Cup outcomes through **up to 10 sequential execution steps**.

## Features

- **Goal input**: Choose one of 5 prediction goals (World Cup winner, Golden Ball, Golden Boot, Golden Glove, Young Player Award).
- **Planning**: Converts the goal into a concrete plan (up to 10 steps) with clear actions.
- **Execution**: Runs each step in order, passing outputs between steps and logging to memory.
- **Memory**: JSON-based memory (`memory.json`) with goal, plan, execution_log (step, action, result, timestamp), and final_output.
- **Tools**: `fetch_fifa_rankings`, `fetch_player_stats`, `fetch_historical_data`, `calculate_predictions`, `generate_report`, `save_to_file`, `create_visualization`.
- **Prediction logic**:
  - **Team winner**: FIFA ranking 25%, Historical 20%, Recent form 25%, Squad strength 20%, Home advantage 10%.
  - **Individual awards**: Golden Ball (goals + assists + ratings), Golden Boot (goals), Golden Glove (clean sheets + saves), Young Player (U21 + performance).

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

Open **http://localhost:8000** in your browser.

1. Select a prediction goal (buttons).
2. Click **Run Workflow**.
3. Watch step-by-step execution (current step N/10, action, result).
4. View final results: top 3–5 predictions with confidence %, key factors, and links to report files.

## API

- `POST /api/plan` — Body: `{"goal": "..."}` → returns plan (up to 10 steps).
- `POST /api/execute` — Body: `{"goal": "..."}` → runs workflow, returns status, memory, output.
- `GET /api/memory` — Returns current memory state.
- `POST /api/reset` — Resets workflow and memory.
- `GET /api/report/{filename}` — Serves `predictions/world_cup_winner.json` or `player_predictions.json`.

## Project structure

```
backend/
  main.py           # FastAPI app, routes, serve UI
  workflow_engine.py # plan(goal), execute(plan, goal), max 10 steps
  memory.py         # JSON memory (goal, plan, execution_log, final_output)
  tools.py          # fetch_*, calculate_predictions, generate_report, save_to_file, create_visualization
frontend/
  index.html        # Goal selector, Run Workflow, step display, results panel
  styles.css
  app.js
memory.json         # Persisted after run (created in project root)
predictions/        # world_cup_winner.json, player_predictions.json
run.py
requirements.txt
```

## Data

Team and player data is built-in (no API key required). You can extend `backend/tools.py` to use Wikipedia or other APIs for live data.
