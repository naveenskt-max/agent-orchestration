#!/bin/bash

# AI Agent Orchestration Platform - Docker Setup Script
# This script sets up and runs the complete platform with Docker

set -e

echo "🤖 AI Agent Orchestration Platform - Docker Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_header "🔧 Step 1: Cleaning up previous containers..."
print_status "Stopping and removing existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

print_header "🏗️ Step 2: Building Docker images..."
print_status "Building all services (this may take a few minutes)..."
docker-compose build --no-cache

print_header "🚀 Step 3: Starting services..."
print_status "Starting all platform services..."
docker-compose up -d

print_header "⏳ Step 4: Waiting for services to be healthy..."
print_status "Waiting for registry service..."
sleep 10

# Wait for services to be healthy
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    print_status "Health check attempt $attempt/$max_attempts..."
    
    # Check if all services are healthy
    all_healthy=true
    
    # Check registry
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_status "✅ Registry is healthy"
    else
        print_warning "⏳ Registry not ready yet..."
        all_healthy=false
    fi
    
    # Check planner
    if curl -f http://localhost:8100/health &>/dev/null; then
        print_status "✅ Planner is healthy"
    else
        print_warning "⏳ Planner not ready yet..."
        all_healthy=false
    fi
    
    # Check executor
    if curl -f http://localhost:8200/health &>/dev/null; then
        print_status "✅ Executor is healthy"
    else
        print_warning "⏳ Executor not ready yet..."
        all_healthy=false
    fi
    
    # Check observability
    if curl -f http://localhost:8300/health &>/dev/null; then
        print_status "✅ Observability is healthy"
    else
        print_warning "⏳ Observability not ready yet..."
        all_healthy=false
    fi
    
    # Check agents
    if curl -f http://localhost:8001/health &>/dev/null; then
        print_status "✅ Sales Data Agent is healthy"
    else
        print_warning "⏳ Sales Data Agent not ready yet..."
        all_healthy=false
    fi
    
    if curl -f http://localhost:8002/health &>/dev/null; then
        print_status "✅ News Search Agent is healthy"
    else
        print_warning "⏳ News Search Agent not ready yet..."
        all_healthy=false
    fi
    
    if curl -f http://localhost:8003/health &>/dev/null; then
        print_status "✅ Text Analysis Agent is healthy"
    else
        print_warning "⏳ Text Analysis Agent not ready yet..."
        all_healthy=false
    fi
    
    if curl -f http://localhost:8004/health &>/dev/null; then
        print_status "✅ Data Visualization Agent is healthy"
    else
        print_warning "⏳ Data Visualization Agent not ready yet..."
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        print_status "🎉 All services are healthy!"
        break
    fi
    
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    print_error "❌ Services did not become healthy within expected time."
    print_status "Check logs with: docker-compose logs"
    exit 1
fi

print_header "🌐 Step 5: Service URLs"
echo ""
print_status "📋 Agent Registry:        http://localhost:8000"
print_status "🧠 Planner Service:       http://localhost:8100"
print_status "⚡ Executor Service:      http://localhost:8200"
print_status "📊 Observability:        http://localhost:8300"
print_status "🤖 Sales Data Agent:      http://localhost:8001"
print_status "📰 News Search Agent:      http://localhost:8002"
print_status "📝 Text Analysis Agent:    http://localhost:8003"
print_status "📈 Data Visualization:    http://localhost:8004"
print_status "🖥️ Web UI:               http://localhost:8501"

print_header "🎯 Step 6: Quick Test"
print_status "Testing agent registration..."
sleep 5

# Test if agents are registered
if curl -f http://localhost:8000/list_agents &>/dev/null; then
    agent_count=$(curl -s http://localhost:8000/list_agents | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    print_status "✅ $agent_count agents registered in registry"
else
    print_warning "⚠️ Could not verify agent registration"
fi

print_header "🎉 Setup Complete!"
echo ""
print_status "🚀 Platform is running and ready to use!"
print_status "🖥️ Open your browser and go to: http://localhost:8501"
echo ""
print_status "📚 Useful commands:"
echo "  • View logs:           docker-compose logs -f"
echo "  • View specific service: docker-compose logs -f [service_name]"
echo "  • Stop platform:        docker-compose down"
echo "  • Restart platform:      docker-compose restart"
echo "  • Check status:        docker-compose ps"
echo ""
print_status "🧪 Try the demo goal:"
echo "  'Create a weekly sales intelligence report with competitor analysis'"
echo ""
print_status "📊 Check observability:"
echo "  • Metrics: http://localhost:8300/metrics"
echo "  • Traces:  http://localhost:8300/traces"
echo "  • Events:   http://localhost:8300/events"
echo ""

# Optional: Open browser automatically
if command -v open &> /dev/null; then
    print_status "🌐 Opening browser automatically..."
    sleep 2
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    print_status "🌐 Opening browser automatically..."
    sleep 2
    xdg-open http://localhost:8501
fi

print_header "✨ Enjoy the AI Agent Orchestration Platform!"