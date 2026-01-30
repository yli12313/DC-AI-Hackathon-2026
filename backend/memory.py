"""
Memory System for World Cup 2026 Prediction Workflow

Stores goal, plan, execution_log (step, action, result, timestamp), final_output.
Persists to memory.json.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class Memory:
    """JSON-based memory for workflow execution."""

    def __init__(self, memory_file: str = "memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._empty()

    def _empty(self) -> Dict[str, Any]:
        return {
            "goal": "",
            "plan": [],
            "execution_log": [],
            "final_output": {},
            "workflow_status": "idle",
            "updated_at": None,
        }

    def start_workflow(self, goal: str, plan: List[str]) -> None:
        """Initialize for a new workflow run."""
        self.memory = {
            "goal": goal,
            "plan": plan,
            "execution_log": [],
            "final_output": {},
            "workflow_status": "running",
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        self._save()

    def log_step(self, step: int, action: str, result: str, data: Any = None) -> None:
        """Append one execution step to the log."""
        entry = {
            "step": step,
            "action": action,
            "result": result,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if data is not None:
            entry["data"] = data
        self.memory.setdefault("execution_log", []).append(entry)
        self.memory["updated_at"] = entry["timestamp"]
        self._save()

    def set_final_output(self, output: Dict[str, Any]) -> None:
        """Store final predictions and mark workflow complete."""
        self.memory["final_output"] = output
        self.memory["workflow_status"] = "completed"
        self.memory["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self._save()

    def set_error(self, message: str) -> None:
        """Mark workflow as failed."""
        self.memory["workflow_status"] = "error"
        self.memory["error"] = message
        self.memory["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self._save()

    def get_state(self) -> Dict[str, Any]:
        """Return full memory state."""
        return dict(self.memory)

    def reset(self) -> None:
        """Clear memory to initial state."""
        self.memory = self._empty()
        self._save()

    def _save(self) -> None:
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)
