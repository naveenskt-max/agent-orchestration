from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import httpx
import random

app = FastAPI()

# Input Schema for text_analysis_agent
class TextAnalysisAgentInput(BaseModel):
    texts: List[str] = Field(..., description="Array of text strings to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform (themes, sentiment, summary)")

# Output Schema for text_analysis_agent
class TextAnalysisAgentOutput(BaseModel):
    insights: List[str]
    sentiment_score: float
    themes: List[str]

@app.post("/execute", response_model=TextAnalysisAgentOutput)
async def execute(request: TextAnalysisAgentInput):
    insights = []
    themes = []
    
    if request.analysis_type == "themes":
        themes = [f"theme_{i+1}" for i in range(random.randint(2, 5))]
    elif request.analysis_type == "summary":
        insights = [f"This is a mock summary of the text."]
    
    sentiment_score = round(random.uniform(-1.0, 1.0), 2)
    
    return TextAnalysisAgentOutput(insights=insights, sentiment_score=sentiment_score, themes=themes)

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": "text_analysis_agent"}

@app.on_event("startup")
async def register_agent():
    import os
    registry_host = os.getenv("REGISTRY_URL", "http://localhost:8000")
    registry_url = f"{registry_host}/register"
    agent_card = {
        "name": "text_analysis_agent",
        "description": "Analyzes text content to extract themes, sentiment, and key insights using NLP. Supports multiple analysis types including theme extraction, sentiment analysis, and summarization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of text strings to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["themes", "sentiment", "summary"],
                    "description": "Type of analysis to perform"
                }
            },
            "required": ["texts", "analysis_type"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key insights extracted from the text"
                },
                "sentiment_score": {
                    "type": "number",
                    "description": "Overall sentiment score (-1 to 1)"
                },
                "themes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Main themes identified in the text"
                }
            }
        },
        "endpoint": "http://text_analysis_agent:8003/execute"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(registry_url, json=agent_card)
            response.raise_for_status()
            print(f"Agent 'text_analysis_agent' registered successfully with registry.")
    except httpx.RequestError as e:
        print(f"Failed to register agent 'text_analysis_agent' with registry: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Failed to register agent 'text_analysis_agent' with registry, status code: {e.response.status_code}, response: {e.response.text}")
