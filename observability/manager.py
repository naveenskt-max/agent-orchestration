import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObservabilityManager:
    """Simple in-memory observability manager for MVP"""
    
    def __init__(self):
        # Metrics storage
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "latencies": deque(maxlen=1000),  # Keep last 1000 latencies
            "agent_invocations": defaultdict(int),
            "agent_success": defaultdict(int),
            "agent_errors": defaultdict(int),
            "agent_latencies": defaultdict(lambda: deque(maxlen=100)),
            "coverage_scores": deque(maxlen=100),
            "gap_detections": 0,
            "planning_attempts": 0,
            "active_traces": {},
            "completed_traces": deque(maxlen=100)  # Keep last 100 traces
        }
        
        # Event storage
        self.events = deque(maxlen=500)  # Keep last 500 events
        
        # Agent registry
        self.registered_agents = set()
        
    def generate_trace_id(self) -> str:
        """Generate a unique trace ID"""
        return str(uuid.uuid4())
    
    def start_trace(self, service: str, operation: str, goal: str = None, **attributes) -> str:
        """Start a new trace"""
        trace_id = self.generate_trace_id()
        
        trace_data = {
            "trace_id": trace_id,
            "service": service,
            "operation": operation,
            "goal": goal,
            "start_time": datetime.now(),
            "attributes": attributes,
            "spans": [],
            "status": "running"
        }
        
        self.metrics["active_traces"][trace_id] = trace_data
        
        # Log event
        self.log_event("trace_started", service, trace_id=trace_id, operation=operation, goal=goal)
        
        return trace_id
    
    def end_trace(self, trace_id: str, status: str = "success", **result_attributes):
        """End a trace and calculate metrics"""
        if trace_id not in self.metrics["active_traces"]:
            return
        
        trace = self.metrics["active_traces"][trace_id]
        trace["end_time"] = datetime.now()
        trace["status"] = status
        trace["result_attributes"] = result_attributes
        
        # Calculate duration
        duration_ms = (trace["end_time"] - trace["start_time"]).total_seconds() * 1000
        trace["duration_ms"] = duration_ms
        
        # Update metrics
        self.metrics["requests_total"] += 1
        self.metrics["latencies"].append(duration_ms)
        
        if status == "success":
            self.metrics["requests_success"] += 1
        else:
            self.metrics["requests_error"] += 1
        
        # Move to completed traces
        self.metrics["completed_traces"].append(trace)
        del self.metrics["active_traces"][trace_id]
        
        # Log event
        self.log_event("trace_completed", trace["service"], trace_id=trace_id, 
                     status=status, duration_ms=duration_ms)
        
        return trace
    
    def add_span(self, trace_id: str, operation: str, service: str, 
                 start_time: datetime = None, end_time: datetime = None, 
                 status: str = "success", **attributes):
        """Add a span to an existing trace"""
        if trace_id not in self.metrics["active_traces"]:
            return None
        
        if start_time is None:
            start_time = datetime.now()
        if end_time is None:
            end_time = datetime.now()
        
        span = {
            "operation": operation,
            "service": service,
            "start_time": start_time,
            "end_time": end_time,
            "duration_ms": (end_time - start_time).total_seconds() * 1000,
            "status": status,
            "attributes": attributes
        }
        
        trace = self.metrics["active_traces"][trace_id]
        trace["spans"].append(span)
        
        return span
    
    def log_agent_invocation(self, agent_name: str, trace_id: str = None, 
                          success: bool = True, latency_ms: float = None, **attributes):
        """Log agent invocation metrics"""
        self.metrics["agent_invocations"][agent_name] += 1
        
        if success:
            self.metrics["agent_success"][agent_name] += 1
        else:
            self.metrics["agent_errors"][agent_name] += 1
        
        if latency_ms is not None:
            self.metrics["agent_latencies"][agent_name].append(latency_ms)
        
        # Log event
        self.log_event("agent_invocation", "executor", trace_id=trace_id,
                     agent_name=agent_name, success=success, latency_ms=latency_ms)
    
    def log_plan_generation(self, trace_id: str, coverage: float, attempts: int, 
                         gap_detected: bool, **attributes):
        """Log planning metrics"""
        self.metrics["coverage_scores"].append(coverage)
        self.metrics["planning_attempts"] += attempts
        
        if gap_detected:
            self.metrics["gap_detections"] += 1
        
        # Log event
        self.log_event("plan_generated", "planner", trace_id=trace_id,
                     coverage=coverage, attempts=attempts, gap_detected=gap_detected)
    
    def log_gap_detection(self, trace_id: str, missing_capability: str, 
                        suggested_agent: Dict[str, Any]):
        """Log gap detection event"""
        self.log_event("gap_detected", "planner", trace_id=trace_id,
                     missing_capability=missing_capability, suggested_agent=suggested_agent)
    
    def log_agent_registration(self, agent_name: str, agent_info: Dict[str, Any]):
        """Log agent registration"""
        self.registered_agents.add(agent_name)
        self.log_event("agent_registered", "registry", agent_name=agent_name, agent_info=agent_info)
    
    def log_event(self, event_type: str, service: str, trace_id: str = None, **data):
        """Log a general event"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "service": service,
            "trace_id": trace_id,
            "data": data
        }
        
        self.events.append(event)
        
        # Also log to standard logger
        logger.info(f"OBSERVABILITY: {json.dumps(event)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        # Calculate derived metrics
        total_requests = self.metrics["requests_total"]
        success_rate = (self.metrics["requests_success"] / total_requests * 100) if total_requests > 0 else 0
        
        latencies = list(self.metrics["latencies"])
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
        
        coverage_scores = list(self.metrics["coverage_scores"])
        avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        
        gap_rate = (self.metrics["gap_detections"] / total_requests * 100) if total_requests > 0 else 0
        
        # Agent metrics
        agent_metrics = []
        for agent_name in self.registered_agents:
            invocations = self.metrics["agent_invocations"][agent_name]
            successes = self.metrics["agent_success"][agent_name]
            errors = self.metrics["agent_errors"][agent_name]
            agent_latencies = list(self.metrics["agent_latencies"][agent_name])
            avg_agent_latency = sum(agent_latencies) / len(agent_latencies) if agent_latencies else 0
            success_rate = (successes / invocations * 100) if invocations > 0 else 0
            
            agent_metrics.append({
                "name": agent_name,
                "invocations": invocations,
                "success_rate": success_rate,
                "avg_latency_ms": avg_agent_latency,
                "status": "registered"
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "requests_total": total_requests,
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "active_agents": len(self.registered_agents),
                "active_traces": len(self.metrics["active_traces"])
            },
            "planning_metrics": {
                "avg_coverage": avg_coverage,
                "gap_detection_rate": gap_rate,
                "total_planning_attempts": self.metrics["planning_attempts"]
            },
            "agent_metrics": agent_metrics,
            "recent_traces": list(self.metrics["completed_traces"])[-10:],  # Last 10 traces
            "recent_events": list(self.events)[-20:]  # Last 20 events
        }
    
    def get_trace_details(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific trace"""
        # Check active traces
        if trace_id in self.metrics["active_traces"]:
            return self.metrics["active_traces"][trace_id]
        
        # Check completed traces
        for trace in self.metrics["completed_traces"]:
            if trace["trace_id"] == trace_id:
                return trace
        
        return None

# Global instance
observability = ObservabilityManager()