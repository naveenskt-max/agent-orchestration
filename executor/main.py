from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from executor import Executor, obs

app = FastAPI()

class Plan(BaseModel):
    plan: List[Dict[str, Any]]
    max_retries: Optional[int] = Field(3, description="Maximum retry attempts per step")
    base_delay: Optional[float] = Field(1.0, description="Base delay for exponential backoff (seconds)")

@app.post("/execute_workflow")
async def execute_workflow(plan: Plan):
    try:
        # Create executor with custom retry settings
        executor = Executor(
            max_retries=plan.max_retries or 3,
            base_delay=plan.base_delay or 1.0
        )
        result = await executor.execute_plan(plan.plan)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get executor observability metrics"""
    try:
        return obs.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
