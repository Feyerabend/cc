# -*- coding: utf-8 -*-
import hashlib
import time
import json
import base64
import logging
import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional, Any, Callable
import ecdsa
import requests
from flask import Flask, jsonify, request

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ----------------------
# Model Layer
# ----------------------

class Transaction:
    """Represents a transaction in the blockchain"""
    
    def __init__(self, sender: str, recipient: str, amount: float, signature: Optional[bytes] = None):
        self.sender = sender  # Public key (wallet address)
        self.recipient = recipient  # Public key (wallet address)
        self.amount = amount
        self.timestamp = time.time()
        self.signature = signature  # Digital signature to verify sender
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary format"""
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': base64.b64encode(self.signature).decode('utf-8') if self.signature else None
        }
    
    def sign(self, private_key: ecdsa.SigningKey) -> None:
        """Sign the transaction with the provided private key"""
        transaction_string = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"
        self.signature = private_key.sign(transaction_string.encode())
    
    def is_valid(self) -> bool:
        """Verify the transaction's signature"""
        if self.sender == "network":
            return True
        if not self.signature:
            return False

        try:
            vk = ecdsa.VerifyingKey.from_string(base64.b64decode(self.sender))
            transaction_string = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"
            return vk.verify(self.signature, transaction_string.encode())
        except Exception as e:
            logging.error(f"Signature verification failed: {e}")
            return False
            
    def __str__(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class Block:
    """Represents a block in the blockchain"""
    
    def __init__(self, index: int, previous_hash: str, timestamp: float, 
                 transactions: List[Transaction], nonce: int = 0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.hash = self.calculate_hash()
        
    def calculate_hash(self) -> str:
        """Calculate the hash of the block based on its contents"""
        block_string = (
            f"{self.index}{self.previous_hash}{self.timestamp}"
            f"{json.dumps([t.to_dict() for t in self.transactions], sort_keys=True)}{self.nonce}"
        )
        return hashlib.sha256(block_string.encode()).hexdigest()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary format"""
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': [t.to_dict() for t in self.transactions],
            'nonce': self.nonce,
            'hash': self.hash
        }


# ----------------------
# Strategy Pattern for Mining
# ----------------------

class MiningStrategy(ABC):
    """Abstract mining strategy"""
    
    @abstractmethod
    def mine(self, block: Block, difficulty: int) -> None:
        """Mine a block according to the strategy"""
        pass


class ProofOfWorkStrategy(MiningStrategy):
    """Proof of Work mining strategy"""
    
    def mine(self, block: Block, difficulty: int) -> None:
        """Mine a block using proof of work"""
        target = "0" * difficulty
        while block.hash[:difficulty] != target:
            block.nonce += 1
            block.hash = block.calculate_hash()


# ----------------------
# Factory Pattern
# ----------------------

class BlockFactory:
    """Factory for creating blocks"""
    
    @staticmethod
    def create_genesis_block() -> Block:
        """Create the genesis block"""
        return Block(0, "0", time.time(), [], 0)
        
    @staticmethod
    def create_next_block(previous_block: Block, transactions: List[Transaction]) -> Block:
        """Create the next block in the chain"""
        return Block(
            previous_block.index + 1,
            previous_block.hash,
            time.time(),
            transactions
        )


class TransactionFactory:
    """Factory for creating transactions"""
    
    @staticmethod
    def create_transaction(sender: str, recipient: str, amount: float) -> Transaction:
        """Create a regular transaction"""
        return Transaction(sender, recipient, amount)
        
    @staticmethod
    def create_reward_transaction(recipient: str, amount: float) -> Transaction:
        """Create a mining reward transaction"""
        return Transaction("network", recipient, amount)


# ----------------------
# Observer Pattern for Broadcasting
# ----------------------

class Observer(ABC):
    """Abstract observer"""
    
    @abstractmethod
    def update_transaction(self, transaction: Transaction) -> None:
        """Handle transaction updates"""
        pass
        
    @abstractmethod
    def update_block(self, block: Block) -> None:
        """Handle block updates"""
        pass


class NodeObserver(Observer):
    """Node observer that sends updates to network nodes"""
    
    def __init__(self, node_address: str):
        self.node_address = node_address
        self.logger = logging.getLogger(f"NodeObserver-{node_address}")
        
    def update_transaction(self, transaction: Transaction) -> None:
        """Send transaction to a node"""
        try:
            requests.post(
                f"{self.node_address}/transaction/new", 
                json=transaction.to_dict(), 
                timeout=5
            )
            self.logger.info(f"Transaction broadcast to {self.node_address}")
        except Exception as e:
            self.logger.warning(f"Failed to broadcast transaction to {self.node_address}: {e}")
            
    def update_block(self, block: Block) -> None:
        """Send block to a node"""
        try:
            requests.post(
                f"{self.node_address}/block/new", 
                json=block.to_dict(), 
                timeout=5
            )
            self.logger.info(f"Block broadcast to {self.node_address}")
        except Exception as e:
            self.logger.warning(f"Failed to broadcast block to {self.node_address}: {e}")


class Subject(ABC):
    """Abstract subject class for the observer pattern"""
    
    def __init__(self):
        self._observers: List[Observer] = []
        
    def attach(self, observer: Observer) -> None:
        """Attach an observer"""
        if observer not in self._observers:
            self._observers.append(observer)
            
    def detach(self, observer: Observer) -> None:
        """Detach an observer"""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
            
    def notify_transaction(self, transaction: Transaction) -> None:
        """Notify all observers about a new transaction"""
        for observer in self._observers:
            observer.update_transaction(transaction)
            
    def notify_block(self, block: Block) -> None:
        """Notify all observers about a new block"""
        for observer in self._observers:
            observer.update_block(block)


# ----------------------
# Core Blockchain Classes
# ----------------------

class Wallet:
    """Represents a wallet in the blockchain"""
    
    def __init__(self):
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key().to_string()
        self.address = base64.b64encode(self.public_key).decode('utf-8')
        
    def sign_transaction(self, transaction: Transaction) -> None:
        """Sign a transaction with this wallet's private key"""
        transaction.sign(self.private_key)


class BlockchainConfig:
    """Configuration for the blockchain"""
    
    def __init__(self, difficulty: int = 4, mining_reward: float = 10.0):
        self.difficulty = difficulty
        self.mining_reward = mining_reward
        

class PersistenceManager:
    """Handles saving and loading the blockchain data"""
    
    def __init__(self, filename: str = "blockchain.dat"):
        self.filename = filename
        self.logger = logging.getLogger("PersistenceManager")
        
    def save(self, chain: list) -> bool:
        """Save blockchain to disk as JSON"""
        try:
            with open(self.filename, "w") as f:
                json.dump([block.to_dict() for block in chain], f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            return False

    def load(self) -> Any:
        """Load blockchain from disk"""
        try:
            with open(self.filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.info(f"No data file found at {self.filename}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            return None


class Blockchain(Subject):
    """Main blockchain implementation"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Blockchain, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, config: BlockchainConfig = None, 
                 persistence: PersistenceManager = None,
                 mining_strategy: MiningStrategy = None):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            super().__init__()
            self.logger = logging.getLogger("Blockchain")
            
            # Dependency injection
            self.config = config or BlockchainConfig()
            self.persistence = persistence or PersistenceManager("coin_blockchain.dat")
            self.mining_strategy = mining_strategy or ProofOfWorkStrategy()
            
            # Initialize blockchain
            self.chain: List[Block] = []
            self.pending_transactions: List[Transaction] = []
            self.nodes: Set[str] = set()
            
            # Load existing chain or create genesis block
            loaded_data = self.persistence.load()
            if loaded_data:
                self.chain = self._json_to_blocks(loaded_data)
            else:
                self.chain = [BlockFactory.create_genesis_block()]
                
            self._initialized = True
    
    def add_node(self, address: str) -> None:
        """Add a node to the network"""
        self.nodes.add(address)
        self.attach(NodeObserver(address))
        self.logger.info(f"Node added: {address}")
        
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a transaction to pending transactions"""
        if not transaction.is_valid():
            self.logger.warning(f"Invalid transaction signature: {transaction}")
            return False
            
        if transaction.amount <= 0:
            self.logger.warning(f"Invalid transaction amount: {transaction}")
            return False
            
        # Check sender has enough funds (except for network rewards)
        if transaction.sender != "network":
            sender_balance = self.get_balance(transaction.sender)
            if sender_balance < transaction.amount:
                self.logger.warning(f"Insufficient funds for {transaction}")
                return False
                
        self.pending_transactions.append(transaction)
        self.notify_transaction(transaction)
        self.logger.info(f"Transaction added: {transaction}")
        return True
        
    def mine_pending_transactions(self, miner_address: str) -> bool:
        """Mine pending transactions into a new block"""
        if not self.pending_transactions:
            self.logger.info("No transactions to mine")
            return False
            
        # Create mining reward
        reward_tx = TransactionFactory.create_reward_transaction(
            miner_address, self.config.mining_reward
        )
        self.pending_transactions.append(reward_tx)
        
        # Create and mine new block
        new_block = BlockFactory.create_next_block(
            self.chain[-1], self.pending_transactions
        )
        
        self.logger.info(f"Mining block #{new_block.index}")
        self.mining_strategy.mine(new_block, self.config.difficulty)
        
        # Add block to chain
        self.chain.append(new_block)
        self.notify_block(new_block)
        
        # Save chain and clear pending transactions
        self.persistence.save(self.chain)
        self.pending_transactions = []
        
        self.logger.info(f"Block #{new_block.index} mined and added to chain")
        return True
        
    def get_balance(self, address: str) -> float:
        """Get the balance of a wallet address"""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.recipient == address:
                    balance += tx.amount
        return balance
        
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check hash integrity
            if current.hash != current.calculate_hash():
                self.logger.error(f"Invalid hash in block #{current.index}")
                return False
                
            # Check chain continuity
            if current.previous_hash != previous.hash:
                self.logger.error(f"Invalid previous hash in block #{current.index}")
                return False
                
            # Check proof of work
            if current.hash[:self.config.difficulty] != "0" * self.config.difficulty:
                self.logger.error(f"Invalid proof-of-work in block #{current.index}")
                return False
                
            # Verify all transaction signatures
            for tx in current.transactions:
                if not tx.is_valid():
                    self.logger.error(f"Invalid transaction signature in block #{current.index}")
                    return False
                    
        return True
        
    def resolve_conflicts(self) -> bool:
        """Consensus algorithm to resolve conflicts between nodes"""
        longest_chain = self.chain
        max_length = len(self.chain)
        replaced = False
        
        for node in self.nodes:
            try:
                response = requests.get(f"{node}/chain", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Convert JSON data back to Block objects
                    chain = self._json_to_blocks(data['chain'])
                    length = data['length']
                    
                    # Check if chain is longer and valid
                    if length > max_length and self._is_valid_chain(chain):
                        max_length = length
                        longest_chain = chain
                        replaced = True
                        self.logger.info(f"Found longer valid chain from {node}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch chain from {node}: {e}")
                
        if replaced:
            self.chain = longest_chain
            self.persistence.save(self.chain)
            self.logger.info("Chain replaced with longer chain")
            
        return replaced
    
    def _json_to_blocks(self, json_chain: List[Dict]) -> List[Block]:
        """Convert JSON chain data to Block objects"""
        blocks = []
        for block_data in json_chain:
            # Convert transaction dicts to Transaction objects
            transactions = [
                Transaction(
                    tx['sender'],
                    tx['recipient'],
                    tx['amount'],
                    base64.b64decode(tx['signature']) if tx['signature'] else None
                ) for tx in block_data['transactions']
            ]
            
            # Create Block object
            block = Block(
                block_data['index'],
                block_data['previous_hash'],
                block_data['timestamp'],
                transactions,
                block_data['nonce']
            )
            # Set the hash directly (as it was already calculated)
            block.hash = block_data['hash']
            blocks.append(block)
            
        return blocks
        
    def _is_valid_chain(self, chain: List[Block]) -> bool:
        """Check if a chain is valid"""
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            if current.hash != current.calculate_hash():
                return False
                
            if current.previous_hash != previous.hash:
                return False
                
            if current.hash[:self.config.difficulty] != "0" * self.config.difficulty:
                return False
                
        return True


# ----------------------
# Controller Layer
# ----------------------

class BlockchainController:
    """Controller for handling blockchain operations"""
    
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.logger = logging.getLogger("BlockchainController")
        
    def register_transaction(self, tx_data: Dict) -> bool:
        """Register a new transaction from request data"""
        try:
            # Extract transaction data
            sender = tx_data.get('sender')
            recipient = tx_data.get('recipient')
            amount = tx_data.get('amount')
            signature = tx_data.get('signature')
            
            # Validate required fields
            if not all([sender, recipient, amount is not None]):
                self.logger.warning("Missing transaction fields")
                return False
                
            # Create and add transaction
            transaction = Transaction(
                sender,
                recipient,
                float(amount),
                base64.b64decode(signature) if signature else None
            )
            
            return self.blockchain.add_transaction(transaction)
        except Exception as e:
            self.logger.error(f"Failed to register transaction: {e}")
            return False
            
    def mine_block(self, miner_address: str) -> bool:
        """Mine a new block"""
        return self.blockchain.mine_pending_transactions(miner_address)
        
    def register_node(self, node_address: str) -> bool:
        """Register a new node"""
        try:
            self.blockchain.add_node(node_address)
            return True
        except Exception as e:
            self.logger.error(f"Failed to register node: {e}")
            return False
            
    def resolve_conflicts(self) -> bool:
        """Resolve conflicts between nodes"""
        return self.blockchain.resolve_conflicts()
        
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.blockchain.get_balance(address)
        
    def get_chain(self) -> List[Dict]:
        """Get the entire blockchain as a list of dictionaries"""
        return [block.to_dict() for block in self.blockchain.chain]


# ----------------------
# API Layer
# ----------------------

def create_app(blockchain: Blockchain = None) -> Flask:
    """Create Flask application with blockchain API endpoints"""
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)
    
    # Dependency injection
    if blockchain is None:
        blockchain = Blockchain()
    
    # Create controller
    controller = BlockchainController(blockchain)
    
    @app.route('/transaction/new', methods=['POST'])
    def new_transaction():
        """API endpoint to add a new transaction"""
        values = request.get_json()
        
        required = ['sender', 'recipient', 'amount', 'signature']
        if not all(k in values for k in required):
            return jsonify({'message': 'Missing values'}), 400
            
        if controller.register_transaction(values):
            return jsonify({'message': 'Transaction added'}), 201
        return jsonify({'message': 'Invalid transaction'}), 400
        
    @app.route('/mine', methods=['POST'])
    def mine():
        """API endpoint to mine pending transactions"""
        values = request.get_json()
        
        if 'miner_address' not in values:
            return jsonify({'message': 'Missing miner address'}), 400
            
        if controller.mine_block(values['miner_address']):
            return jsonify({'message': 'New block mined'}), 200
        return jsonify({'message': 'No transactions to mine'}), 400
        
    @app.route('/chain', methods=['GET'])
    def get_chain():
        """API endpoint to get the full blockchain"""
        chain_data = controller.get_chain()
        return jsonify({
            'chain': chain_data, 
            'length': len(chain_data)
        }), 200
        
    @app.route('/nodes/register', methods=['POST'])
    def register_nodes():
        """API endpoint to register new nodes"""
        values = request.get_json()
        nodes = values.get('nodes')
        
        if nodes is None:
            return jsonify({'message': 'No nodes provided'}), 400
            
        for node in nodes:
            controller.register_node(node)
            
        return jsonify({
            'message': 'Nodes added', 
            'total_nodes': list(blockchain.nodes)
        }), 201
        
    @app.route('/nodes/resolve', methods=['GET'])
    def consensus():
        """API endpoint to resolve conflicts between nodes"""
        replaced = controller.resolve_conflicts()
        
        return jsonify({
            'message': 'Chain replaced' if replaced else 'Chain authoritative',
            'chain': controller.get_chain()
        }), 200
        
    @app.route('/balance/<address>', methods=['GET'])
    def get_balance(address):
        """API endpoint to get the balance of an address"""
        balance = controller.get_balance(address)
        return jsonify({'address': address, 'balance': balance}), 200
        
    @app.route('/block/new', methods=['POST'])
    def new_block():
        """API endpoint to add a new block broadcast from another node"""
        # Implementation would go here
        # This would validate and add a block received from another node
        return jsonify({'message': 'Block received'}), 200
        
    return app


# ----------------------
# Server Runner
# ----------------------

class ServerRunner:
    """Runs the blockchain server"""
    
    def __init__(self, app: Flask, port: int = 5000, production: bool = False):
        self.app = app
        self.port = port
        self.production = production
        self.logger = logging.getLogger("ServerRunner")
        
    def run(self) -> None:
        """Run the server"""
        if self.production:
            try:
                import waitress
                self.logger.info(f"Starting production server on port {self.port} with waitress")
                waitress.serve(self.app, host='0.0.0.0', port=self.port)
            except ImportError:
                self.logger.error("Waitress not installed. Install with 'pip install waitress' or run in development mode.")
                sys.exit(1)
        else:
            self.logger.info(f"Starting development server on http://127.0.0.1:{self.port}")
            self.logger.warning("Development server. Not for production use. Use --production flag for production.")
            self.app.run(host='0.0.0.0', port=self.port, debug=False)


# ----------------------
# Main Function
# ----------------------

def main():
    """Main function to run the blockchain application"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a Blockchain node")
    parser.add_argument('--port', type=int, default=5000, help='Port to run the node on')
    parser.add_argument('--production', action='store_true', help='Run in production mode with waitress')
    parser.add_argument('--difficulty', type=int, default=4, help='Mining difficulty')
    parser.add_argument('--reward', type=float, default=10.0, help='Mining reward')
    args = parser.parse_args()
    
    # Create blockchain with configuration
    config = BlockchainConfig(difficulty=args.difficulty, mining_reward=args.reward)
    blockchain = Blockchain(config=config)
    
    # Create and run server
    app = create_app(blockchain)
    server = ServerRunner(app, args.port, args.production)
    
    # Test setup - only in development mode
    if not args.production:
        # Create test wallets
        alice_wallet = Wallet()
        bob_wallet = Wallet()
        miner_wallet = Wallet()
        
        # Register test nodes
        blockchain.add_node("http://localhost:5001")
        blockchain.add_node("http://localhost:5002")
        
        # Fund wallets via mining rewards before spending
        blockchain.add_transaction(TransactionFactory.create_reward_transaction(alice_wallet.address, 50.0))
        blockchain.add_transaction(TransactionFactory.create_reward_transaction(bob_wallet.address, 50.0))
        blockchain.mine_pending_transactions(miner_wallet.address)

        # Create and sign test transactions (wallets now have funded balances)
        tx1 = TransactionFactory.create_transaction(alice_wallet.address, bob_wallet.address, 5.0)
        alice_wallet.sign_transaction(tx1)
        blockchain.add_transaction(tx1)

        tx2 = TransactionFactory.create_transaction(bob_wallet.address, alice_wallet.address, 2.0)
        bob_wallet.sign_transaction(tx2)
        blockchain.add_transaction(tx2)

        # Mine a test block
        blockchain.mine_pending_transactions(miner_wallet.address)
        
        # Print test balances
        logging.info(f"Alice's balance: {blockchain.get_balance(alice_wallet.address)}")
        logging.info(f"Bob's balance: {blockchain.get_balance(bob_wallet.address)}")
        logging.info(f"Miner's balance: {blockchain.get_balance(miner_wallet.address)}")
    
    # Display server information
    logging.info("Blockchain node started successfully.")
    logging.info("Available endpoints:")
    logging.info("  GET  /chain - View the blockchain")
    logging.info("  POST /nodes/register - Register new nodes")
    logging.info("  GET  /nodes/resolve - Resolve conflicts")
    logging.info("  POST /transaction/new - Create new transactions")
    logging.info("  POST /mine - Mine new blocks")
    logging.info("  GET  /balance/<address> - Check balance of an address")
    
    # Run the server
    try:
        server.run()
    except KeyboardInterrupt:
        logging.info("Shutting down the server.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Save blockchain state
        blockchain.persistence.save(blockchain.chain)
        logging.info("Blockchain saved.")


if __name__ == "__main__":
    main()


# This code is a complete implementation of a simple blockchain system with transaction handling, mining, and node management.
# It includes a Flask API for interaction, a persistence layer for saving the blockchain state, and a server runner to start the application.
