import httpx
import asyncio
import time
import uuid
from datetime import datetime
from context_manager import context_manager

class SimpleObservability:
    """Simple observability for executor service"""
    
    def __init__(self):
        self.metrics = {
            "executions_total": 0,
            "executions_success": 0,
            "executions_failed": 0,
            "agent_invocations": {},
            "agent_latencies": {},
            "traces": []
        }
    
    def start_trace(self, goal: str = ""):
        trace_id = str(uuid.uuid4())
        trace = {
            "trace_id": trace_id,
            "goal": goal,
            "start_time": datetime.now(),
            "steps": [],
            "status": "running"
        }
        self.metrics["traces"].append(trace)
        return trace_id
    
    def end_trace(self, trace_id: str, status: str, final_output: dict = {}):
        for trace in self.metrics["traces"]:
            if trace["trace_id"] == trace_id:
                trace["end_time"] = datetime.now()
                trace["status"] = status
                trace["duration_ms"] = (trace["end_time"] - trace["start_time"]).total_seconds() * 1000
                if final_output is not None:
                    trace["final_output"] = final_output
                break
        
        self.metrics["executions_total"] += 1
        if status == "success":
            self.metrics["executions_success"] += 1
        else:
            self.metrics["executions_failed"] += 1
    
    def log_step(self, trace_id: str, step_num: int, agent_name: str, 
                status: str, latency_ms: float, output: dict = {}, error: str = ""):
        step_data = {
            "step": step_num,
            "agent": agent_name,
            "status": status,
            "latency_ms": latency_ms,
            "timestamp": datetime.now()
        }
        
        if output is not None:
            step_data["output"] = output
        if error is not None:
            step_data["error"] = error
        
        # Add to trace
        for trace in self.metrics["traces"]:
            if trace["trace_id"] == trace_id:
                trace["steps"].append(step_data)
                break
        
        # Update agent metrics
        if agent_name not in self.metrics["agent_invocations"]:
            self.metrics["agent_invocations"][agent_name] = 0
            self.metrics["agent_latencies"][agent_name] = []
        
        self.metrics["agent_invocations"][agent_name] += 1
        self.metrics["agent_latencies"][agent_name].append(latency_ms)
    
    def get_metrics(self):
        return self.metrics

# Global observability instance
obs = SimpleObservability()

class Executor:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_step(self, step: dict, agent_endpoint: str):
        context = context_manager.get_context()
        payload = {
            "task": step["task"],
            "context": context
        }
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(agent_endpoint, json=payload)
                    response.raise_for_status()
                    return response.json()
            
            except httpx.RequestError as e:
                last_error = f"Request failed: {str(e)}"
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay)
                    continue
            
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                # Don't retry client errors (4xx), only server errors (5xx)
                if 400 <= e.response.status_code < 500 and attempt < self.max_retries:
                    break
                elif attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
        
        raise Exception(f"Agent '{step['agent_name']}' failed after {self.max_retries + 1} attempts. Last error: {last_error}")

    async def execute_plan(self, plan: list[dict]):
        import time
        context_manager.clear_context()
        execution_trace = []
        
        # Start observability trace
        trace_id = obs.start_trace("workflow_execution")
        
        try:
            # First, get all agent endpoints from the registry
            registry_url = "http://localhost:8000/list_agents"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(registry_url)
                response.raise_for_status()
                registered_agents = {agent['name']: agent['endpoint'] for agent in response.json()}

            for step in plan:
                agent_name = step["agent_name"]
                if agent_name not in registered_agents:
                    raise Exception(f"Agent '{agent_name}' not found in registry.")
                
                agent_endpoint = registered_agents[agent_name]
                
                # Track execution time
                start_time = time.time()
                
                try:
                    output = await self.execute_step(step, agent_endpoint)
                    duration_ms = round((time.time() - start_time) * 1000)
                    
                    # Log to observability
                    obs.log_step(trace_id, step['step'], agent_name, "success", duration_ms, output=output)
                    
                    context_manager.add_to_context(f"step_{step['step']}_output", output)
                    execution_trace.append({
                        "step": step['step'],
                        "agent": agent_name,
                        "duration_ms": duration_ms,
                        "status": "success",
                        "output": output
                    })
                
                except Exception as e:
                    duration_ms = round((time.time() - start_time) * 1000)
                    
                    # Log failure to observability
                    obs.log_step(trace_id, step['step'], agent_name, "failed", duration_ms, error=str(e))
                    
                    execution_trace.append({
                        "step": step['step'],
                        "agent": agent_name,
                        "duration_ms": duration_ms,
                        "status": "failed",
                        "error": str(e)
                    })
                    
                    # End trace with failure
                    obs.end_trace(trace_id, "failed", {"execution_trace": execution_trace})
                    
                    # Stop execution on first failure
                    return {
                        "status": "failed",
                        "failed_step": step['step'],
                        "failed_agent": agent_name,
                        "error": str(e),
                        "execution_trace": execution_trace,
                        "partial_context": context_manager.get_context()
                    }
            
            # End trace with success
            final_output = context_manager.get_context()
            obs.end_trace(trace_id, "success", final_output)
            
            return {
                "status": "success",
                "final_output": final_output,
                "execution_trace": execution_trace
            }
        
        except Exception as e:
            # End trace with error
            obs.end_trace(trace_id, "error", {"error": str(e)})
            raise

executor = Executor(max_retries=3, base_delay=1.0)
