from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from manager import observability
import json

app = FastAPI(title="Observability Service")

class MetricsResponse(BaseModel):
    timestamp: str
    system_metrics: Dict[str, Any]
    planning_metrics: Dict[str, Any]
    agent_metrics: List[Dict[str, Any]]
    recent_traces: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get current observability metrics"""
    try:
        metrics = observability.get_metrics()
        return MetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/traces")
async def list_traces(limit: int = 50):
    """List recent traces"""
    try:
        traces = list(observability.metrics["completed_traces"])[-limit:]
        return {"traces": traces, "total": len(traces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/traces/{trace_id}")
async def get_trace_details(trace_id: str):
    """Get detailed information about a specific trace"""
    try:
        trace = observability.get_trace_details(trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def list_events(limit: int = 100, event_type: Optional[str] = None):
    """List recent events"""
    try:
        events = list(observability.events)
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        # Return last N events
        events = events[-limit:]
        
        return {"events": events, "total": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def get_agent_performance():
    """Get performance metrics for all agents"""
    try:
        metrics = observability.get_metrics()
        return metrics["agent_metrics"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "observability"}

@app.post("/test-event")
async def create_test_event(event_type: str, data: Dict[str, Any]):
    """Create a test event for debugging"""
    try:
        observability.log_event(event_type, "test", **data)
        return {"message": "Test event created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))