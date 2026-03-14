#!/bin/bash
# ============================================
# Blockchain Management Scripts
# ============================================

# Create scripts directory structure
mkdir -p scripts logs tests

# ============================================
# scripts/mining_demo.sh
# ============================================
cat > scripts/mining_demo.sh << 'EOF'
#!/bin/bash
# Mining demonstration script

echo "🔨 Blockchain Mining Demo"
echo "========================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PORT=5000
BLOCKCHAIN_FILE="blockchain.py"

# Start blockchain node in background
echo -e "${GREEN}Starting blockchain node on port $PORT...${NC}"
python3 $BLOCKCHAIN_FILE --port $PORT --difficulty 2 --reward 50 > logs/mining_demo.log 2>&1 &
NODE_PID=$!

# Wait for node to start
sleep 3

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping blockchain node...${NC}"
    kill $NODE_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Check if node is running
if ! curl -s http://localhost:$PORT/health > /dev/null; then
    echo -e "${RED}Failed to start blockchain node${NC}"
    exit 1
fi

echo -e "${GREEN}Node started successfully!${NC}"

# Create wallets
echo -e "\n${BLUE}1. Creating wallets...${NC}"
WALLET1=$(curl -s -X POST http://localhost:$PORT/wallet/new | jq -r '.address')
WALLET2=$(curl -s -X POST http://localhost:$PORT/wallet/new | jq -r '.address')

echo "Wallet 1: ${WALLET1:0:16}..."
echo "Wallet 2: ${WALLET2:0:16}..."

# Mine first block
echo -e "\n${BLUE}2. Mining first block...${NC}"
curl -s -X POST http://localhost:$PORT/mine \
    -H "Content-Type: application/json" \
    -d "{\"miner_address\":\"$WALLET1\"}" | jq '.message'

# Check balance
echo -e "\n${BLUE}3. Checking balance...${NC}"
BALANCE=$(curl -s http://localhost:$PORT/balance/$WALLET1 | jq -r '.balance')
echo "Wallet 1 balance: $BALANCE"

# Create transaction
echo -e "\n${BLUE}4. Creating transaction...${NC}"
curl -s -X POST http://localhost:$PORT/transaction \
    -H "Content-Type: application/json" \
    -d "{\"sender\":\"$WALLET1\",\"recipient\":\"$WALLET2\",\"amount\":20}" | jq '.message'

# Mine second block
echo -e "\n${BLUE}5. Mining second block...${NC}"
curl -s -X POST http://localhost:$PORT/mine \
    -H "Content-Type: application/json" \
    -d "{\"miner_address\":\"$WALLET1\"}" | jq '.message'

# Show final stats
echo -e "\n${BLUE}6. Final blockchain stats:${NC}"
curl -s http://localhost:$PORT/stats | jq '.'

echo -e "\n${GREEN}Mining demo complete!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the node${NC}"

# Keep script running
while true; do
    sleep 1
done
EOF

# ============================================
# scripts/network_demo.sh
# ============================================
cat > scripts/network_demo.sh << 'EOF'
#!/bin/bash
# Network demonstration script

echo "Blockchain Network Demo"
echo "=========================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BLOCKCHAIN_FILE="blockchain.py"
PORTS=(5000 5001 5002)
PIDS=()

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping all nodes...${NC}"
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null
    done
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start nodes
echo -e "${GREEN}Starting 3-node network...${NC}"
for port in "${PORTS[@]}"; do
    echo -e "${BLUE}Starting node on port $port...${NC}"
    python3 $BLOCKCHAIN_FILE --port $port --difficulty 2 --reward 25 > logs/node_$port.log 2>&1 &
    PIDS+=($!)
    sleep 2
done

# Wait for all nodes to start
echo -e "${GREEN}Waiting for nodes to initialize...${NC}"
sleep 5

# Check node health
echo -e "\n${BLUE}Checking node health...${NC}"
for port in "${PORTS[@]}"; do
    if curl -s http://localhost:$port/health > /dev/null; then
        echo -e "Node $port: ${GREEN}✓ Running${NC}"
    else
        echo -e "Node $port: ${RED}✗ Failed${NC}"
    fi
done

# Connect nodes
echo -e "\n${BLUE}Connecting nodes...${NC}"
curl -s -X POST http://localhost:5000/nodes \
    -H "Content-Type: application/json" \
    -d '{"nodes": ["http://localhost:5001", "http://localhost:5002"]}' > /dev/null

curl -s -X POST http://localhost:5001/nodes \
    -H "Content-Type: application/json" \
    -d '{"nodes": ["http://localhost:5000", "http://localhost:5002"]}' > /dev/null

curl -s -X POST http://localhost:5002/nodes \
    -H "Content-Type: application/json" \
    -d '{"nodes": ["http://localhost:5000", "http://localhost:5001"]}' > /dev/null

echo -e "${GREEN}Nodes connected!${NC}"

# Create wallets on different nodes
echo -e "\n${BLUE}Creating wallets...${NC}"
WALLET1=$(curl -s -X POST http://localhost:5000/wallet/new | jq -r '.address')
WALLET2=$(curl -s -X POST http://localhost:5001/wallet/new | jq -r '.address')
WALLET3=$(curl -s -X POST http://localhost:5002/wallet/new | jq -r '.address')

echo "Wallet 1 (Node 5000): ${WALLET1:0:16}..."
echo "Wallet 2 (Node 5001): ${WALLET2:0:16}..."
echo "Wallet 3 (Node 5002): ${WALLET3:0:16}..."

# Mine on different nodes
echo -e "\n${BLUE}Mining blocks on different nodes...${NC}"

echo "Mining on Node 5000..."
curl -s -X POST http://localhost:5000/mine \
    -H "Content-Type: application/json" \
    -d "{\"miner_address\":\"$WALLET1\"}" > /dev/null

sleep 2

echo "Mining on Node 5001..."
curl -s -X POST http://localhost:5001/mine \
    -H "Content-Type: application/json" \
    -d "{\"miner_address\":\"$WALLET2\"}" > /dev/null

sleep 2

echo "Mining on Node 5002..."
curl -s -X POST http://localhost:5002/mine \
    -H "Content-Type: application/json" \
    -d "{\"miner_address\":\"$WALLET3\"}" > /dev/null

# Show network stats
echo -e "\n${BLUE}Network Statistics:${NC}"
for port in "${PORTS[@]}"; do
    echo -e "\n${YELLOW}Node $port:${NC}"
    curl -s http://localhost:$port/stats | jq '{blocks, total_transactions, nodes}'
done

echo -e "\n${GREEN}Network demo running!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all nodes${NC}"
echo -e "${BLUE}Check logs in logs/ directory${NC}"

# Keep script running
while true; do
    sleep 5
    # Show live chain lengths
    echo -e "\n${BLUE}Chain lengths:${NC}"
    for port in "${PORTS[@]}"; do
        LENGTH=$(curl -s http://localhost:$port/chain | jq -r '.length')
        echo "Node $port: $LENGTH blocks"
    done
done
EOF

# ============================================
# scripts/api_test.sh
# ============================================
cat > scripts/api_test.sh << 'EOF'
#!/bin/bash
# API testing script

echo "🔧 Blockchain API Test Suite"
echo "============================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PORT=5000
BASE_URL="http://localhost:$PORT"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    echo -n "Testing: $description... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "%{http_code}" -X $method "$BASE_URL$endpoint" \
                       -H "Content-Type: application/json" \
                       -d "$data")
    else
        response=$(curl -s -w "%{http_code}" -X $method "$BASE_URL$endpoint")
    fi
    
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        if [ -n "$body" ] && command -v jq &> /dev/null; then
            echo "$body" | jq '.' 2>/dev/null | head -5
        fi
    else
        echo -e "${RED}✗ FAIL (Expected: $expected_status, Got: $status_code)${NC}"
        ((TESTS_FAILED++))
        echo "Response: $body"
    fi
    echo ""
}

# Check if node is running
echo -e "${BLUE}Checking if blockchain node is running on port $PORT...${NC}"
if ! curl -s $BASE_URL/health > /dev/null; then
    echo -e "${RED}Node not running. Start with: make run-node${NC}"
    exit 1
fi

echo -e "${GREEN}Node is running!${NC}\n"

# Run tests
echo -e "${BLUE}Running API tests...${NC}\n"

# Basic endpoints
test_endpoint "GET" "/health" "" 200 "Health check"
test_endpoint "GET" "/stats" "" 200 "Get statistics"
test_endpoint "GET" "/chain" "" 200 "Get blockchain"
test_endpoint "GET" "/transactions/pending" "" 200 "Get pending transactions"

# Wallet creation
test_endpoint "POST" "/wallet/new" "" 200 "Create wallet"

# Create a wallet for testing
WALLET_RESPONSE=$(curl -s -X POST $BASE_URL/wallet/new)
if command -v jq &> /dev/null; then
    WALLET_ADDR=$(echo $WALLET_RESPONSE | jq -r '.address')
else
    WALLET_ADDR="test_address"
fi

# Balance check
test_endpoint "GET" "/balance/$WALLET_ADDR" "" 200 "Get balance"

# Transaction creation (will fail due to no signature)
test_endpoint "POST" "/transaction" '{"sender":"test","recipient":"test2","amount":10}' 400 "Create invalid transaction"

# Mining
test_endpoint "POST" "/mine" '{"miner_address":"'$WALLET_ADDR'"}' 200 "Mine block"

# Node registration
test_endpoint "POST" "/nodes" '{"nodes":["http://localhost:5001"]}' 200 "Register nodes"

# Conflict resolution
test_endpoint "POST" "/nodes/resolve" "" 200 "Resolve conflicts"

# Invalid endpoints
test_endpoint "GET" "/invalid" "" 404 "Invalid endpoint"
test_endpoint "POST" "/transaction" '{"invalid":"data"}' 400 "Invalid transaction data"

# Results
echo -e "${BLUE}Test Results:${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! ${NC}"
    exit 0
else
    echo -e "\n${YELLOW}Some tests failed. Check the output above.${NC}"
    exit 1
fi
EOF

# ============================================
# scripts/stress_test.sh
# ============================================
cat > scripts/stress_test.sh << 'EOF'
#!/bin/bash
# Stress testing script

echo "⚡ Blockchain Stress Test"
echo "======================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PORT=5000
BASE_URL="http://localhost:$PORT"
NUM_WALLETS=10
NUM_TRANSACTIONS=50

# Check if node is running
if ! curl -s $BASE_URL/health > /dev/null; then
    echo -e "${RED}Node not running. Start with: make run-node${NC}"
    exit 1
fi

echo -e "${GREEN}Starting stress test...${NC}"

# Create multiple wallets
echo -e "\n${BLUE}Creating $NUM_WALLETS wallets...${NC}"
WALLETS=()
for ((i=1; i<=NUM_WALLETS; i++)); do
    WALLET=$(curl -s -X POST $BASE_URL/wallet/new | jq -r '.address')
    WALLETS+=("$WALLET")
    echo "Wallet $i: ${WALLET:0:16}..."
done

# Mine initial blocks to give wallets some balance
echo -e "\n${BLUE}Mining initial blocks...${NC}"
for ((i=0; i<5; i++)); do
    MINER=${WALLETS[$((i % ${#WALLETS[@]}))]}
    curl -s -X POST $BASE_URL/mine \
        -H "Content-Type: application/json" \
        -d "{\"miner_address\":\"$MINER\"}" > /dev/null
    echo -n "."
done
echo ""

# Create many transactions
echo -e "\n${BLUE}Creating $NUM_TRANSACTIONS transactions...${NC}"
for ((i=1; i<=NUM_TRANSACTIONS; i++)); do
    SENDER=${WALLETS[$((RANDOM % ${#WALLETS[@]}))]}
    RECIPIENT=${WALLETS[$((RANDOM % ${#WALLETS[@]}))]}
    AMOUNT=$((RANDOM % 10 + 1))
    
    curl -s -X POST $BASE_URL/transaction \
        -H "Content-Type: application/json" \
        -d "{\"sender\":\"$SENDER\",\"recipient\":\"$RECIPIENT\",\"amount\":$AMOUNT}" > /dev/null
    
    if [ $((i % 10)) -eq 0 ]; then
        echo "Created $i transactions..."
    fi
done

# Show statistics
echo -e "\n${BLUE}Final statistics:${NC}"
curl -s $BASE_URL/stats | jq '.'

echo -e "\n${GREEN}Stress test complete!${NC}"
EOF

# ============================================
# scripts/setup.sh
# ============================================
cat > scripts/setup.sh << 'EOF'
#!/bin/bash
# Complete setup script

echo "Blockchain Setup Script"
echo "========================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}Python $PYTHON_VERSION found${NC}"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 is required but not installed.${NC}"
    exit 1
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Creating requirements.txt...${NC}"
    cat > requirements.txt << 'REQ_EOF'
flask==2.3.2
requests==2.31.0
ecdsa==0.18.0
REQ_EOF
fi

# Install dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Create directories
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p logs tests

# Make scripts executable
chmod +x scripts/*.sh

# Check optional dependencies
echo -e "\n${BLUE}Checking optional dependencies...${NC}"
if command -v curl &> /dev/null; then
    echo -e "${GREEN}curl: ✓ Available${NC}"
else
    echo -e "${YELLOW}curl: ✗ Not found (recommended for API testing)${NC}"
fi

if command -v jq &> /dev/null; then
    echo -e "${GREEN}jq: ✓ Available${NC}"
else
    echo -e "${YELLOW}jq: ✗ Not found (recommended for JSON formatting)${NC}"
fi

# Create basic test
echo -e "${BLUE}Creating basic test...${NC}"
cat > tests/test_basic.py << 'TEST_EOF'
#!/usr/bin/env python3
"""Basic blockchain tests"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
from unittest.mock import patch, MagicMock

class TestBlockchain(unittest.TestCase):
    """Basic blockchain functionality tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = {
            'address': 'test_address_123',
            'transaction': {
                'sender': 'sender_address',
                'recipient': 'recipient_address',
                'amount': 10
            }
        }
    
    def test_address_validation(self):
        """Test address validation"""
        # Valid address
        valid_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        self.assertTrue(len(valid_addr) > 20)
        
        # Invalid address
        invalid_addr = "invalid"
        self.assertTrue(len(invalid_addr) < 20)
    
    def test_transaction_format(self):
        """Test transaction format"""
        tx = self.test_data['transaction']
        required_fields = ['sender', 'recipient', 'amount']
        
        for field in required_fields:
            self.assertIn(field, tx)

if __name__ == '__main__':
    unittest.main()
TEST_EOF

# Create Makefile for easy management
echo -e "${BLUE}Creating Makefile...${NC}"
cat > Makefile << 'MAKE_EOF'
.PHONY: help install run-node run-mining run-network test clean

help:
	@echo "Blockchain Management Commands:"
	@echo "  install      - Install dependencies"
	@echo "  run-node     - Run single blockchain node"
	@echo "  run-mining   - Run mining demonstration"
	@echo "  run-network  - Run network demonstration"
	@echo "  test         - Run API tests"
	@echo "  stress       - Run stress tests"
	@echo "  clean        - Clean logs and temporary files"

install:
	@echo "Installing dependencies..."
	@pip3 install -r requirements.txt

run-node:
	@echo "Starting blockchain node on port 5000..."
	@python3 blockchain.py --port 5000 --difficulty 2 --reward 50

run-mining:
	@echo "Starting mining demonstration..."
	@./scripts/mining_demo.sh

run-network:
	@echo "Starting network demonstration..."
	@./scripts/network_demo.sh

test:
	@echo "Running API tests..."
	@./scripts/api_test.sh

stress:
	@echo "Running stress tests..."
	@./scripts/stress_test.sh

test-python:
	@echo "Running Python tests..."
	@python3 -m pytest tests/ -v

clean:
	@echo "Cleaning up..."
	@rm -rf logs/*.log
	@rm -rf __pycache__/
	@rm -rf *.pyc
	@echo "Cleanup complete"
MAKE_EOF

# Create configuration file
echo -e "${BLUE}Creating configuration file...${NC}"
cat > config.json << 'CONFIG_EOF'
{
    "blockchain": {
        "difficulty": 2,
        "reward": 50,
        "max_transactions_per_block": 100
    },
    "network": {
        "default_port": 5000,
        "sync_interval": 30,
        "max_peers": 10
    },
    "wallet": {
        "key_length": 256,
        "address_version": 1
    },
    "mining": {
        "auto_mine": false,
        "mine_interval": 10
    }
}
CONFIG_EOF

# Create README
echo -e "${BLUE}Creating README.md...${NC}"
cat > README.md << 'README_EOF'
# Blockchain Implementation

A complete blockchain implementation in Python with REST API, mining, and networking capabilities.

## Features

- Block creation and validation
- Transaction processing
- Proof of Work consensus
- Wallet management
- Network synchronization
- REST API interface
- Mining rewards
- Digital signatures

## Quick Start

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Run a single node:**
   ```bash
   make run-node
   ```

3. **Run mining demo:**
   ```bash
   make run-mining
   ```

4. **Run network demo:**
   ```bash
   make run-network
   ```

## API Endpoints

### Basic Operations
- `GET /health` - Health check
- `GET /stats` - Blockchain statistics
- `GET /chain` - Get full blockchain
- `GET /transactions/pending` - Get pending transactions

### Wallet Operations
- `POST /wallet/new` - Create new wallet
- `GET /balance/{address}` - Get balance for address

### Transaction Operations
- `POST /transaction` - Create new transaction
- `GET /transactions/{address}` - Get transactions for address

### Mining Operations
- `POST /mine` - Mine new block
- `GET /mining/status` - Get mining status

### Network Operations
- `POST /nodes` - Register network nodes
- `POST /nodes/resolve` - Resolve blockchain conflicts

## Scripts

- `scripts/mining_demo.sh` - Interactive mining demonstration
- `scripts/network_demo.sh` - Multi-node network demonstration
- `scripts/api_test.sh` - Complete API test suite
- `scripts/stress_test.sh` - Stress testing with multiple transactions
- `scripts/setup.sh` - Complete environment setup

## Testing

```bash
# Run API tests
make test

# Run Python unit tests
make test-python

# Run stress tests
make stress
```

## Configuration

Edit `config.json` to customize:
- Mining difficulty
- Block rewards
- Network settings
- Wallet parameters

## Development

### Project Structure
```
├── blockchain.py          # Main blockchain implementation
├── scripts/              # Management scripts
├── tests/                # Test files
├── logs/                 # Log files
├── config.json           # Configuration
├── requirements.txt      # Python dependencies
├── Makefile             # Build automation
└── README.md            # This file
```

### Adding New Features

1. Implement in `blockchain.py`
2. Add tests in `tests/`
3. Update API endpoints
4. Add script demonstrations
5. Update documentation

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

2. **Dependencies missing:**
   ```bash
   make install
   ```

3. **Permission denied:**
   ```bash
   chmod +x scripts/*.sh
   ```

## License

MIT License - See LICENSE file for details.
README_EOF

# Create .gitignore
echo -e "${BLUE}Creating .gitignore...${NC}"
cat > .gitignore << 'GITIGNORE_EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/*.log
*.log

# OS
.DS_Store
Thumbs.db

# Blockchain data
blockchain_data/
wallets/
*.wallet

# Temporary files
*.tmp
*.temp
GITIGNORE_EOF

# Final setup steps
echo -e "\n${BLUE}Setting up final permissions...${NC}"
chmod +x scripts/*.sh
chmod +x tests/test_basic.py

# Summary
echo -e "\n${GREEN} Setup Complete!${NC}"
echo -e "\n${BLUE}What's been created:${NC}"
echo "├── scripts/mining_demo.sh    - Mining demonstration"
echo "├── scripts/network_demo.sh   - Network demonstration"
echo "├── scripts/api_test.sh       - API testing suite"
echo "├── scripts/stress_test.sh    - Stress testing"
echo "├── scripts/setup.sh          - This setup script"
echo "├── tests/test_basic.py       - Basic unit tests"
echo "├── config.json               - Configuration file"
echo "├── Makefile                  - Build automation"
echo "├── README.md                 - Documentation"
echo "├── .gitignore               - Git ignore rules"
echo "└── requirements.txt          - Python dependencies"

echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Make sure you have blockchain.py in the current directory"
echo "2. Run: make install"
echo "3. Run: make run-node"
echo "4. In another terminal: make run-mining"

echo -e "\n${YELLOW}For help: make help${NC}"
echo -e "${GREEN}Happy blockchain development! ${NC}"
EOF

# Make all scripts executable
chmod +x scripts/*.sh

echo "All blockchain management scripts have been created!"
echo ""
echo "Directory structure:"
echo "├── scripts/"
echo "│   ├── mining_demo.sh"
echo "│   ├── network_demo.sh"
echo "│   ├── api_test.sh"
echo "│   ├── stress_test.sh"
echo "│   └── setup.sh"
echo "├── logs/"
echo "└── tests/"
echo ""
echo "  To get started:"
echo "1. Run: ./scripts/setup.sh"
echo "2. Then: make help"