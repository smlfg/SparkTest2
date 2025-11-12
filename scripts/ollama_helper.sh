#!/bin/bash

# ============================================================================
# Ollama Helper Script
# ============================================================================
# TEACHING: Shell Script Best Practices
#
# This script provides convenient commands for managing Ollama.
# Instead of remembering long Docker commands, you can use:
#   ./scripts/ollama_helper.sh list
#   ./scripts/ollama_helper.sh test exp-001
#
# Shell scripting skills are valuable in ML engineering for:
# - Automating repetitive tasks
# - Orchestrating multiple tools
# - Creating reproducible workflows
# ============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Ollama container is running
check_ollama() {
    if ! docker ps | grep -q ollama; then
        print_error "Ollama container is not running"
        echo "Start it with: docker-compose up -d"
        exit 1
    fi
}

# Command: start
cmd_start() {
    print_header "Starting Ollama"
    docker-compose up -d
    sleep 2
    if docker ps | grep -q ollama; then
        print_success "Ollama started successfully"
        echo "API available at: http://localhost:11434"
    else
        print_error "Failed to start Ollama"
        exit 1
    fi
}

# Command: stop
cmd_stop() {
    print_header "Stopping Ollama"
    docker-compose down
    print_success "Ollama stopped"
}

# Command: restart
cmd_restart() {
    print_header "Restarting Ollama"
    docker-compose restart
    sleep 2
    print_success "Ollama restarted"
}

# Command: logs
cmd_logs() {
    print_header "Ollama Logs (Ctrl+C to exit)"
    docker-compose logs -f ollama
}

# Command: status
cmd_status() {
    print_header "Ollama Status"

    if docker ps | grep -q ollama; then
        print_success "Container: Running"

        # Check API
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "API: Responding"
        else
            print_warning "API: Not responding"
        fi

        # Show resource usage
        echo -e "\n📊 Resource Usage:"
        docker stats ollama --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}"

    else
        print_error "Container: Not running"
        echo "Start it with: $0 start"
    fi
}

# Command: list
cmd_list() {
    check_ollama
    print_header "Models in Ollama"
    docker exec ollama ollama list
}

# Command: pull
cmd_pull() {
    check_ollama
    if [ -z "$1" ]; then
        print_error "Usage: $0 pull <model-name>"
        echo "Example: $0 pull qwen2.5:0.5b"
        exit 1
    fi

    print_header "Pulling model: $1"
    docker exec ollama ollama pull "$1"
    print_success "Model pulled: $1"
}

# Command: remove
cmd_remove() {
    check_ollama
    if [ -z "$1" ]; then
        print_error "Usage: $0 remove <model-name>"
        echo "Example: $0 remove exp-001"
        exit 1
    fi

    print_warning "Removing model: $1"
    docker exec ollama ollama rm "$1"
    print_success "Model removed: $1"
}

# Command: test
cmd_test() {
    check_ollama
    if [ -z "$1" ]; then
        print_error "Usage: $0 test <model-name> [prompt]"
        echo "Example: $0 test exp-001 'What is 2+2?'"
        exit 1
    fi

    MODEL="$1"
    PROMPT="${2:-Hello! Who are you?}"

    print_header "Testing model: $MODEL"
    echo "Prompt: $PROMPT"
    echo ""

    docker exec -it ollama ollama run "$MODEL" "$PROMPT"
}

# Command: api-test
cmd_api_test() {
    check_ollama
    if [ -z "$1" ]; then
        print_error "Usage: $0 api-test <model-name> [prompt]"
        echo "Example: $0 api-test exp-001 'What is 2+2?'"
        exit 1
    fi

    MODEL="$1"
    PROMPT="${2:-Hello! Who are you?}"

    print_header "API Test: $MODEL"
    echo "Prompt: $PROMPT"
    echo ""

    curl http://localhost:11434/api/generate -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"$PROMPT\",
        \"stream\": false
    }" | python3 -m json.tool
}

# Command: shell
cmd_shell() {
    check_ollama
    print_header "Opening shell in Ollama container"
    docker exec -it ollama /bin/bash
}

# Command: gpu
cmd_gpu() {
    check_ollama
    print_header "GPU Status in Container"
    docker exec ollama nvidia-smi
}

# Command: help
cmd_help() {
    cat << EOF

${BLUE}Ollama Helper Script${NC}
====================

Convenient commands for managing Ollama during development.

${GREEN}Usage:${NC}
    $0 <command> [arguments]

${GREEN}Commands:${NC}

  ${YELLOW}Infrastructure:${NC}
    start              Start Ollama container
    stop               Stop Ollama container
    restart            Restart Ollama container
    status             Show Ollama status
    logs               View Ollama logs (live)
    shell              Open bash shell in container
    gpu                Show GPU status in container

  ${YELLOW}Model Management:${NC}
    list               List all models
    pull <name>        Pull a model from Ollama registry
    remove <name>      Remove a model

  ${YELLOW}Testing:${NC}
    test <name> [prompt]      Test model interactively
    api-test <name> [prompt]  Test model via API (JSON)

  ${YELLOW}Help:${NC}
    help               Show this help message

${GREEN}Examples:${NC}
    $0 start
    $0 pull qwen2.5:0.5b
    $0 list
    $0 test exp-001 "What is 2+2?"
    $0 api-test exp-001
    $0 gpu
    $0 logs

${GREEN}Troubleshooting:${NC}
    # Container won't start
    $0 logs

    # API not responding
    $0 restart
    $0 status

    # GPU not detected
    $0 gpu

EOF
}

# Main command dispatcher
main() {
    COMMAND="${1:-help}"

    case "$COMMAND" in
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs
            ;;
        list)
            cmd_list
            ;;
        pull)
            cmd_pull "$2"
            ;;
        remove|rm)
            cmd_remove "$2"
            ;;
        test)
            cmd_test "$2" "$3"
            ;;
        api-test)
            cmd_api_test "$2" "$3"
            ;;
        shell)
            cmd_shell
            ;;
        gpu)
            cmd_gpu
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"
