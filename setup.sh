#!/bin/bash
# =============================================================================
# DGX Fast Fine-tuning Lab - Automated Setup Script
# =============================================================================
#
# WHAT THIS DOES:
# 1. Checks prerequisites (GPU, Docker, Python)
# 2. Creates Python virtual environment
# 3. Installs dependencies
# 4. Starts Ollama (if docker-compose.yml exists)
# 5. Pulls base model (qwen2.5:0.5b)
# 6. Verifies everything works
#
# USAGE:
#   ./setup.sh
#
# FOR BEGINNERS:
#   chmod +x setup.sh
#   ./setup.sh
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# =============================================================================
# STEP 0: Welcome
# =============================================================================
clear
print_header "DGX Fast Fine-tuning Lab - Setup"
echo "This script will set up your environment step by step."
echo "Estimated time: 5-10 minutes (depending on downloads)"
echo ""
echo "Press ENTER to start..."
read

# =============================================================================
# STEP 1: Check Prerequisites
# =============================================================================
print_header "STEP 1: Checking Prerequisites"

# Check: nvidia-smi (GPU drivers)
print_info "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
        print_step "NVIDIA GPU detected: $GPU_NAME"
    else
        print_error "nvidia-smi found but failed to run"
        print_warning "GPU drivers may not be properly installed"
        echo ""
        echo "Try: sudo apt-get install nvidia-driver-535 && sudo reboot"
        exit 1
    fi
else
    print_error "nvidia-smi not found"
    print_warning "NVIDIA GPU drivers are required for this project"
    echo ""
    echo "Install drivers:"
    echo "  Ubuntu/Debian: sudo apt-get install nvidia-driver-535"
    echo "  Then reboot: sudo reboot"
    exit 1
fi

# Check: Docker
print_info "Checking for Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | tr -d ',')
    print_step "Docker installed: $DOCKER_VERSION"

    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        print_step "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        echo ""
        echo "Start Docker:"
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        exit 1
    fi
else
    print_error "Docker not found"
    print_warning "Docker is required for Ollama (inference engine)"
    echo ""
    echo "Install Docker:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    exit 1
fi

# Check: Docker Compose
print_info "Checking for Docker Compose..."
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    print_step "Docker Compose available"
    COMPOSE_CMD="docker compose"
    # Try old version
    if ! docker compose version &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    fi
else
    print_error "Docker Compose not found"
    echo ""
    echo "Install Docker Compose:"
    echo "  sudo apt-get install docker-compose-plugin"
    exit 1
fi

# Check: Python 3
print_info "Checking for Python 3..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f2)
    print_step "Python 3 installed: $PYTHON_VERSION"

    # Check version >= 3.8
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found"
    echo ""
    echo "Install Python 3:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip"
    exit 1
fi

# Check: pip
print_info "Checking for pip..."
if command -v pip3 &> /dev/null || python3 -m pip --version &> /dev/null; then
    print_step "pip available"
else
    print_error "pip not found"
    echo ""
    echo "Install pip:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-pip"
    exit 1
fi

echo ""
print_step "All prerequisites met!"
sleep 1

# =============================================================================
# STEP 2: Create Virtual Environment
# =============================================================================
print_header "STEP 2: Creating Python Virtual Environment"

print_info "Creating virtual environment in ./venv..."

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    echo "Do you want to:"
    echo "  1) Keep existing venv (skip this step)"
    echo "  2) Delete and recreate venv"
    read -p "Choice [1/2]: " choice

    if [ "$choice" == "2" ]; then
        print_info "Removing old venv..."
        rm -rf venv
        python3 -m venv venv
        print_step "New virtual environment created"
    else
        print_step "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    print_step "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

if [ "$VIRTUAL_ENV" != "" ]; then
    print_step "Virtual environment activated: $VIRTUAL_ENV"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

sleep 1

# =============================================================================
# STEP 3: Install Python Dependencies
# =============================================================================
print_header "STEP 3: Installing Python Dependencies"

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in current directory"
    echo ""
    echo "Make sure you're in the project root directory:"
    echo "  cd /path/to/SparkTest2"
    echo "  ./setup.sh"
    exit 1
fi

print_info "Installing dependencies from requirements.txt..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

print_step "Dependencies installed"

# Verify key dependencies
print_info "Verifying installation..."
if python -c "import requests; print('OK')" &> /dev/null; then
    print_step "requests module working"
else
    print_error "Failed to import requests module"
    exit 1
fi

sleep 1

# =============================================================================
# STEP 4: Docker Compose Setup (Ollama)
# =============================================================================
print_header "STEP 4: Starting Ollama (Inference Engine)"

if [ ! -f "docker-compose.yml" ]; then
    print_warning "docker-compose.yml not found"
    print_info "Agent 5 (Infrastructure) will provide this file"
    print_info "For now, you can manually run Ollama:"
    echo ""
    echo "  docker run -d -v ollama:/root/.ollama -p 11434:11434 --gpus all --name ollama ollama/ollama"
    echo ""
    read -p "Press ENTER to continue..."
else
    print_info "Found docker-compose.yml"
    print_info "Starting Ollama container..."

    $COMPOSE_CMD up -d

    # Wait for Ollama to be ready
    print_info "Waiting for Ollama to start (max 30s)..."
    RETRY_COUNT=0
    MAX_RETRIES=30

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_step "Ollama is running and responding"
            break
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 1
    done
    echo ""

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_error "Ollama did not start within 30 seconds"
        echo ""
        echo "Check logs:"
        echo "  docker logs ollama"
        exit 1
    fi
fi

sleep 1

# =============================================================================
# STEP 5: Pull Base Model
# =============================================================================
print_header "STEP 5: Pulling Base Model (qwen2.5:0.5b)"

print_info "Checking if Ollama is accessible..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_step "Ollama API responding"

    # Check if model already exists
    print_info "Checking for existing models..."
    EXISTING_MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4)

    if echo "$EXISTING_MODELS" | grep -q "qwen2.5:0.5b"; then
        print_step "Base model qwen2.5:0.5b already exists"
    else
        print_warning "Base model not found, pulling now..."
        print_info "This will download ~500MB, may take 5-10 minutes"
        echo ""

        # Pull model
        if command -v docker &> /dev/null; then
            docker exec ollama ollama pull qwen2.5:0.5b
            print_step "Base model qwen2.5:0.5b pulled successfully"
        else
            print_error "Cannot pull model: Docker not accessible"
            exit 1
        fi
    fi

    # List all models
    print_info "Available models:"
    docker exec ollama ollama list

else
    print_error "Cannot connect to Ollama at http://localhost:11434"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if container is running: docker ps"
    echo "  2. Check logs: docker logs ollama"
    echo "  3. Restart: docker-compose restart"

    read -p "Press ENTER to continue anyway..."
fi

sleep 1

# =============================================================================
# STEP 6: Verify Setup
# =============================================================================
print_header "STEP 6: Verifying Setup"

print_info "Testing benchmark script..."
cd benchmark

if python run.py --help > /dev/null 2>&1; then
    print_step "Benchmark script working"
else
    print_error "Benchmark script failed"
    exit 1
fi

cd ..

sleep 1

# =============================================================================
# STEP 7: Summary & Next Steps
# =============================================================================
print_header "Setup Complete!"

echo -e "${GREEN}✓${NC} GPU drivers working"
echo -e "${GREEN}✓${NC} Docker running"
echo -e "${GREEN}✓${NC} Python virtual environment created"
echo -e "${GREEN}✓${NC} Dependencies installed"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama running"
    echo -e "${GREEN}✓${NC} Base model available"
else
    echo -e "${YELLOW}!${NC} Ollama setup pending (Agent 5 needed)"
fi

echo ""
print_header "Next Steps"

echo "1. ACTIVATE VIRTUAL ENVIRONMENT (every time you use the project):"
echo "   ${GREEN}source venv/bin/activate${NC}"
echo ""

echo "2. TEST THE BENCHMARK SYSTEM (once Agent 5 exports a model):"
echo "   ${GREEN}cd benchmark${NC}"
echo "   ${GREEN}python run.py --finetuned exp-001${NC}"
echo ""

echo "3. CURRENT STATUS:"
echo "   ✅ Agent 2 (Benchmark Suite) - Ready"
echo "   🔜 Agent 1 (Training) - Coming soon"
echo "   🔜 Agent 5 (Infrastructure) - Coming soon"
echo "   🔜 Agent 3 (Delta Calculator) - Coming soon"
echo "   🔜 Agent 4 (Visualization) - Coming soon"
echo "   🔜 Agent 6 (Orchestration) - Coming soon"
echo ""

echo "4. DOCUMENTATION:"
echo "   📖 README.md - Project overview"
echo "   📖 benchmark/README.md - Benchmark usage"
echo "   📖 docs/agents/agent2_teaching.md - Learning guide"
echo ""

echo "5. HELP:"
echo "   If you encounter issues, check: ${BLUE}README.md${NC} → Troubleshooting section"
echo "   Or check: ${BLUE}docs/agents/agent2_audit_report.md${NC} → Robustness guide"
echo ""

print_header "Quick Reference"

echo "# Activate environment:"
echo "source venv/bin/activate"
echo ""
echo "# Check Ollama status:"
echo "docker ps"
echo "curl http://localhost:11434/api/tags"
echo ""
echo "# List available models:"
echo "docker exec ollama ollama list"
echo ""
echo "# Test GPU:"
echo "nvidia-smi"
echo ""
echo "# Run benchmark (when model ready):"
echo "cd benchmark && python run.py --finetuned exp-001"
echo ""

print_header "Setup Complete! 🚀"

echo "The virtual environment is currently active."
echo "To deactivate it later, run: ${YELLOW}deactivate${NC}"
echo ""
echo "Happy fine-tuning! 🎉"
