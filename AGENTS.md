# Agent Orchestration Platform - Development Guidelines

## Build & Run Commands

```bash
# Start all services with Docker Compose
docker-compose up --build

# Start individual services (development)
cd registry && uvicorn main:app --port 8000 --reload
cd planner && uvicorn main:app --port 8100 --reload  
cd executor && uvicorn main:app --port 8200 --reload

# Start agents
cd agents/sales_data_agent && uvicorn main:app --port 8001 --reload
cd agents/news_search_agent && uvicorn main:app --port 8002 --reload
```

## Code Style Guidelines

### Imports & Structure
- Use FastAPI for all services with Pydantic models
- Import order: standard library → third-party → local modules
- Use `from pydantic import BaseModel, Field` for data models
- Use `httpx` for HTTP client requests
- Use `os.getenv()` for environment variables with sensible defaults

### Docker Configuration
- Base image: `python:3.9-slim` (not deprecated -buster variants)
- All services must have health check endpoints
- Use Docker service names for inter-service communication
- Environment variables are passed via docker-compose.yml from .env file

### Naming Conventions
- Agent names: snake_case (e.g., `sales_data_agent`)
- Classes: PascalCase (e.g., `SalesDataAgentInput`)
- Endpoints: `/execute` for agents, `/register`, `/list_agents` for registry
- Docker services: snake_case matching directory names

### Agent Development

**Required Endpoints:**
- `/execute` POST endpoint - Main agent execution
- `/health` GET endpoint - Returns `{"status": "ok", "agent": "agent_name"}`

**Registration Requirements:**
- Auto-register on startup using `@app.on_event("startup")`
- Use environment variable `REGISTRY_URL` (defaults to `http://localhost:8000`)
- Register endpoint using Docker service name: `http://agent_name:PORT/execute`
- Use MCP-compatible JSON Schema in agent cards
- Port allocation: agents 8001-8099, services 8100-8999

**Data Models:**
- Define input/output Pydantic models with Field descriptions
- Input models provide JSON Schema for MCP compatibility
- Output models enable gap analysis and type safety

### Error Handling
- Use HTTPException for FastAPI error responses
- Handle httpx.RequestError and HTTPStatusError separately
- Log registration failures with descriptive messages
- Executor includes retry logic: 3 attempts with exponential backoff
- Don't retry 4xx client errors, only 5xx server errors and network issues

### Testing
- No test framework currently configured
- Test endpoints manually with curl or FastAPI docs at /docs
- Observability test: `python test_observability.py`

### Observability
- Observability service runs on port 8300
- Metrics endpoint: `GET /metrics`
- Traces endpoint: `GET /traces`
- Events endpoint: `GET /events`
- Integrated into UI with dedicated "📊 Observability" tab
## Agent Registration Example

```python
import os
import httpx
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": "my_agent"}

@app.on_event("startup")
async def register_agent():
    registry_host = os.getenv("REGISTRY_URL", "http://localhost:8000")
    registry_url = f"{registry_host}/register"
    
    agent_card = {
        "name": "my_agent",
        "description": "Agent description",
        "inputSchema": {...},
        "outputSchema": {...},
        "endpoint": "http://my_agent:8001/execute"  # Docker service name
    }
    
    try:
        response = httpx.post(registry_url, json=agent_card, timeout=5.0)
        response.raise_for_status()
        print(f"✅ Registered my_agent with registry")
    except Exception as e:
        print(f"⚠️  Failed to register: {e}")
```

## Docker Networking Best Practices

**Service Names vs Localhost:**
- Inside Docker: Use service names (e.g., `http://registry:8000`)
- Outside Docker: Use localhost (e.g., `http://localhost:8000`)
- UI uses environment variables to support both contexts

**Health Checks:**
- All services must respond to `/health` with status 200
- Docker Compose uses health checks to enforce startup order
- Health checks prevent premature service-to-service calls

**Environment Variables:**
- Never hardcode `localhost` URLs in agent code
- Always use `os.getenv("REGISTRY_URL", "http://localhost:8000")`
- Allows same code to work in Docker and local development
