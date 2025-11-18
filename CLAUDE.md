# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An AI Agent Orchestration Platform that decomposes complex business goals into executable workflows using specialized agents. The key innovation is **intelligent gap analysis** - when the system can't complete a goal, it generates MCP-compatible Agent Card specifications describing exactly what agent to build next.

**Technology**: Python, FastAPI, Google ADK (Agent Development Kit), Gemini, Streamlit, Docker

## Architecture

### Three-Layer Microservices Architecture

**Core Services Layer:**
- **Registry (8000)**: Central agent registry with MCP-compatible Agent Cards
- **Planner (8100)**: Google ADK-powered multi-strategy goal decomposition with gap analysis
- **Executor (8200)**: Deterministic workflow execution with retry logic and context passing

**Agent Layer (4 specialist agents on ports 8001-8004):**
- Sales Data, News Search, Text Analysis, Data Visualization

**Support Layer:**
- **Observability (8300)**: Distributed tracing, metrics, event logging
- **UI (8501)**: Streamlit dashboard with planning, observability, trace viewer

### Key Architectural Pattern: MCP-Compatible Registration

All agents self-register with Registry on startup using MCP (Model Context Protocol) tool definition format. The Planner dynamically discovers available agents and converts them to Google ADK tools for goal decomposition.

**Flow**: Agents → Registry → Planner queries Registry → Gemini decomposes goal → Executor invokes agents sequentially

### Multi-Strategy Planning Innovation

The Planner attempts 4 different decomposition strategies (`planner/planner_agent.py:173-220`):
1. LINEAR workflow (sequential A→B→C→D)
2. EFFICIENT workflow (minimize steps)
3. COMPREHENSIVE workflow (maximize coverage)
4. CREATIVE workflow (novel combinations)

Each is scored on coverage (60%), efficiency (30%), composability (10%). Best scoring plan is selected.

### Gap Analysis & Agent Specification Generation

When coverage < 100%, the Planner uses Gemini to generate a complete Agent Card specification for the missing capability (`planner/planner_agent.py:288-367`), including:
- Required input/output schemas (inferred from workflow context)
- Implementation hints (libraries, complexity, effort)
- Human-readable description of the gap

This enables **incremental agent ecosystem growth** - users get actionable guidance on what to build next.

## Essential Commands

### Docker (Primary Method)
```bash
# One-command setup with health checks and browser auto-open
./docker-setup.sh

# Manual Docker
docker-compose up --build -d  # Start all 9 services
docker-compose logs -f        # View logs
docker-compose logs -f planner  # Service-specific logs
docker-compose down           # Stop all
docker-compose ps             # Check health
```

### Local Development
```bash
# Prerequisites: cp .env.template .env, then add GOOGLE_API_KEY

# Start in dependency order:
cd registry && uvicorn main:app --port 8000 --reload
cd planner && uvicorn main:app --port 8100 --reload
cd executor && uvicorn main:app --port 8200 --reload
cd observability && uvicorn main:app --port 8300 --reload
cd ui && streamlit run main.py --server.port 8501

# Start agents (any order after registry)
cd agents/sales_data_agent && uvicorn main:app --port 8001 --reload
cd agents/news_search_agent && uvicorn main:app --port 8002 --reload
cd agents/text_analysis_agent && uvicorn main:app --port 8003 --reload
cd agents/data_visualization_agent && uvicorn main:app --port 8004 --reload
```

### Testing & Debugging
```bash
# Health checks
curl http://localhost:{8000,8100,8200,8300}/health

# Test observability
python test_observability.py

# View registered agents
curl http://localhost:8000/list_agents

# Test planning
curl -X POST http://localhost:8100/plan \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create weekly sales report with competitor analysis"}'

# Direct agent testing
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Fetch sales for last week", "context": {}}'
```

## Critical Implementation Details

### Context Passing Between Agents
The Executor maintains workflow context across steps (`executor/context_manager.py`). Each agent receives:
```python
{
  "task": "Current step description",
  "context": {
    "step_1_output": {...},  # Output from step 1
    "step_2_output": {...}   # Output from step 2
    # etc.
  }
}
```

This enables data flow without shared state. Each step can access all upstream outputs.

### Retry Logic with Exponential Backoff
`executor/executor.py:85-128`: Max 3 retries with 1s, 2s, 4s delays
- **Retries**: Network errors, 5xx server errors
- **No retry**: 4xx client errors (fail immediately)
- Prevents cascade failures in distributed system

### Observability Integration
Every workflow execution creates a distributed trace (`executor/executor.py:130-213`):
- Trace ID tracks entire workflow
- Each step logs: agent, latency, status, output/error
- Accessible via UI observability tab (`http://localhost:8501`) or API `GET /traces`
- Real-time metrics, event filtering, and Gantt chart visualizations

### Planner System Instruction
`planner/planner_agent.py:123-159`: The system prompt instructs Gemini to:
1. Only use available agents from registry
2. Output structured JSON (no execution)
3. Estimate coverage percentage
4. List missing capabilities if < 100%

The Planner is an **architect, not an executor** - pure planning logic with no execution responsibility.

### MCP-Compatible Agent Card Schema
```python
{
  "name": "snake_case_name",  # Required
  "description": "Detailed capability description",  # For LLM understanding
  "endpoint": "http://host:port/execute",
  "inputSchema": {...},   # JSON Schema Draft-07 (MCP standard)
  "outputSchema": {...}   # Extension for gap analysis
}
```

Stored in `registry/models.py`. All agents must conform to this schema for registration.

## Environment Configuration

### Required
```bash
GOOGLE_API_KEY=your_key  # Get from https://makersuite.google.com/app/apikey
```

### Optional
```bash
GOOGLE_MODEL=gemini-2.5-flash  # Default (latest stable Flash model as of June 2025)
REGISTRY_URL=http://registry:8000
PLANNER_URL=http://planner:8100
EXECUTOR_URL=http://executor:8200
OBSERVABILITY_URL=http://observability:8300
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Note**: The planner makes 5 Gemini API calls per plan (4 decomposition strategies + 1 gap analysis), so the UI timeout is set to 120 seconds to allow sufficient time for completion.

**Security**: Never commit `.env` files. Use `.env.template` as starting point. See `SECURITY-IMPLEMENTATION.md` for enterprise practices.

## Service Dependencies

```
Registry (MUST start first)
  ↓
Agents (self-register) + Planner + Executor
  ↓
Observability
  ↓
UI (depends on all)
```

Docker health checks enforce this order automatically.

## Development Guidelines

See `AGENTS.md` for detailed guidelines on:
- Code style and naming conventions
- Agent development patterns
- Error handling standards
- Testing approaches

### Creating a New Agent

1. **Create structure**:
   ```bash
   mkdir -p agents/your_agent_name
   cd agents/your_agent_name
   ```

2. **Required files**:
   - `main.py`: FastAPI with `/execute` and `/health` endpoints
   - `requirements.txt`: Dependencies
   - `Dockerfile`: Use `python:3.9-slim` base image (not deprecated -buster variant)

3. **Agent must**:
   - Define Pydantic models with Field descriptions
   - Implement `/health` endpoint returning `{"status": "ok"}`
   - Auto-register on startup: `@app.on_event("startup")`
   - Use environment variable `REGISTRY_URL` for registry endpoint
   - Register with Docker service name (e.g., `http://agent_name:8001/execute`)
   - Use port 8001-8099
   - Accept `{"task": str, "context": dict}` in `/execute`

4. **Add to `docker-compose.yml`** with health check

5. **Reference implementation**: `agents/sales_data_agent/`

## Notable Code Locations

### Planner Logic
- `planner/planner_agent.py:61-121` - Main planning workflow
- `planner/planner_agent.py:161-226` - Multi-strategy decomposition
- `planner/planner_agent.py:256-286` - Scoring and selection
- `planner/planner_agent.py:288-367` - Gap analysis with Gemini

### Executor Logic
- `executor/executor.py:89-128` - Retry with exponential backoff
- `executor/executor.py:130-213` - Plan execution with observability
- `executor/context_manager.py` - Context management

### Registry
- `registry/models.py` - MCP AgentCard Pydantic model
- `registry/storage.py` - In-memory storage (not persisted)
- `registry/main.py` - FastAPI endpoints

### Observability
- `observability/manager.py` - Core implementation
- `observability/main.py` - API endpoints

### UI
- `ui/main.py` - Streamlit multi-tab interface

## Modifying System Behavior

### Change Planning Strategies
Edit `planner/planner_agent.py:173-178`:
```python
approaches = [
    "Your custom strategy description",
    # ...
]
```

### Adjust Scoring Weights
Edit `planner/planner_agent.py:266-282`:
```python
coverage_score = decomp['coverage'] * 0.6  # 60% weight
efficiency_score = (1.0 / max(len(decomp['steps']), 1)) * 0.3  # 30%
composability_score = 0.1  # 10%
```

### Modify Retry Behavior
Edit `executor/executor.py:85`:
```python
Executor(max_retries=3, base_delay=1.0)  # Adjust values
```

Line 107: Change exponential backoff formula (`2 ** attempt`)

## Architectural Decisions

**Why MCP-Compatible Format?**
Future-proof for MCP ecosystem. Phase 1 uses REST, but Agent Cards follow MCP tool definitions for easy MCP server wrapper addition later.

**Why Multi-Strategy Planning?**
LLMs produce different decompositions. Generating multiple and scoring increases chance of optimal plan and coverage.

**Why Deterministic Executor?**
No LLM in execution = predictable, repeatable workflows. Clear separation: planning (LLM) vs execution (deterministic).

**Why In-Memory Registry?**
Simplicity for MVP. Agents re-register on restart. Production would use persistent storage (Redis, PostgreSQL).

## Troubleshooting

### Common Issues

**Services won't start in Docker:**
- Ensure `.env` file exists with valid `GOOGLE_API_KEY`
- Check ports 8000-8004, 8100, 8200, 8300, 8501 are available
- Run `docker-compose down -v` to clean volumes, then rebuild

**Agent registration fails:**
- Verify Registry is healthy: `curl http://localhost:8000/health`
- Check agent can reach Registry (network connectivity in Docker)
- Review agent logs: `docker-compose logs -f sales_data_agent`

**Planner returns errors:**
- Verify `GOOGLE_API_KEY` is valid and has Gemini API access
- Check model name in `.env` matches available models (default: `gemini-2.0-flash-exp`)
- Ensure at least one agent is registered before planning

**Executor fails to invoke agents:**
- Verify agent endpoints are accessible from executor container
- Check agent health: `curl http://localhost:8001/health`
- Review execution trace in observability UI for detailed error messages

**UI shows "Service Unavailable":**
- Verify all dependencies are healthy: `docker-compose ps`
- Check service URLs in `docker-compose.yml` match internal network names
- Streamlit health check: `curl http://localhost:8501/_stcore/health`

## Related Documentation

- **AGENTS.md** - Development guidelines and code style
- **README.md** - Quick start and feature overview
- **prd.md** - Complete product requirements
- **DOCKER.md** - Docker setup guide
- **OBSERVABILITY.md** - Observability deep dive
- **SECURITY-IMPLEMENTATION.md** - API key security
- **ENVIRONMENT-SETUP.md** - Environment configuration
- **GIT.md** - Git workflow and version control
