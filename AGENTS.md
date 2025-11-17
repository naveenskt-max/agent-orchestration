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

### Naming Conventions
- Agent names: snake_case (e.g., `sales_data_agent`)
- Classes: PascalCase (e.g., `SalesDataAgentInput`)
- Endpoints: `/execute` for agents, `/register`, `/list_agents` for registry
- Docker services: snake_case matching directory names

### Agent Development
- All agents must have `/execute` POST endpoint
- Define input/output Pydantic models with Field descriptions
- Auto-register on startup using `@app.on_event("startup")`
- Use MCP-compatible JSON Schema in agent cards
- Port allocation: agents 8001-8099, services 8100-8999

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