# AI Agent Orchestration Platform

An intelligent workflow planning and execution system with gap analysis and comprehensive observability.

## 🎯 Features

- **🧠 Intelligent Planning**: Multi-strategy decomposition using Google ADK
- **🚧 Gap Analysis**: Identifies missing capabilities and suggests implementations
- **⚡ Robust Execution**: Retry logic with exponential backoff
- **📊 Observability**: Real-time metrics, tracing, and event logging
- **🎨 Professional UI**: Streamlit dashboard with planning, observability, and trace viewer
- **🐳 Docker Ready**: Complete containerization with health checks

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Port 8501)              │
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Planning    │  │   Observability     │  │
│  │   Tab         │  │   Tab              │  │
│  └──────┬───────┘  └──────────┬─────────┘  │
│         │                           │           │
└─────────┼───────────────────────────┼───────────┘
          │                           │
          ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer                   │
│  ┌──────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │   Planner    │  │ Executor  │  │Observability│  │
│  │   (8100)    │  │  (8200)   │  │   (8300)    │  │
│  └──────┬───────┘  └──────┬─────┘  └──────┬───────┘  │
│         │                   │              │           │
└─────────┼───────────────────┼──────────────┼───────────┘
          │                   │              │           │
          ▼                   ▼              ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Agent Registry (8000)               │
│  ┌─────────────────────────────────────────────┐     │
│  │    Agent Registration & Discovery        │     │
│  │  ┌─────────┐  ┌─────────────────┐   │     │
│  │  │   Sales  │  │   News Search  │   │     │
│  │  │   Agent  │  │   Agent        │   │     │
│  │  │ (8001)   │  │ (8002)        │   │     │
│  │  └─────────┘  └─────────────────┘   │     │
│  │  ┌─────────┐  ┌─────────────────┐   │     │
│  │  │   Text   │  │   Data Visual- │   │     │
│  │  │Analysis  │  │   ization     │   │     │
│  │  │  Agent  │  │   Agent        │   │     │
│  │  │ (8003)   │  │ (8004)        │   │     │
│  │  └─────────┘  └─────────────────┘   │     │
│  └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git (for version control)

### One-Command Setup
```bash
# Clone the repository
git clone <repository-url>
cd agent-orchestration

# Run the automated setup
./docker-setup.sh
```

This will:
- ✅ Build all Docker images
- ✅ Start all 9 services
- ✅ Wait for services to be healthy
- ✅ Display access URLs
- 🌐 Auto-open browser to dashboard

### Manual Setup
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🌐 Access Points

| Service | URL | Description |
|----------|-----|-------------|
| **🖥️ Main Dashboard** | http://localhost:8501 | Planning, Observability, Trace Viewer |
| **📋 Agent Registry** | http://localhost:8000 | Agent registration and discovery API |
| **🧠 Planner Service** | http://localhost:8100 | Goal decomposition and planning API |
| **⚡ Executor Service** | http://localhost:8200 | Workflow execution API |
| **📊 Observability** | http://localhost:8300 | Metrics, traces, and events API |
| **🤖 Sales Agent** | http://localhost:8001 | Sales data retrieval |
| **📰 News Agent** | http://localhost:8002 | News article search |
| **📝 Text Agent** | http://localhost:8003 | Text analysis and processing |
| **📈 Visualization Agent** | http://localhost:8004 | Chart and graph generation |

## 🎯 Demo Workflow

1. **Open Dashboard**: Navigate to http://localhost:8501
2. **Generate Plan**: Use "Create weekly sales intelligence report with competitor analysis"
3. **Review Gaps**: See 80% coverage with executive_report_agent missing
4. **Execute Workflow**: Run achievable plan steps
5. **Monitor Performance**: Check observability tab for metrics and traces
6. **Analyze Results**: View execution timeline and agent performance

## 📊 Key Capabilities

### Intelligent Planning
- Multi-strategy decomposition (3-4 attempts)
- Coverage calculation and gap detection
- Agent specification generation for missing capabilities
- MCP-compatible agent cards

### Robust Execution
- Sequential workflow execution
- Retry logic with exponential backoff
- Context passing between steps
- Error handling and partial execution

### Comprehensive Observability
- Real-time system metrics
- Distributed tracing with timelines
- Agent performance analytics
- Event logging and filtering
- Interactive visualizations

### Professional UI
- Multi-tab interface (Planning, Observability, Trace Viewer)
- Real-time updates and auto-refresh
- Interactive charts and Gantt timelines
- Service health monitoring

## 🐳 Docker Features

- **Production Ready**: Security best practices, health checks
- **Networking**: Internal service communication
- **Monitoring**: Built-in health endpoints
- **Scalable**: Easy service scaling and load balancing
- **Portable**: Works on Linux, macOS, Windows

## 📚 Documentation

- **README.md**: Main project documentation
- **AGENTS.md**: Development guidelines for agents
- **DOCKER.md**: Complete Docker setup guide
- **OBSERVABILITY.md**: Observability system documentation
- **prd.md**: Product requirements document

## 🔧 Development

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run individual services
cd registry && uvicorn main:app --port 8000 --reload
cd planner && uvicorn main:app --port 8100 --reload
cd executor && uvicorn main:app --port 8200 --reload
cd observability && uvicorn main:app --port 8300 --reload
cd ui && streamlit run main.py --server.port 8501
```

### Testing
```bash
# Test observability system
python test_observability.py

# Test individual services
curl http://localhost:8000/health
curl http://localhost:8100/health
curl http://localhost:8200/health
curl http://localhost:8300/health
```

## 🎊 Success Metrics

✅ **Complete Platform**: All services integrated and working
✅ **Intelligent Planning**: Multi-strategy decomposition with gap analysis
✅ **Robust Execution**: Retry logic and error handling
✅ **Observability**: Real-time metrics and distributed tracing
✅ **Professional UI**: Streamlit dashboard with rich visualizations
✅ **Docker Ready**: Production-grade containerization
✅ **Documentation**: Comprehensive guides and API documentation

## 🚀 Next Steps

1. **Explore**: Try different goals and workflow combinations
2. **Monitor**: Use observability to optimize performance
3. **Extend**: Add new agents for missing capabilities
4. **Scale**: Consider production deployment options
5. **Contribute**: Enhance features and fix issues

---

**Built with FastAPI, Google ADK, Streamlit, and Docker** 🚀