from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union
import httpx
import random

app = FastAPI()

# Input Schema for data_visualization_agent
class DataVisualizationAgentInput(BaseModel):
    data: Union[Dict[str, Any], List[Any]] = Field(..., description="Data to visualize")
    chart_type: str = Field(..., description="Type of chart to create (line, bar, pie)")
    title: str = Field(..., description="Title for the chart")

# Output Schema for data_visualization_agent
class DataVisualizationAgentOutput(BaseModel):
    chart_url: str
    chart_type: str

@app.post("/execute", response_model=DataVisualizationAgentOutput)
async def execute(request: DataVisualizationAgentInput):
    chart_url = f"http://mockcharts.com/chart/{random.randint(1000,9999)}.png"
    return DataVisualizationAgentOutput(chart_url=chart_url, chart_type=request.chart_type)

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": "data_visualization_agent"}

@app.on_event("startup")
async def register_agent():
    import os
    registry_host = os.getenv("REGISTRY_URL", "http://localhost:8000")
    registry_url = f"{registry_host}/register"
    agent_card = {
        "name": "data_visualization_agent",
        "description": "Creates charts and graphs from structured data. Supports multiple chart types including line, bar, and pie charts with customizable titles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Data to visualize (object or array with numeric values)"
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["line", "bar", "pie"],
                    "description": "Type of chart to create"
                },
                "title": {
                    "type": "string",
                    "description": "Title for the chart"
                }
            },
            "required": ["data", "chart_type", "title"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "chart_url": {
                    "type": "string",
                    "description": "URL to the generated chart image"
                },
                "chart_type": {
                    "type": "string",
                    "description": "Type of chart that was created"
                }
            }
        },
        "endpoint": "http://data_visualization_agent:8004/execute"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(registry_url, json=agent_card)
            response.raise_for_status()
            print(f"Agent 'data_visualization_agent' registered successfully with registry.")
    except httpx.RequestError as e:
        print(f"Failed to register agent 'data_visualization_agent' with registry: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Failed to register agent 'data_visualization_agent' with registry, status code: {e.response.status_code}, response: {e.response.text}")
