"""
FastAPI Server for World Cup Prediction Workflow
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from pathlib import Path
import uvicorn

from .workflow_engine import WorkflowEngine


# Initialize FastAPI app
app = FastAPI(
    title="World Cup 2026 Prediction Workflow",
    description="Autonomous AI workflow for World Cup predictions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow engine
engine = WorkflowEngine(max_steps=10)

# Get frontend directory path
frontend_dir = Path(__file__).parent.parent / "frontend"

# Mount static files for frontend
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# Pydantic models for API
class GoalRequest(BaseModel):
    goal: str


# Use more flexible models to avoid validation issues
class PlanStep(BaseModel):
    step: int
    action: str
    description: str


class PlanResponse(BaseModel):
    goal: str
    plan: List[PlanStep]
    total_steps: int


class ExecuteResponse(BaseModel):
    status: str
    memory: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None


class ResetResponse(BaseModel):
    status: str
    message: str


# API Routes
@app.get("/")
async def root():
    """Serve the main HTML page"""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": "World Cup 2026 Prediction Workflow",
        "version": "1.0.0",
        "status": "running",
        "message": "HTML file not found"
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "World Cup 2026 Prediction Workflow API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "GET /": "Main HTML page",
            "GET /api": "This info",
            "POST /api/plan": "Generate execution plan",
            "POST /api/execute": "Execute workflow",
            "GET /api/memory": "Get memory state",
            "POST /api/reset": "Reset workflow"
        }
    }


@app.post("/api/plan", response_model=PlanResponse)
async def create_plan(request: GoalRequest):
    """
    Create a workflow plan for a given goal.
    
    Returns a numbered plan with up to 10 steps.
    """
    if not request.goal or not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    
    plan = engine.create_plan(request.goal)
    
    # Convert to PlanStep models
    plan_steps = [PlanStep(**step) for step in plan]
    
    return PlanResponse(
        goal=request.goal,
        plan=plan_steps,
        total_steps=len(plan)
    )


@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_workflow(request: GoalRequest):
    """
    Execute the full workflow for a given goal.
    
    Creates a plan, executes up to 10 steps sequentially,
    and returns the final predictions.
    """
    if not request.goal or not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    
    # Create plan and execute
    plan = engine.create_plan(request.goal)
    result = engine.execute_plan(plan, request.goal)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Execution failed"))
    
    return ExecuteResponse(
        status=result["status"],
        memory=result["memory"],
        output=result["output"]
    )


@app.get("/api/memory")
async def get_memory() -> Dict[str, Any]:
    """
    Get the current memory state.
    
    Returns the execution log, current goal, and workflow status.
    """
    return engine.get_memory()


@app.post("/api/reset", response_model=ResetResponse)
async def reset_workflow():
    """
    Reset the workflow engine and memory.
    """
    engine.reset()
    return ResetResponse(
        status="success",
        message="Workflow engine reset successfully"
    )


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}


# Run server if executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
