# 🐳 Docker Setup Guide

## 🎯 Overview

This guide provides complete Docker setup for the AI Agent Orchestration Platform with observability, including all services, networking, and health checks.

## 📁 Project Structure

```
agent-orchestration/
├── docker-compose.yml          # Main orchestration file
├── docker-setup.sh            # Automated setup script
├── registry/                  # Agent Registry Service
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── planner/                   # Planner Agent Service
│   ├── Dockerfile
│   ├── main.py
│   ├── planner_agent.py
│   └── requirements.txt
├── executor/                  # Executor Service
│   ├── Dockerfile
│   ├── main.py
│   ├── executor.py
│   └── requirements.txt
├── observability/             # Observability Service
│   ├── Dockerfile
│   ├── main.py
│   ├── manager.py
│   └── requirements.txt
├── ui/                       # Streamlit Web UI
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── agents/                    # Specialist Agents
    ├── sales_data_agent/
    ├── news_search_agent/
    ├── text_analysis_agent/
    └── data_visualization_agent/
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd agent-orchestration

# Run the automated setup script
./docker-setup.sh
```

The script will:
- ✅ Check Docker installation
- ✅ Clean up previous containers
- ✅ Build all Docker images
- ✅ Start all services with health checks
- ✅ Wait for services to be healthy
- ✅ Display service URLs
- 🌐 Open browser automatically

### Option 2: Manual Setup

```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Service Configuration

### Port Mapping
| Service | Internal Port | External Port | Purpose |
|---------|---------------|---------------|---------|
| Registry | 8000 | 8000 | Agent registration/discovery |
| Planner | 8100 | 8100 | Goal decomposition & planning |
| Executor | 8200 | 8200 | Workflow execution |
| Observability | 8300 | 8300 | Metrics & tracing |
| Sales Data Agent | 8001 | 8001 | Sales data retrieval |
| News Search Agent | 8002 | 8002 | News article search |
| Text Analysis Agent | 8003 | 8003 | Text processing |
| Data Visualization Agent | 8004 | 8004 | Chart generation |
| Web UI | 8501 | 8501 | Main dashboard |

### Docker Networking
- **Network**: Custom bridge network `agent-network`
- **Service Discovery**: Services communicate using service names
- **Environment Variables**: Service URLs configured via environment

### Health Checks
All services include Docker health checks:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds  
- **Retries**: 3 attempts
- **Start Period**: 40 seconds

## 🏗️ Dockerfile Features

### Security
- **Non-root User**: All services run as `appuser`
- **Minimal Base**: Python 3.9 slim images
- **No Sensitive Data**: No secrets in images

### Performance
- **Layer Caching**: Requirements copied first for better caching
- **Multi-stage**: Optimized image sizes
- **Health Monitoring**: Built-in health checks

### Portability
- **Platform Independent**: Works on Linux, macOS, Windows
- **Docker Compose**: Orchestration for multi-service setup
- **Environment Config**: Flexible configuration via env vars

## 🌐 Access Points

### Main Dashboard
- **URL**: http://localhost:8501
- **Features**: Planning, Observability, Trace Viewer
- **Auto-refresh**: Real-time metrics updates

### API Endpoints
- **Registry**: http://localhost:8000
- **Planner**: http://localhost:8100  
- **Executor**: http://localhost:8200
- **Observability**: http://localhost:8300

### Agent Endpoints
- **Sales Data**: http://localhost:8001
- **News Search**: http://localhost:8002
- **Text Analysis**: http://localhost:8003
- **Data Visualization**: http://localhost:8004

## 📊 Service Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Dependency Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐    ┌──────────┐    ┌─────────────┐  │
│  │ Registry  │◄───┤ Planner   │◄───┤   Executor   │  │
│  │ (8000)   │    │ (8100)   │    │   (8200)    │  │
│  └─────────┘    └──────────┘    └─────────────┘  │
│         │                │                   │         │
│         ▼                ▼                   ▼         │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Agents (8001-8004)            │   │
│  │  sales_data  news_search  text_analysis  │   │
│  │  data_visualization                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────┐    ┌──────────────────────────┐   │
│  │ Observability │◄───┤   All Services         │   │
│  │   (8300)     │    │   (Metrics/Traces)     │   │
│  └─────────────────┘    └──────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Development Workflow

### Building Individual Services
```bash
# Build specific service
docker-compose build planner

# Build with no cache
docker-compose build --no-cache

# Build in parallel
docker-compose build --parallel
```

### Running Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d planner

# Start with logs
docker-compose up -f planner
```

### Debugging
```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f planner

# Execute command in container
docker-compose exec planner bash

# Inspect container
docker-compose ps
```

### Environment Configuration
```bash
# Override environment variables
docker-compose up -d --env-file .env

# Common environment variables:
REGISTRY_URL=http://registry:8000
PLANNER_URL=http://planner:8100
EXECUTOR_URL=http://executor:8200
OBSERVABILITY_URL=http://observability:8300
```

## 🔍 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep :8000
lsof -i :8000

# Solution: Change ports in docker-compose.yml
```

#### Service Not Starting
```bash
# Check service logs
docker-compose logs planner

# Check health status
docker-compose ps

# Restart specific service
docker-compose restart planner
```

#### Network Issues
```bash
# Check network configuration
docker network ls
docker network inspect agent-orchestration_agent-network

# Rebuild network
docker-compose down
docker network prune
docker-compose up -d
```

#### Memory Issues
```bash
# Check resource usage
docker stats

# Increase memory limits
docker-compose up -d --scale planner=1 --memory=2g
```

### Performance Optimization

#### Build Optimization
```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker-compose build

# Parallel builds
docker-compose build --parallel
```

#### Runtime Optimization
```bash
# Resource limits
docker-compose up -d --memory=4g --cpus=2

# Remove unused containers/images
docker system prune -a
```

## 📈 Monitoring

### Docker Health
```bash
# Check container health
docker-compose ps

# Detailed health information
docker inspect agent-orchestration_planner_1 | grep Health
```

### Resource Usage
```bash
# Real-time resource usage
docker stats

# Historical usage
docker stats --no-stream
```

### Log Management
```bash
# Rotate logs
docker-compose logs --tail=1000

# Export logs
docker-compose logs > platform.log

# Clean up old logs
docker system prune --volumes
```

## 🔒 Security Considerations

### Container Security
- **Non-root User**: All containers run as non-root user
- **Minimal Images**: Python slim base images
- **No Secrets**: No sensitive data in images
- **Read-only FS**: Consider read-only filesystem where possible

### Network Security
- **Isolated Network**: Custom bridge network
- **Port Mapping**: Only expose necessary ports
- **Internal Communication**: Services use internal network
- **Firewall**: Consider firewall rules for production

### Data Security
- **No Persistence**: No sensitive data persistence
- **Environment Variables**: Use for configuration
- **Health Checks**: No sensitive data in health endpoints
- **Logs**: Avoid logging sensitive information

## 🚀 Production Deployment

### Environment Variables
Create `.env` file for production:
```bash
# Production environment variables
REGISTRY_URL=https://registry.yourdomain.com
PLANNER_URL=https://planner.yourdomain.com
EXECUTOR_URL=https://executor.yourdomain.com
OBSERVABILITY_URL=https://observability.yourdomain.com

# Security
GOOGLE_API_KEY=your_api_key_here
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Docker Compose Production
```yaml
version: '3.8'

services:
  registry:
    image: your-registry:latest
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Scaling
```bash
# Scale specific services
docker-compose up -d --scale planner=2

# Load balancing with nginx
# Configure nginx to load balance between instances
```

## 📚 Additional Resources

### Docker Commands Reference
```bash
# Essential commands
docker-compose up -d          # Start services
docker-compose down            # Stop services
docker-compose ps             # Show status
docker-compose logs -f        # Follow logs
docker-compose exec service bash # Execute in container
docker-compose build          # Build images
docker-compose pull           # Pull images
docker-compose restart        # Restart services

# Advanced commands
docker-compose config        # Validate configuration
docker-compose top          # Show processes
docker-compose port service # Show port mapping
```

### Backup and Recovery
```bash
# Export configuration
docker-compose config > docker-compose-backup.yml

# Backup data volumes
docker run --rm -v agent-orchestration_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v agent-orchestration_data:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /data
```

## 🎯 Success Criteria

✅ **Platform Running**: All services healthy and accessible
✅ **UI Accessible**: Web interface loads at http://localhost:8501
✅ **Agents Registered**: All 4 agents appear in registry
✅ **Planning Working**: Can generate plans with gap analysis
✅ **Execution Working**: Can execute workflows successfully
✅ **Observability Working**: Metrics and traces visible in dashboard
✅ **Health Monitoring**: All services pass health checks
✅ **Networking**: Services communicate via Docker network
✅ **Resource Usage**: Reasonable memory and CPU consumption

## 🎉 Next Steps

Once Docker setup is complete:

1. **Explore the UI**: Navigate to http://localhost:8501
2. **Try Demo Goals**: Use example goals for testing
3. **Monitor Performance**: Check observability dashboard
4. **Review Traces**: Analyze execution patterns
5. **Customize**: Modify agents or add new ones
6. **Scale**: Consider production deployment options

Enjoy your fully containerized AI Agent Orchestration Platform! 🚀