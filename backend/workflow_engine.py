"""
Workflow Engine for World Cup 2026 Prediction

Converts user goal into an execution plan (up to 10 steps) and runs steps sequentially.
Passes outputs from step N to step N+1; logs each step to memory.
"""

from typing import Dict, List, Any, Optional

from pathlib import Path

from .memory import Memory
from .tools import Tools


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


class WorkflowEngine:
    """Plan and execute workflow with max 10 steps."""

    def __init__(self, max_steps: int = 10):
        self.max_steps = max_steps
        self.memory = Memory(memory_file=str(_project_root() / "memory.json"))
        self.tools = Tools()

    def _goal_type(self, goal: str) -> str:
        g = (goal or "").strip().lower()
        if "winner" in g and ("world cup" in g or "2026" in g):
            return "team_winner"
        if "golden ball" in g:
            return "golden_ball"
        if "golden boot" in g:
            return "golden_boot"
        if "golden glove" in g:
            return "golden_glove"
        if "young player" in g:
            return "young_player"
        return "team_winner"

    def plan(self, goal: str) -> List[str]:
        """
        Convert goal into a concrete execution plan with UP TO 10 steps.
        Each step is a short description string.
        """
        goal_type = self._goal_type(goal)
        if goal_type == "team_winner":
            steps = [
                "Fetch current FIFA rankings data",
                "Fetch historical World Cup performance data",
                "Analyze team form and recent match results",
                "Calculate predictive scores using weighted factors (FIFA 25%, Historical 20%, Form 25%, Squad 20%, Home 10%)",
                "Generate top 5 predictions with probabilities",
                "Create visualization data",
                "Generate report",
                "Save results to memory and file",
                "Format output for display",
            ]
        elif goal_type == "golden_ball":
            steps = [
                "Fetch forward statistics",
                "Fetch midfielder statistics",
                "Fetch historical Golden Ball winners",
                "Calculate player scores (goals + assists + ratings + team success)",
                "Rank top 5 candidates with probabilities",
                "Create visualization data",
                "Generate report",
                "Save results to file",
                "Format output for display",
            ]
        elif goal_type == "golden_boot":
            steps = [
                "Fetch forward and attacking player statistics",
                "Fetch historical Golden Boot / top scorer data",
                "Calculate scoring-based scores (goals + form + team style)",
                "Rank top 5 candidates with probabilities",
                "Create visualization data",
                "Generate report",
                "Save results to file",
                "Format output for display",
            ]
        elif goal_type == "golden_glove":
            steps = [
                "Fetch goalkeeper statistics",
                "Fetch historical Golden Glove winners",
                "Calculate keeper scores (clean sheets + saves + defensive strength)",
                "Rank top 5 candidates with probabilities",
                "Create visualization data",
                "Generate report",
                "Save results to file",
                "Format output for display",
            ]
        else:
            steps = [
                "Fetch young player (U21) statistics",
                "Fetch historical Young Player Award winners",
                "Calculate scores (age <21 + performance + potential)",
                "Rank top 5 candidates with probabilities",
                "Create visualization data",
                "Generate report",
                "Save results to file",
                "Format output for display",
            ]
        return steps[: self.max_steps]

    def execute(self, plan: List[str], goal: str) -> Dict[str, Any]:
        """
        Run each planned step in order. Pass outputs between steps.
        Log each step to memory (step number, action, result, timestamp).
        Return final_output; on error, set memory error and raise or return error state.
        """
        self.memory.start_workflow(goal, plan)
        context: Dict[str, Any] = {}
        goal_type = self._goal_type(goal)
        final_output: Dict[str, Any] = {}
        t = self.tools

        for i, step_desc in enumerate(plan[: self.max_steps], 1):
            step_num = i
            action = step_desc
            try:
                result_text, result_data = self._run_step(step_desc, goal_type, context)
                self.memory.log_step(step_num, action, result_text, result_data)
                if result_data is not None:
                    context["last"] = result_data
                    context[f"step_{step_num}"] = result_data
                    if isinstance(result_data, dict) and ("top5" in result_data or "predictions" in result_data):
                        context["predictions"] = result_data
                        final_output = result_data
            except Exception as e:
                self.memory.log_step(step_num, action, f"Error: {e}", None)
                self.memory.set_error(str(e))
                return {"status": "error", "memory": self.memory.get_state(), "error": str(e), "output": {}}

        self.memory.set_final_output(final_output)
        return {"status": "completed", "memory": self.memory.get_state(), "output": final_output}

    def _run_step(self, step_desc: str, goal_type: str, context: Dict[str, Any]) -> tuple:
        """Execute one step; return (result_summary_string, result_data_or_None)."""
        s = step_desc.lower()
        t = self.tools

        if "fifa ranking" in s:
            out = t.fetch_fifa_rankings()
            return out["result"], out
        if "historical" in s and "world cup" in s:
            out = t.fetch_historical_data("World Cup")
            return out["result"], out
        if "historical" in s and "golden" in s:
            out = t.fetch_historical_data("World Cup")
            return out["result"], out
        if "historical" in s and "young" in s:
            out = t.fetch_historical_data("World Cup")
            return out["result"], out
        if "analyze team form" in s or "team form" in s:
            teams = t.get_team_names()[:15]
            out = t.analyze_team_form(teams)
            return out["result"], out
        if "calculate predictive" in s or "weighted factors" in s:
            rankings = t.fetch_fifa_rankings()
            out = t.calculate_predictions(rankings, t.WEIGHTS_TEAM)
            return out["result"], out
        if "generate top 5" in s and goal_type == "team_winner":
            rankings = t.fetch_fifa_rankings()
            out = t.calculate_predictions(rankings, t.WEIGHTS_TEAM)
            return out["result"], out

        if goal_type == "golden_ball":
            if "forward" in s:
                out = t.fetch_player_stats("forwards")
                return out["result"], out
            if "midfielder" in s:
                out = t.fetch_player_stats("midfielders")
                return out["result"], out
            if "calculate player" in s or "rank top 5" in s:
                fwd = t.fetch_player_stats("forwards")
                mid = t.fetch_player_stats("midfielders")
                players = (fwd.get("data") or []) + (mid.get("data") or [])
                out = t.calculate_player_predictions(players, "golden_ball")
                return out["result"], out
        if goal_type == "golden_boot":
            if "forward" in s or "attacking" in s:
                out = t.fetch_player_stats("forwards")
                return out["result"], out
            if "calculate" in s and "scor" in s or "rank top 5" in s:
                fwd = t.fetch_player_stats("forwards")
                players = fwd.get("data") or []
                out = t.calculate_player_predictions(players, "golden_boot")
                return out["result"], out
        if goal_type == "golden_glove":
            if "goalkeeper" in s:
                out = t.fetch_player_stats("goalkeepers")
                return out["result"], out
            if "calculate" in s or "rank top 5" in s:
                gk = t.fetch_player_stats("goalkeepers")
                players = gk.get("data") or []
                out = t.calculate_player_predictions(players, "golden_glove")
                return out["result"], out
        if goal_type == "young_player":
            if "young" in s or "u21" in s:
                out = t.fetch_player_stats("young")
                return out["result"], out
            if "calculate" in s or "rank top 5" in s:
                y = t.fetch_player_stats("young")
                players = y.get("data") or []
                out = t.calculate_player_predictions(players, "young_player")
                return out["result"], out

        if "create visualization" in s:
            last = context.get("last") or {}
            out = t.create_visualization(last)
            return out["result"], out
        if "generate report" in s:
            pred = context.get("predictions") or context.get("last") or {}
            out = t.generate_report(pred)
            return out["result"], out
        if "save results" in s or "save to file" in s:
            pred = context.get("predictions") or context.get("last") or {}
            report = t.generate_report(pred).get("data") or pred
            fname = "world_cup_winner.json" if goal_type == "team_winner" else "player_predictions.json"
            out = t.save_to_file(fname, report)
            return out["result"], out
        if "format output" in s:
            return "Results ready for display", context.get("last")

        return "Step completed", None

    def get_memory(self) -> Dict[str, Any]:
        return self.memory.get_state()

    def reset(self) -> None:
        self.memory.reset()
