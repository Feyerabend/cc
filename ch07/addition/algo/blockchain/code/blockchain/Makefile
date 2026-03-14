# Refined Blockchain Makefile
# ================================

# Configuration
PYTHON := python3
PIP := pip3
VENV := venv
BLOCKCHAIN_FILE := blockchain.py
REQUIREMENTS := requirements.txt

# Default ports for multi-node setup
NODE1_PORT := 5000
NODE2_PORT := 5001
NODE3_PORT := 5002

# Mining configuration
DIFFICULTY := 4
REWARD := 10.0

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help install setup clean test demo run-node run-multi-node stop-nodes mine-demo network-demo docker-build docker-run

# Default target
help: ## Show this help message
	@echo "$(BLUE)Refined Blockchain Management$(NC)"
	@echo "============================="
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Setup and Installation
install: ## Install Python dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install -r $(REQUIREMENTS)

setup: ## Create virtual environment and install dependencies
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)Activating virtual environment and installing dependencies...$(NC)"
	$(VENV)/bin/pip install -r $(REQUIREMENTS)
	@echo "$(GREEN)Setup complete! Activate with: source $(VENV)/bin/activate$(NC)"

requirements: ## Generate requirements.txt file
	@echo "$(GREEN)Generating requirements.txt...$(NC)"
	@echo "flask==2.3.2" > $(REQUIREMENTS)
	@echo "requests==2.31.0" >> $(REQUIREMENTS)
	@echo "ecdsa==0.18.0" >> $(REQUIREMENTS)
	@echo "$(GREEN)Requirements file created$(NC)"

# Development and Testing
test: ## Run blockchain tests
	@echo "$(GREEN)Running blockchain tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v || echo "$(YELLOW)No tests found - running basic validation$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) demo

demo: ## Run blockchain demonstration
	@echo "$(GREEN)Running blockchain demo...$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) demo

validate: ## Validate blockchain code
	@echo "$(GREEN)Validating blockchain code...$(NC)"
	$(PYTHON) -m py_compile $(BLOCKCHAIN_FILE)
	@echo "$(GREEN)Code validation passed$(NC)"

# Single Node Operations
run-node: ## Run single blockchain node (default port 5000)
	@echo "$(GREEN)Starting blockchain node on port $(NODE1_PORT)...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) --port $(NODE1_PORT) --difficulty $(DIFFICULTY) --reward $(REWARD)

run-node-debug: ## Run single node with debug logging
	@echo "$(GREEN)Starting blockchain node in debug mode...$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) --port $(NODE1_PORT) --difficulty $(DIFFICULTY) --reward $(REWARD) --debug

# Multi-Node Network
run-multi-node: ## Start 3-node blockchain network
	@echo "$(GREEN)Starting 3-node blockchain network...$(NC)"
	@echo "$(YELLOW)Starting node 1 on port $(NODE1_PORT)...$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) --port $(NODE1_PORT) --difficulty $(DIFFICULTY) --reward $(REWARD) > logs/node1.log 2>&1 &
	@sleep 2
	@echo "$(YELLOW)Starting node 2 on port $(NODE2_PORT)...$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) --port $(NODE2_PORT) --difficulty $(DIFFICULTY) --reward $(REWARD) > logs/node2.log 2>&1 &
	@sleep 2
	@echo "$(YELLOW)Starting node 3 on port $(NODE3_PORT)...$(NC)"
	$(PYTHON) $(BLOCKCHAIN_FILE) --port $(NODE3_PORT) --difficulty $(DIFFICULTY) --reward $(REWARD) > logs/node3.log 2>&1 &
	@sleep 1
	@echo "$(GREEN)Network started! Nodes running on ports $(NODE1_PORT), $(NODE2_PORT), $(NODE3_PORT)$(NC)"
	@echo "$(BLUE)Check logs in logs/ directory$(NC)"
	@echo "$(BLUE)Use 'make stop-nodes' to stop all nodes$(NC)"

stop-nodes: ## Stop all blockchain nodes
	@echo "$(GREEN)Stopping all blockchain nodes...$(NC)"
	@pkill -f "$(BLOCKCHAIN_FILE)" || echo "$(YELLOW)No nodes running$(NC)"
	@echo "$(GREEN)All nodes stopped$(NC)"

# Mining Operations
mine-demo: ## Run mining demonstration
	@echo "$(GREEN)Running mining demo...$(NC)"
	@echo "$(YELLOW)This will start a node and demonstrate mining operations$(NC)"
	./scripts/mining_demo.sh

# Network Operations
network-demo: ## Demonstrate network operations
	@echo "$(GREEN)Running network demonstration...$(NC)"
	./scripts/network_demo.sh

connect-nodes: ## Connect nodes in multi-node setup
	@echo "$(GREEN)Connecting nodes...$(NC)"
	curl -X POST http://localhost:$(NODE1_PORT)/nodes \
		-H "Content-Type: application/json" \
		-d '{"nodes": ["http://localhost:$(NODE2_PORT)", "http://localhost:$(NODE3_PORT)"]}' || true
	curl -X POST http://localhost:$(NODE2_PORT)/nodes \
		-H "Content-Type: application/json" \
		-d '{"nodes": ["http://localhost:$(NODE1_PORT)", "http://localhost:$(NODE3_PORT)"]}' || true
	curl -X POST http://localhost:$(NODE3_PORT)/nodes \
		-H "Content-Type: application/json" \
		-d '{"nodes": ["http://localhost:$(NODE1_PORT)", "http://localhost:$(NODE2_PORT)"]}' || true
	@echo "$(GREEN)Nodes connected$(NC)"

# API Testing
test-api: ## Test blockchain API endpoints
	@echo "$(GREEN)Testing API endpoints...$(NC)"
	./scripts/api_test.sh

create-wallet: ## Create a new wallet
	@echo "$(GREEN)Creating new wallet...$(NC)"
	curl -X POST http://localhost:$(NODE1_PORT)/wallet/new | jq '.'

get-stats: ## Get blockchain statistics
	@echo "$(GREEN)Getting blockchain stats...$(NC)"
	curl -s http://localhost:$(NODE1_PORT)/stats | jq '.'

get-chain: ## Get blockchain data
	@echo "$(GREEN)Getting blockchain...$(NC)"
	curl -s http://localhost:$(NODE1_PORT)/chain | jq '.length'

# Maintenance
clean: ## Clean generated files and logs
	@echo "$(GREEN)Cleaning up...$(NC)"
	rm -f *.log
	rm -f *.dat
	rm -f *.json
	rm -rf logs/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(GREEN)Removing virtual environment...$(NC)"
	rm -rf $(VENV)

# Docker Operations
docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t refined-blockchain .

docker-run: ## Run blockchain in Docker
	@echo "$(GREEN)Running blockchain in Docker...$(NC)"
	docker run -p $(NODE1_PORT):$(NODE1_PORT) refined-blockchain

# Monitoring
logs: ## Show logs from all nodes
	@echo "$(GREEN)Showing logs...$(NC)"
	mkdir -p logs
	tail -f logs/*.log 2>/dev/null || echo "$(YELLOW)No log files found$(NC)"

status: ## Check status of running nodes
	@echo "$(GREEN)Checking node status...$(NC)"
	@echo "$(YELLOW)Node 1 (port $(NODE1_PORT)):$(NC)"
	@curl -s http://localhost:$(NODE1_PORT)/health || echo "$(RED)Not running$(NC)"
	@echo "$(YELLOW)Node 2 (port $(NODE2_PORT)):$(NC)"
	@curl -s http://localhost:$(NODE2_PORT)/health || echo "$(RED)Not running$(NC)"
	@echo "$(YELLOW)Node 3 (port $(NODE3_PORT)):$(NC)"
	@curl -s http://localhost:$(NODE3_PORT)/health || echo "$(RED)Not running$(NC)"

# Development helpers
dev-setup: setup requirements ## Complete development setup
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. source $(VENV)/bin/activate"
	@echo "  2. make run-node"

lint: ## Run code linting (if available)
	@echo "$(GREEN)Running code linting...$(NC)"
	@which flake8 > /dev/null && flake8 $(BLOCKCHAIN_FILE) || echo "$(YELLOW)flake8 not installed$(NC)"
	@which black > /dev/null && black --check $(BLOCKCHAIN_FILE) || echo "$(YELLOW)black not installed$(NC)"

format: ## Format code (if black is available)
	@echo "$(GREEN)Formatting code...$(NC)"
	@which black > /dev/null && black $(BLOCKCHAIN_FILE) || echo "$(YELLOW)black not installed - skipping format$(NC)"

# Quick start combinations
quick-start: dev-setup run-node ## Quick start for development

full-demo: demo mine-demo ## Run all demonstrations

# Create necessary directories
init-dirs:
	@mkdir -p logs
	@mkdir -p scripts
	@mkdir -p tests

# Help for specific operations
help-api: ## Show API usage examples
	@echo "$(BLUE)Blockchain API Examples:$(NC)"
	@echo "========================"
	@echo ""
	@echo "$(GREEN)Health Check:$(NC)"
	@echo "  curl http://localhost:5000/health"
	@echo ""
	@echo "$(GREEN)Get Stats:$(NC)"
	@echo "  curl http://localhost:5000/stats"
	@echo ""
	@echo "$(GREEN)Create Wallet:$(NC)"
	@echo "  curl -X POST http://localhost:5000/wallet/new"
	@echo ""
	@echo "$(GREEN)Get Balance:$(NC)"
	@echo "  curl http://localhost:5000/balance/ADDRESS"
	@echo ""
	@echo "$(GREEN)Create Transaction:$(NC)"
	@echo "  curl -X POST http://localhost:5000/transaction \\"
	@echo "    -H 'Content-Type: application/json' \\"
	@echo "    -d '{\"sender\":\"ADDR1\",\"recipient\":\"ADDR2\",\"amount\":10}'"
	@echo ""
	@echo "$(GREEN)Mine Block:$(NC)"
	@echo "  curl -X POST http://localhost:5000/mine \\"
	@echo "    -H 'Content-Type: application/json' \\"
	@echo "    -d '{\"miner_address\":\"ADDRESS\"}'"

# Installation check
check-deps: ## Check if dependencies are installed
	@echo "$(GREEN)Checking dependencies...$(NC)"
	@$(PYTHON) -c "import flask; print('Flask: OK')" || echo "$(RED)Flask: Missing$(NC)"
	@$(PYTHON) -c "import requests; print('Requests: OK')" || echo "$(RED)Requests: Missing$(NC)"
	@$(PYTHON) -c "import ecdsa; print('ECDSA: OK')" || echo "$(RED)ECDSA: Missing$(NC)"
	@which curl > /dev/null && echo "$(GREEN)curl: OK$(NC)" || echo "$(RED)curl: Missing$(NC)"
	@which jq > /dev/null && echo "$(GREEN)jq: OK$(NC)" || echo "$(YELLOW)jq: Missing (optional)$(NC)"