from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import httpx
import random
from datetime import datetime, timedelta

app = FastAPI()

# Input Schema for news_search_agent
class NewsSearchAgentInput(BaseModel):
    keywords: List[str] = Field(..., description="Search keywords")
    date_range: str = Field(..., description="Date range for articles (e.g., 'last_week', 'last_month')")
    max_results: int = Field(10, description="Maximum number of articles to return")

# Output Schema for news_search_agent
class Article(BaseModel):
    title: str
    url: str
    snippet: str
    date: str

class NewsSearchAgentOutput(BaseModel):
    articles: List[Article]

@app.post("/execute", response_model=NewsSearchAgentOutput)
async def execute(request: NewsSearchAgentInput):
    articles = []
    for i in range(request.max_results):
        date = (datetime.now() - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
        title = f"Mock Article about {' '.join(request.keywords)} #{i+1}"
        url = f"http://mocknews.com/article/{random.randint(1000,9999)}"
        snippet = f"This is a mock snippet for the article titled '{title}'."
        articles.append(Article(title=title, url=url, snippet=snippet, date=date))
    
    return NewsSearchAgentOutput(articles=articles)

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": "news_search_agent"}

@app.on_event("startup")
async def register_agent():
    import os
    registry_host = os.getenv("REGISTRY_URL", "http://localhost:8000")
    registry_url = f"{registry_host}/register"
    agent_card = {
        "name": "news_search_agent",
        "description": "Searches web for recent news articles using keywords and date ranges. Returns structured article data including titles, URLs, and snippets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Search keywords (e.g., ['competitor', 'product launch'])"
                },
                "date_range": {
                    "type": "string",
                    "description": "Date range for articles (e.g., 'last_week', 'last_month')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of articles to return",
                    "default": 10
                }
            },
            "required": ["keywords", "date_range"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "snippet": {"type": "string"},
                            "date": {"type": "string"}
                        }
                    }
                }
            }
        },
        "endpoint": "http://news_search_agent:8002/execute"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(registry_url, json=agent_card)
            response.raise_for_status()
            print(f"Agent 'news_search_agent' registered successfully with registry.")
    except httpx.RequestError as e:
        print(f"Failed to register agent 'news_search_agent' with registry: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Failed to register agent 'news_search_agent' with registry, status code: {e.response.status_code}, response: {e.response.text}")
