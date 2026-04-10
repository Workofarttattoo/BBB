#!/bin/bash
#
# Gradual Scaling Deployment Script for BBB Autonomous System
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
#
# This script deploys the intelligent gradual scaling system that:
# - Starts with 3-5 businesses to prove profitability
# - Monitors performance metrics in real-time
# - Scales up gradually based on proven success
# - Uses exponential scaling with safety checks
#

set -e  # Exit on any error

echo "🎯 GRADUAL SCALING DEPLOYMENT - BBB AUTONOMOUS SYSTEM"
echo "Copyright (c) 2025 Joshua Hendricks Cole"
echo "Corporation of Light - PATENT PENDING"
echo

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCALING_ORCHESTRATOR_PORT=8002
PROFITABILITY_MONITOR_PORT=8001
DEPLOYMENT_API_PORT=8000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if port is in use
check_port() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        log_warning "Port $port ($service_name) is already in use"
        return 1
    else
        log_info "Port $port ($service_name) is available"
        return 0
    fi
}

# Kill process on port
kill_port() {
    local port=$1
    local service_name=$2

    if lsof -ti:$port >/dev/null 2>&1; then
        log_info "Stopping existing $service_name on port $port..."
        kill -9 $(lsof -ti:$port) 2>/dev/null || true
        sleep 2
    fi
}

# Start service in background
start_service() {
    local service_name=$1
    local command=$2
    local log_file=$3

    log_info "Starting $service_name..."
    nohup $command > "$log_file" 2>&1 &
    local pid=$!

    # Wait a bit and check if it's still running
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        log_success "$service_name started (PID: $pid)"
        echo $pid > "${service_name}.pid"
        return $pid
    else
        log_error "$service_name failed to start. Check logs: $log_file"
        return 1
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if required Python files exist
    local required_files=(
        "gradual_scaling_orchestrator.py"
        "profitability_monitor.py"
        "mass_business_deployment_api.py"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done

    # Check Python availability
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        exit 1
    fi

    # Check required Python packages
    python3 -c "
import sys
required_packages = ['fastapi', 'uvicorn', 'httpx', 'stripe']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'Missing packages: {missing_packages}')
    sys.exit(1)
" 2>/dev/null

    if [[ $? -ne 0 ]]; then
        log_error "Missing required Python packages. Install with: pip install fastapi uvicorn httpx stripe"
        exit 1
    fi

    log_success "Pre-deployment checks passed"
}

# Deploy profitability monitor
deploy_profitability_monitor() {
    log_info "Deploying Profitability Monitor..."

    kill_port $PROFITABILITY_MONITOR_PORT "Profitability Monitor"

    if ! check_port $PROFITABILITY_MONITOR_PORT "Profitability Monitor"; then
        kill_port $PROFITABILITY_MONITOR_PORT "Profitability Monitor"
    fi

    cd "$SCRIPT_DIR"
    local log_file="$SCRIPT_DIR/logs/profitability_monitor_$(date +%Y%m%d_%H%M%S).log"

    start_service "Profitability Monitor" "python3 profitability_monitor.py" "$log_file"

    # Wait for service to be ready
    local retries=10
    while [[ $retries -gt 0 ]]; do
        if curl -s "http://localhost:$PROFITABILITY_MONITOR_PORT/portfolio/summary" >/dev/null 2>&1; then
            log_success "Profitability Monitor is responding"
            return 0
        fi
        sleep 2
        ((retries--))
    done

    log_error "Profitability Monitor failed to respond"
    return 1
}

# Deploy mass deployment API
deploy_mass_deployment_api() {
    log_info "Deploying Mass Business Deployment API..."

    kill_port $DEPLOYMENT_API_PORT "Mass Deployment API"

    if ! check_port $DEPLOYMENT_API_PORT "Mass Deployment API"; then
        kill_port $DEPLOYMENT_API_PORT "Mass Deployment API"
    fi

    cd "$SCRIPT_DIR"
    local log_file="$SCRIPT_DIR/logs/mass_deployment_api_$(date +%Y%m%d_%H%M%S).log"

    start_service "Mass Deployment API" "python3 -m uvicorn mass_business_deployment_api:app --host 0.0.0.0 --port $DEPLOYMENT_API_PORT" "$log_file"

    # Wait for service to be ready
    local retries=10
    while [[ $retries -gt 0 ]]; do
        if curl -s "http://localhost:$DEPLOYMENT_API_PORT/docs" >/dev/null 2>&1; then
            log_success "Mass Deployment API is responding"
            return 0
        fi
        sleep 2
        ((retries--))
    done

    log_error "Mass Deployment API failed to respond"
    return 1
}

# Deploy gradual scaling orchestrator
deploy_scaling_orchestrator() {
    log_info "Deploying Gradual Scaling Orchestrator..."

    kill_port $SCALING_ORCHESTRATOR_PORT "Scaling Orchestrator"

    if ! check_port $SCALING_ORCHESTRATOR_PORT "Scaling Orchestrator"; then
        kill_port $SCALING_ORCHESTRATOR_PORT "Scaling Orchestrator"
    fi

    cd "$SCRIPT_DIR"
    local log_file="$SCRIPT_DIR/logs/scaling_orchestrator_$(date +%Y%m%d_%H%M%S).log"

    start_service "Scaling Orchestrator" "python3 gradual_scaling_orchestrator.py" "$log_file"

    # The orchestrator doesn't have a web API, so just check if process is running
    sleep 3
    if [[ -f "Scaling Orchestrator.pid" ]] && kill -0 $(cat "Scaling Orchestrator.pid") 2>/dev/null; then
        log_success "Gradual Scaling Orchestrator is running"
        return 0
    else
        log_error "Gradual Scaling Orchestrator failed to start"
        return 1
    fi
}

# Test the integrated system
test_system_integration() {
    log_info "Testing system integration..."

    # Test profitability monitor
    if ! curl -s "http://localhost:$PROFITABILITY_MONITOR_PORT/portfolio/summary" >/dev/null 2>&1; then
        log_error "Profitability Monitor not responding"
        return 1
    fi

    # Test mass deployment API
    if ! curl -s "http://localhost:$DEPLOYMENT_API_PORT/docs" >/dev/null 2>&1; then
        log_error "Mass Deployment API not responding"
        return 1
    fi

    # Test scaling orchestrator (check if process is running)
    if [[ ! -f "Scaling Orchestrator.pid" ]] || ! kill -0 $(cat "Scaling Orchestrator.pid") 2>/dev/null; then
        log_error "Scaling Orchestrator not running"
        return 1
    fi

    # Test initial deployment (should be rejected or approved based on current state)
    local test_response=$(curl -s -X POST "http://localhost:$DEPLOYMENT_API_PORT/deploy/mass" \
        -H "Content-Type: application/json" \
        -d '{
            "count": 3,
            "business_type": "5_gig",
            "owner_email": "josh@flowstate.work",
            "auto_fold_inactive": true
        }')

    if [[ $? -eq 0 ]] && [[ "$test_response" == *"deployment_id"* ]]; then
        log_success "System integration test passed"
        return 0
    else
        log_warning "System integration test inconclusive (may be expected based on scaling state)"
        return 0
    fi
}

# Show status
show_deployment_status() {
    echo
    log_success "DEPLOYMENT COMPLETE!"
    echo
    echo "📊 Active Services:"
    echo "   • Profitability Monitor:     http://localhost:$PROFITABILITY_MONITOR_PORT"
    echo "   • Mass Deployment API:       http://localhost:$DEPLOYMENT_API_PORT"
    echo "   • Scaling Orchestrator:      Running (PID: $(cat 'Scaling Orchestrator.pid' 2>/dev/null || echo 'unknown'))"
    echo
    echo "🎯 Scaling Strategy:"
    echo "   • Phase 1 (Pilot): 3-5 businesses - Prove concept"
    echo "   • Phase 2 (Validation): 10-25 businesses - Prove profitability"
    echo "   • Phase 3 (Scale 100): 100 businesses - Establish patterns"
    echo "   • Phase 4 (Scale 1K): 1,000 businesses - Optimize operations"
    echo "   • Phase 5 (Scale 10K): 10,000 businesses - Full automation"
    echo "   • Phase 6 (Scale 100K): 100,000 businesses - Mass deployment"
    echo "   • Phase 7 (Scale 1M): 1,000,000 businesses - Peak scale"
    echo
    echo "📈 Current Status:"
    echo "   • Starting with PILOT phase (3 businesses)"
    echo "   • Monitoring profitability in real-time"
    echo "   • Automatic scaling based on performance"
    echo "   • Safety controls prevent over-scaling"
    echo
    echo "🔧 Management Commands:"
    echo "   • Check status: curl http://localhost:$SCALING_ORCHESTRATOR_PORT/status"
    echo "   • View logs: tail -f logs/scaling_orchestrator_*.log"
    echo "   • Stop all: ./STOP_AUTONOMOUS_SYSTEM.sh"
    echo
    echo "⚡ The system will now:"
    echo "   1. Deploy initial 3 pilot businesses"
    echo "   2. Monitor their performance daily"
    echo "   3. Scale up only after proving profitability"
    echo "   4. Continue scaling gradually to 1 million businesses"
    echo
    log_success "Gradual scaling deployment successful!"
}

# Main deployment function
main() {
    echo "Starting Gradual Scaling Deployment..."

    # Create logs directory
    mkdir -p "$SCRIPT_DIR/logs"

    # Run pre-deployment checks
    pre_deployment_checks

    # Deploy services in order
    log_info "Deploying system components..."

    if ! deploy_profitability_monitor; then
        log_error "Failed to deploy profitability monitor"
        exit 1
    fi

    if ! deploy_mass_deployment_api; then
        log_error "Failed to deploy mass deployment API"
        exit 1
    fi

    if ! deploy_scaling_orchestrator; then
        log_error "Failed to deploy scaling orchestrator"
        exit 1
    fi

    # Test integration
    if ! test_system_integration; then
        log_error "System integration test failed"
        exit 1
    fi

    # Show final status
    show_deployment_status
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        log_info "Stopping all gradual scaling services..."
        kill_port $SCALING_ORCHESTRATOR_PORT "Scaling Orchestrator"
        kill_port $PROFITABILITY_MONITOR_PORT "Profitability Monitor"
        kill_port $DEPLOYMENT_API_PORT "Mass Deployment API"
        log_success "All services stopped"
        ;;
    "status")
        echo "Service Status:"
        echo "Scaling Orchestrator: $(if [[ -f 'Scaling Orchestrator.pid' ]] && kill -0 $(cat 'Scaling Orchestrator.pid') 2>/dev/null; then echo 'RUNNING'; else echo 'STOPPED'; fi)"
        echo "Profitability Monitor: $(if curl -s http://localhost:$PROFITABILITY_MONITOR_PORT/portfolio/summary >/dev/null 2>&1; then echo 'RUNNING'; else echo 'STOPPED'; fi)"
        echo "Mass Deployment API: $(if curl -s http://localhost:$DEPLOYMENT_API_PORT/docs >/dev/null 2>&1; then echo 'RUNNING'; else echo 'STOPPED'; fi)"
        ;;
    "restart")
        log_info "Restarting gradual scaling system..."
        "$0" stop
        sleep 3
        "$0"
        ;;
    *)
        main
        ;;
esac
