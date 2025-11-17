from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from planner_agent import planner_agent
import sys
import os
import time
import uuid
from datetime import datetime

# Simple observability implementation
class SimpleObservability:
    """Simple observability for planner service"""

    def __init__(self):
        self.traces = []

    def start_trace(self, service: str, operation: str, **kwargs):
        trace_id = str(uuid.uuid4())
        trace = {
            "trace_id": trace_id,
            "service": service,
            "operation": operation,
            "start_time": datetime.now(),
            "metadata": kwargs
        }
        self.traces.append(trace)
        return trace_id

    def end_trace(self, trace_id: str, status: str, **kwargs):
        for trace in self.traces:
            if trace["trace_id"] == trace_id:
                trace["end_time"] = datetime.now()
                trace["status"] = status
                trace["metadata"].update(kwargs)
                break

    def log_plan_generation(self, **kwargs):
        pass  # No-op for now

    def log_gap_detection(self, **kwargs):
        pass  # No-op for now

observability = SimpleObservability()

app = FastAPI()

class Goal(BaseModel):
    goal: str

@app.post("/plan")
async def create_plan(goal: Goal):
    # Start trace
    trace_id = observability.start_trace("planner", "plan_workflow", goal=goal.goal)
    
    try:
        start_time = time.time()
        plan = await planner_agent.generate_plan(goal.goal)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log planning metrics
        coverage = plan.get("coverage", 0)
        status = plan.get("status", "unknown")
        attempts = plan.get("alternative_approaches_tried", 1)
        gap_detected = status == "partial"
        
        observability.log_plan_generation(
            trace_id=trace_id,
            coverage=coverage,
            attempts=attempts,
            gap_detected=gap_detected
        )
        
        # Log gaps if detected
        if gap_detected and plan.get("gaps"):
            for gap in plan["gaps"]:
                missing_capability = gap.get("required_capability", "unknown")
                suggested_agent = gap.get("suggested_agent_card", {})
                observability.log_gap_detection(
                    trace_id=trace_id,
                    missing_capability=missing_capability,
                    suggested_agent=suggested_agent
                )
        
        # End trace
        observability.end_trace(
            trace_id=trace_id,
            status="success",
            coverage=coverage,
            gap_detected=gap_detected,
            duration_ms=duration_ms
        )
        
        return plan
        
    except Exception as e:
        # End trace with error
        observability.end_trace(
            trace_id=trace_id,
            status="error",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
