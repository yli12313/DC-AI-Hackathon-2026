"""
Memory System for Workflow Execution
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class Memory:
    """JSON-based memory system for workflow execution"""
    
    def __init__(self, memory_file: str = "memory/workflow_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(exist_ok=True)
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file or create new"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return self._create_empty_memory()
    
    def _create_empty_memory(self) -> Dict[str, Any]:
        """Create empty memory structure"""
        return {
            "goal": "",
            "plan": [],
            "execution_log": [],
            "final_output": {},
            "workflow_status": "idle",
            "created_at": None,
            "updated_at": None
        }
    
    def initialize_workflow(self, goal: str, plan: List[str]) -> Dict[str, Any]:
        """Initialize memory for a new workflow"""
        self.memory = {
            "goal": goal,
            "plan": plan,
            "execution_log": [],
            "final_output": {},
            "workflow_status": "running",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        self._save_memory()
        return self.memory
    
    def update_step(self, step_number: int, action: str, result: str, data: Any = None) -> Dict[str, Any]:
        """Update memory with step execution result"""
        step_log = {
            "step": step_number,
            "action": action,
            "result": result,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.memory["execution_log"].append(step_log)
        self.memory["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._save_memory()
        
        return step_log
    
    def set_final_output(self, output: Dict[str, Any]) -> None:
        """Set the final output of the workflow"""
        self.memory["final_output"] = output
        self.memory["workflow_status"] = "completed"
        self.memory["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._save_memory()
    
    def set_error(self, error_message: str) -> None:
        """Mark workflow as failed with error"""
        self.memory["workflow_status"] = "error"
        self.memory["error"] = error_message
        self.memory["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._save_memory()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current memory state"""
        return self.memory
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get full execution log"""
        return self.memory.get("execution_log", [])
    
    def get_step_count(self) -> int:
        """Get number of executed steps"""
        return len(self.memory.get("execution_log", []))
    
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return self.memory.get("workflow_status") == "completed"
    
    def reset(self) -> None:
        """Reset memory to empty state"""
        self.memory = self._create_empty_memory()
        self._save_memory()
    
    def _save_memory(self) -> None:
        """Save memory to file"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)
    
    def export_memory(self) -> str:
        """Export memory as formatted JSON string"""
        return json.dumps(self.memory, indent=2)
