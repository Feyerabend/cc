# -*- coding: utf-8 -*-
import hashlib
import time
import json
import base64
import logging
import sys
import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager

import ecdsa
import requests
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blockchain.log')
    ]
)



class TransactionStatus(Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass
class TransactionData:
    """Immutable transaction data structure"""
    sender: str
    recipient: str
    amount: float
    timestamp: float
    signature: Optional[bytes] = None
    status: TransactionStatus = TransactionStatus.PENDING
    
    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        if not self.sender or not self.recipient:
            raise ValueError("Sender and recipient cannot be empty")


class Transaction:
    """Transaction with validation and signing capabilities"""
    
    def __init__(self, sender: str, recipient: str, amount: float):
        self._data = TransactionData(sender, recipient, amount, time.time())
        self._hash: Optional[str] = None
        
    @property
    def data(self) -> TransactionData:
        """Get immutable transaction data"""
        return self._data
        
    @property
    def hash(self) -> str:
        """Get transaction hash (cached)"""
        if self._hash is None:
            content = f"{self._data.sender}{self._data.recipient}{self._data.amount}{self._data.timestamp}"
            self._hash = hashlib.sha256(content.encode()).hexdigest()
        return self._hash
    
    def sign(self, private_key: ecdsa.SigningKey) -> None:
        """Sign the transaction"""
        if self._data.signature is not None:
            raise ValueError("Transaction already signed")
            
        signature = private_key.sign(self.hash.encode())
        # Create new data with signature (immutable update)
        self._data = TransactionData(
            self._data.sender,
            self._data.recipient,
            self._data.amount,
            self._data.timestamp,
            signature,
            self._data.status
        )
    
    def verify_signature(self) -> bool:
        """Verify transaction signature"""
        if self._data.sender == "network":
            return True
        if self._data.signature is None:
            return False
            
        try:
            public_key_bytes = base64.b64decode(self._data.sender)
            verifying_key = ecdsa.VerifyingKey.from_string(
                public_key_bytes, 
                curve=ecdsa.SECP256k1
            )
            return verifying_key.verify(self._data.signature, self.hash.encode())
        except Exception as e:
            logging.error(f"Signature verification failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = asdict(self._data)
        result['signature'] = base64.b64encode(self._data.signature).decode() if self._data.signature else None
        result['status'] = self._data.status.value
        result['hash'] = self.hash
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create transaction from dictionary"""
        tx = cls(data['sender'], data['recipient'], data['amount'])
        
        # Restore signature if present
        if data.get('signature'):
            signature = base64.b64decode(data['signature'])
            tx._data = TransactionData(
                data['sender'],
                data['recipient'],
                data['amount'],
                data['timestamp'],
                signature,
                TransactionStatus(data.get('status', 'pending'))
            )
        
        return tx


@dataclass
class BlockHeader:
    """Block header containing metadata"""
    index: int
    previous_hash: str
    timestamp: float
    merkle_root: str
    nonce: int = 0
    difficulty: int = 4
    
    def calculate_hash(self) -> str:
        """Calculate block header hash"""
        content = f"{self.index}{self.previous_hash}{self.timestamp}{self.merkle_root}{self.nonce}{self.difficulty}"
        return hashlib.sha256(content.encode()).hexdigest()


class Block:
    """Immutable block implementation"""
    
    def __init__(self, header: BlockHeader, transactions: List[Transaction]):
        self._header = header
        self._transactions = transactions.copy()  # Defensive copy
        self._hash: Optional[str] = None
        self._merkle_root: Optional[str] = None
        
        # Update merkle root in header
        self._header.merkle_root = self.merkle_root
    
    @property
    def header(self) -> BlockHeader:
        """Get block header"""
        return self._header
    
    @property
    def transactions(self) -> List[Transaction]:
        """Get transactions (defensive copy)"""
        return self._transactions.copy()
    
    @property
    def hash(self) -> str:
        """Get block hash (cached)"""
        if self._hash is None:
            self._hash = self._header.calculate_hash()
        return self._hash
    
    @property
    def merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if self._merkle_root is None:
            if not self._transactions:
                self._merkle_root = hashlib.sha256(b"").hexdigest()
            else:
                tx_hashes = [tx.hash for tx in self._transactions]
                self._merkle_root = self._calculate_merkle_root(tx_hashes)
        return self._merkle_root
    
    def _calculate_merkle_root(self, hashes: List[str]) -> str:
        """Calculate Merkle root from transaction hashes"""
        if len(hashes) == 1:
            return hashes[0]
            
        # Ensure even number of hashes
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])
        
        # Combine pairs
        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
        
        return self._calculate_merkle_root(next_level)
    
    def mine(self, difficulty: int) -> 'Block':
        """Mine the block and return new block with updated nonce"""
        target = "0" * difficulty
        new_header = BlockHeader(
            self._header.index,
            self._header.previous_hash,
            self._header.timestamp,
            self._header.merkle_root,
            0,
            difficulty
        )
        
        while True:
            test_hash = new_header.calculate_hash()
            if test_hash.startswith(target):
                break
            new_header.nonce += 1
            
        return Block(new_header, self._transactions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return {
            'index': self._header.index,
            'previous_hash': self._header.previous_hash,
            'timestamp': self._header.timestamp,
            'merkle_root': self.merkle_root,
            'nonce': self._header.nonce,
            'difficulty': self._header.difficulty,
            'hash': self.hash,
            'transactions': [tx.to_dict() for tx in self._transactions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """Create block from dictionary"""
        header = BlockHeader(
            data['index'],
            data['previous_hash'],
            data['timestamp'],
            data['merkle_root'],
            data['nonce'],
            data.get('difficulty', 4)
        )
        
        transactions = [Transaction.from_dict(tx_data) for tx_data in data['transactions']]
        return cls(header, transactions)



class Wallet:
    """Secure wallet implementation"""
    
    def __init__(self, private_key: Optional[ecdsa.SigningKey] = None):
        self._private_key = private_key or ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self._public_key = self._private_key.get_verifying_key()
        self._address = base64.b64encode(self._public_key.to_string()).decode()
    
    @property
    def address(self) -> str:
        """Get wallet address (public key)"""
        return self._address
    
    def sign_transaction(self, transaction: Transaction) -> None:
        """Sign a transaction with this wallet"""
        if transaction.data.sender != self.address:
            raise ValueError("Cannot sign transaction from different address")
        transaction.sign(self._private_key)
    
    def create_transaction(self, recipient: str, amount: float) -> Transaction:
        """Create and sign a transaction"""
        transaction = Transaction(self.address, recipient, amount)
        self.sign_transaction(transaction)
        return transaction




class ValidationResult:
    """Result of validation operations"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def __bool__(self) -> bool:
        return self.is_valid


class BlockchainValidator:
    """Comprehensive blockchain validation"""
    
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_transaction(self, transaction: Transaction, current_balances: Dict[str, float] = None) -> ValidationResult:
        """Validate a single transaction"""
        errors = []
        
        # Basic validation
        if transaction.data.amount <= 0:
            errors.append("Transaction amount must be positive")
        
        if not transaction.data.sender or not transaction.data.recipient:
            errors.append("Sender and recipient addresses required")
        
        # Signature validation
        if not transaction.verify_signature():
            errors.append("Invalid transaction signature")
        
        # Balance validation (if balances provided)
        if current_balances and transaction.data.sender != "network":
            sender_balance = current_balances.get(transaction.data.sender, 0)
            if sender_balance < transaction.data.amount:
                errors.append(f"Insufficient balance: {sender_balance} < {transaction.data.amount}")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def validate_block(self, block: Block, previous_block: Optional[Block] = None) -> ValidationResult:
        """Validate a single block"""
        errors = []
        
        # Hash validation
        if block.hash != block.header.calculate_hash():
            errors.append("Invalid block hash")
        
        # Previous hash validation
        if previous_block and block.header.previous_hash != previous_block.hash:
            errors.append("Invalid previous block hash")
        
        # Proof of work validation
        target = "0" * self.difficulty
        if not block.hash.startswith(target):
            errors.append(f"Block doesn't meet difficulty requirement: {self.difficulty}")
        
        # Merkle root validation
        if block.header.merkle_root != block.merkle_root:
            errors.append("Invalid Merkle root")
        
        # Transaction validation
        for i, tx in enumerate(block.transactions):
            tx_result = self.validate_transaction(tx)
            if not tx_result:
                errors.extend([f"Transaction {i}: {error}" for error in tx_result.errors])
        
        return ValidationResult(len(errors) == 0, errors)
    
    def validate_chain(self, chain: List[Block]) -> ValidationResult:
        """Validate entire blockchain"""
        errors = []
        
        if not chain:
            errors.append("Empty blockchain")
            return ValidationResult(False, errors)
        
        # Validate genesis block
        genesis = chain[0]
        if genesis.header.index != 0 or genesis.header.previous_hash != "0":
            errors.append("Invalid genesis block")
        
        # Validate each block in sequence
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            
            block_result = self.validate_block(current_block, previous_block)
            if not block_result:
                errors.extend([f"Block {i}: {error}" for error in block_result.errors])
        
        return ValidationResult(len(errors) == 0, errors)




class PersistenceManager:
    """Thread-safe persistence management"""
    
    def __init__(self, filename: str = "blockchain.dat"):
        self.filename = filename
        self.logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.RLock()
    
    @contextmanager
    def _file_lock(self):
        """Context manager for file operations"""
        with self._lock:
            yield
    
    def save_chain(self, chain: List[Block]) -> bool:
        """Save blockchain to disk"""
        try:
            with self._file_lock():
                chain_data = [block.to_dict() for block in chain]
                with open(self.filename, 'w') as f:
                    json.dump(chain_data, f, indent=2)
                self.logger.info(f"Blockchain saved to {self.filename}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to save blockchain: {e}")
            return False
    
    def load_chain(self) -> Optional[List[Block]]:
        """Load blockchain from disk"""
        try:
            with self._file_lock():
                with open(self.filename, 'r') as f:
                    chain_data = json.load(f)
                
                chain = [Block.from_dict(block_data) for block_data in chain_data]
                self.logger.info(f"Blockchain loaded from {self.filename}")
                return chain
        except FileNotFoundError:
            self.logger.info(f"No blockchain file found at {self.filename}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load blockchain: {e}")
            return None




class NetworkManager:
    """Manages network communication between nodes"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def broadcast_transaction(self, transaction: Transaction, nodes: Set[str]) -> int:
        """Broadcast transaction to network nodes"""
        success_count = 0
        for node in nodes:
            try:
                response = requests.post(
                    f"{node}/transaction/new",
                    json=transaction.to_dict(),
                    timeout=self.timeout
                )
                if response.status_code in [200, 201]:
                    success_count += 1
                    self.logger.debug(f"Transaction broadcast to {node}")
            except Exception as e:
                self.logger.warning(f"Failed to broadcast transaction to {node}: {e}")
        
        self.logger.info(f"Transaction broadcast to {success_count}/{len(nodes)} nodes")
        return success_count
    
    def broadcast_block(self, block: Block, nodes: Set[str]) -> int:
        """Broadcast block to network nodes"""
        success_count = 0
        for node in nodes:
            try:
                response = requests.post(
                    f"{node}/block/new",
                    json=block.to_dict(),
                    timeout=self.timeout
                )
                if response.status_code in [200, 201]:
                    success_count += 1
                    self.logger.debug(f"Block broadcast to {node}")
            except Exception as e:
                self.logger.warning(f"Failed to broadcast block to {node}: {e}")
        
        self.logger.info(f"Block broadcast to {success_count}/{len(nodes)} nodes")
        return success_count
    
    def fetch_chain(self, node: str) -> Optional[List[Block]]:
        """Fetch blockchain from a node"""
        try:
            response = requests.get(f"{node}/chain", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return [Block.from_dict(block_data) for block_data in data['chain']]
        except Exception as e:
            self.logger.warning(f"Failed to fetch chain from {node}: {e}")
        return None




@dataclass
class BlockchainConfig:
    """Blockchain configuration"""
    difficulty: int = 4
    mining_reward: float = 10.0
    max_transactions_per_block: int = 100
    block_time_target: int = 600  # 10 minutes in seconds


class Blockchain:
    """Main blockchain implementation with improved architecture"""
    
    def __init__(self, config: BlockchainConfig = None):
        self.config = config or BlockchainConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Core components
        self._chain: List[Block] = []
        self._pending_transactions: List[Transaction] = []
        self._nodes: Set[str] = set()
        self._balances: Dict[str, float] = {}
        
        # Dependencies
        self.validator = BlockchainValidator(self.config.difficulty)
        self.persistence = PersistenceManager("refined_blockchain.json")
        self.network = NetworkManager()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize blockchain
        self._initialize_chain()
    
    def _initialize_chain(self) -> None:
        """Initialize blockchain from persistence or create genesis"""
        loaded_chain = self.persistence.load_chain()
        if loaded_chain:
            validation_result = self.validator.validate_chain(loaded_chain)
            if validation_result:
                self._chain = loaded_chain
                self._recalculate_balances()
                self.logger.info(f"Loaded valid blockchain with {len(self._chain)} blocks")
            else:
                self.logger.error(f"Loaded blockchain is invalid: {validation_result.errors}")
                self._create_genesis_block()
        else:
            self._create_genesis_block()
    
    def _create_genesis_block(self) -> None:
        """Create the genesis block"""
        header = BlockHeader(0, "0", time.time(), "", 0, self.config.difficulty)
        genesis_block = Block(header, [])
        self._chain = [genesis_block]
        self.logger.info("Created genesis block")
    
    @contextmanager
    def _thread_safe_operation(self):
        """Context manager for thread-safe operations"""
        with self._lock:
            yield
    
    def add_node(self, address: str) -> bool:
        """Add a node to the network"""
        try:
            with self._thread_safe_operation():
                self._nodes.add(address)
                self.logger.info(f"Added node: {address}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add node {address}: {e}")
            return False
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a validated transaction to pending pool"""
        try:
            with self._thread_safe_operation():
                # Validate transaction
                validation_result = self.validator.validate_transaction(transaction, self._balances)
                if not validation_result:
                    self.logger.warning(f"Invalid transaction: {validation_result.errors}")
                    return False
                
                # Add to pending pool
                self._pending_transactions.append(transaction)
                
                # Broadcast to network
                if self._nodes:
                    self.network.broadcast_transaction(transaction, self._nodes)
                
                self.logger.info(f"Added transaction: {transaction.hash}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to add transaction: {e}")
            return False
    
    def mine_block(self, miner_address: str) -> Optional[Block]:
        """Mine a new block with pending transactions"""
        try:
            # Set up block under lock (fast)
            with self._thread_safe_operation():
                # Select pending transactions (may be empty — miner still earns reward)
                transactions = self._pending_transactions[:self.config.max_transactions_per_block]

                # Add mining reward
                reward_tx = Transaction("network", miner_address, self.config.mining_reward)
                transactions.append(reward_tx)

                previous_block = self._chain[-1]
                header = BlockHeader(
                    len(self._chain),
                    previous_block.hash,
                    time.time(),
                    "",  # Calculated by Block.__init__
                    0,
                    self.config.difficulty
                )
                block = Block(header, transactions)

            # PoW is CPU-intensive — run outside the lock so other operations aren't blocked
            self.logger.info(f"Mining block #{block.header.index}...")
            start_time = time.time()
            mined_block = block.mine(self.config.difficulty)
            mining_time = time.time() - start_time

            # Commit mined block under lock
            with self._thread_safe_operation():
                previous_block = self._chain[-1]  # Re-check tip after mining
                validation_result = self.validator.validate_block(mined_block, previous_block)
                if not validation_result:
                    self.logger.error(f"Mined block is invalid: {validation_result.errors}")
                    return None

                self._chain.append(mined_block)
                self._update_balances_for_block(mined_block)

                mined_tx_hashes = {tx.hash for tx in mined_block.transactions}
                self._pending_transactions = [
                    tx for tx in self._pending_transactions
                    if tx.hash not in mined_tx_hashes
                ]

                self.persistence.save_chain(self._chain)

                if self._nodes:
                    self.network.broadcast_block(mined_block, self._nodes)

            self.logger.info(
                f"Block #{mined_block.header.index} mined in {mining_time:.2f}s "
                f"with {len(mined_block.transactions)} transactions"
            )
            return mined_block
        except Exception as e:
            self.logger.error(f"Failed to mine block: {e}")
            return None
    
    def _update_balances_for_block(self, block: Block) -> None:
        """Update balance cache for a block"""
        for tx in block.transactions:
            if tx.data.sender != "network":
                self._balances[tx.data.sender] = self._balances.get(tx.data.sender, 0) - tx.data.amount
            self._balances[tx.data.recipient] = self._balances.get(tx.data.recipient, 0) + tx.data.amount
    
    def _recalculate_balances(self) -> None:
        """Recalculate all balances from chain"""
        self._balances.clear()
        for block in self._chain:
            self._update_balances_for_block(block)
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        with self._thread_safe_operation():
            return self._balances.get(address, 0.0)
    
    def get_chain(self) -> List[Block]:
        """Get copy of the blockchain"""
        with self._thread_safe_operation():
            return self._chain.copy()
    
    def get_pending_transactions(self) -> List[Transaction]:
        """Get copy of pending transactions"""
        with self._thread_safe_operation():
            return self._pending_transactions.copy()
    
    def resolve_conflicts(self) -> bool:
        """Resolve conflicts using longest valid chain"""
        try:
            with self._thread_safe_operation():
                longest_chain = self._chain
                max_length = len(self._chain)
                replaced = False
                
                for node in self._nodes:
                    chain = self.network.fetch_chain(node)
                    if chain and len(chain) > max_length:
                        validation_result = self.validator.validate_chain(chain)
                        if validation_result:
                            longest_chain = chain
                            max_length = len(chain)
                            replaced = True
                            self.logger.info(f"Found longer valid chain from {node}")
                
                if replaced:
                    self._chain = longest_chain
                    self._recalculate_balances()
                    self.persistence.save_chain(self._chain)
                    self.logger.info("Chain replaced with longer valid chain")
                
                return replaced
        except Exception as e:
            self.logger.error(f"Failed to resolve conflicts: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        with self._thread_safe_operation():
            total_transactions = sum(len(block.transactions) for block in self._chain)
            return {
                'blocks': len(self._chain),
                'pending_transactions': len(self._pending_transactions),
                'total_transactions': total_transactions,
                'nodes': len(self._nodes),
                'difficulty': self.config.difficulty,
                'mining_reward': self.config.mining_reward
            }




class BlockchainAPI:
    """Clean API layer for blockchain operations"""
    
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_app(self) -> Flask:
        """Create Flask application"""
        app = Flask(__name__)
        app.config['JSON_SORT_KEYS'] = False
        
        @app.errorhandler(Exception)
        def handle_error(error):
            self.logger.error(f"API error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
        
        @app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({'status': 'healthy', 'timestamp': time.time()})
        
        @app.route('/stats', methods=['GET'])
        def get_stats():
            """Get blockchain statistics"""
            return jsonify(self.blockchain.get_stats())
        
        @app.route('/chain', methods=['GET'])
        def get_chain():
            """Get the full blockchain"""
            chain = self.blockchain.get_chain()
            return jsonify({
                'chain': [block.to_dict() for block in chain],
                'length': len(chain)
            })
        
        @app.route('/transactions/pending', methods=['GET'])
        def get_pending_transactions():
            """Get pending transactions"""
            pending = self.blockchain.get_pending_transactions()
            return jsonify({
                'transactions': [tx.to_dict() for tx in pending],
                'count': len(pending)
            })
        
        @app.route('/balance/<address>', methods=['GET'])
        def get_balance(address: str):
            """Get balance for an address"""
            balance = self.blockchain.get_balance(address)
            return jsonify({'address': address, 'balance': balance})
        
        @app.route('/transaction', methods=['POST'])
        def create_transaction():
            """Create a new transaction"""
            try:
                data = request.get_json()
                required_fields = ['sender', 'recipient', 'amount']
                
                if not all(field in data for field in required_fields):
                    return jsonify({'error': 'Missing required fields'}), 400
                
                # Create transaction
                transaction = Transaction(data['sender'], data['recipient'], float(data['amount']))
                
                # Apply signature if provided
                if 'signature' in data:
                    signature = base64.b64decode(data['signature'])
                    transaction._data = TransactionData(
                        transaction.data.sender,
                        transaction.data.recipient,
                        transaction.data.amount,
                        transaction.data.timestamp,
                        signature
                    )
                
                # Add to blockchain
                if self.blockchain.add_transaction(transaction):
                    return jsonify({
                        'message': 'Transaction created successfully',
                        'transaction_hash': transaction.hash
                    }), 201
                else:
                    return jsonify({'error': 'Invalid transaction'}), 400
                    
            except Exception as e:
                self.logger.error(f"Transaction creation failed: {e}")
                return jsonify({'error': str(e)}), 400
        
        @app.route('/mine', methods=['POST'])
        def mine_block():
            """Mine a new block"""
            try:
                data = request.get_json() or {}
                miner_address = data.get('miner_address')
                
                if not miner_address:
                    return jsonify({'error': 'Miner address required'}), 400
                
                block = self.blockchain.mine_block(miner_address)
                if block:
                    return jsonify({
                        'message': 'Block mined successfully',
                        'block': block.to_dict()
                    })
                else:
                    return jsonify({'message': 'No transactions to mine'}), 400
                    
            except Exception as e:
                self.logger.error(f"Mining failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/nodes', methods=['POST'])
        def register_nodes():
            """Register new nodes"""
            try:
                data = request.get_json()
                nodes = data.get('nodes', [])
                
                if not nodes:
                    return jsonify({'error': 'No nodes provided'}), 400
                
                added_nodes = []
                for node in nodes:
                    if self.blockchain.add_node(node):
                        added_nodes.append(node)
                
                return jsonify({
                    'message': f'Added {len(added_nodes)} nodes',
                    'nodes': added_nodes
                })
                
            except Exception as e:
                self.logger.error(f"Node registration failed: {e}")
                return jsonify({'error': str(e)}), 400
        
        @app.route('/nodes/resolve', methods=['POST'])
        def resolve_conflicts():
            """Resolve conflicts using consensus"""
            try:
                replaced = self.blockchain.resolve_conflicts()
                if replaced:
                    return jsonify({'message': 'Chain was replaced with longer valid chain'})
                else:
                    return jsonify({'message': 'Chain is already the longest'})
                    
            except Exception as e:
                self.logger.error(f"Conflict resolution failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/wallet/new', methods=['POST'])
        def create_wallet():
            """Create a new wallet"""
            try:
                wallet = Wallet()
                return jsonify({
                    'address': wallet.address,
                    'message': 'Wallet created successfully'
                })
            except Exception as e:
                self.logger.error(f"Wallet creation failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        return app




class MiningPool:
    """Mining pool for coordinated mining efforts"""
    
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.miners: Dict[str, float] = {}  # address -> hash rate
        self.active_miners: Set[str] = set()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.RLock()
    
    def register_miner(self, address: str, hash_rate: float = 1.0) -> bool:
        """Register a miner in the pool"""
        try:
            with self._lock:
                self.miners[address] = hash_rate
                self.active_miners.add(address)
                self.logger.info(f"Registered miner: {address} with hash rate: {hash_rate}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to register miner {address}: {e}")
            return False
    
    def remove_miner(self, address: str) -> bool:
        """Remove a miner from the pool"""
        try:
            with self._lock:
                if address in self.miners:
                    del self.miners[address]
                    self.active_miners.discard(address)
                    self.logger.info(f"Removed miner: {address}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove miner {address}: {e}")
            return False
    
    def get_next_miner(self) -> Optional[str]:
        """Get next miner based on weighted selection"""
        if not self.active_miners:
            return None
        
        # Simple round-robin for now, could implement weighted selection
        return next(iter(self.active_miners))
    
    def distribute_rewards(self, block: Block, total_reward: float) -> Dict[str, float]:
        """Distribute mining rewards among pool members"""
        if not self.miners:
            return {}
        
        total_hash_rate = sum(self.miners.values())
        rewards = {}
        
        for address, hash_rate in self.miners.items():
            share = hash_rate / total_hash_rate
            reward = total_reward * share
            rewards[address] = reward
        
        return rewards




class BlockchainUtils:
    """Utility functions for blockchain operations"""
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """Validate if an address is properly formatted"""
        try:
            decoded = base64.b64decode(address)
            return len(decoded) == 64  # SECP256k1 public key length
        except Exception:
            return False
    
    @staticmethod
    def calculate_difficulty_adjustment(blocks: List[Block], target_time: int) -> int:
        """Calculate difficulty adjustment based on block times"""
        if len(blocks) < 2:
            return 4  # Default difficulty
        
        # Calculate average time for last 10 blocks
        recent_blocks = blocks[-10:] if len(blocks) >= 10 else blocks
        time_diffs = []
        
        for i in range(1, len(recent_blocks)):
            time_diff = recent_blocks[i].header.timestamp - recent_blocks[i-1].header.timestamp
            time_diffs.append(time_diff)
        
        if not time_diffs:
            return 4
        
        avg_time = sum(time_diffs) / len(time_diffs)
        current_difficulty = recent_blocks[-1].header.difficulty
        
        # Adjust difficulty based on target time
        if avg_time < target_time * 0.8:  # Too fast
            return min(current_difficulty + 1, 10)  # Max difficulty 10
        elif avg_time > target_time * 1.2:  # Too slow
            return max(current_difficulty - 1, 1)   # Min difficulty 1
        
        return current_difficulty
    
    @staticmethod
    def format_hash(hash_str: str) -> str:
        """Format hash for display"""
        if len(hash_str) > 16:
            return f"{hash_str[:8]}...{hash_str[-8:]}"
        return hash_str
    
    @staticmethod
    def estimate_network_hash_rate(blocks: List[Block]) -> float:
        """Estimate network hash rate based on recent blocks"""
        if len(blocks) < 2:
            return 0.0
        
        recent_blocks = blocks[-10:] if len(blocks) >= 10 else blocks
        total_work = 0
        total_time = 0
        
        for i in range(1, len(recent_blocks)):
            block = recent_blocks[i]
            prev_block = recent_blocks[i-1]
            
            # Estimate work done (simplified)
            work = 2 ** block.header.difficulty
            total_work += work
            
            time_diff = block.header.timestamp - prev_block.header.timestamp
            total_time += time_diff
        
        if total_time > 0:
            return total_work / total_time
        return 0.0




def create_blockchain_node(port: int = 5000, config: BlockchainConfig = None) -> Tuple[Blockchain, Flask]:
    """Factory function to create a blockchain node"""
    # Create blockchain instance
    blockchain = Blockchain(config or BlockchainConfig())
    
    # Create API
    api = BlockchainAPI(blockchain)
    app = api.create_app()
    
    return blockchain, app


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Refined Blockchain Node')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the node on')
    parser.add_argument('--difficulty', type=int, default=4, help='Mining difficulty')
    parser.add_argument('--reward', type=float, default=10.0, help='Mining reward')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration
    config = BlockchainConfig(
        difficulty=args.difficulty,
        mining_reward=args.reward
    )
    
    # Create blockchain node
    blockchain, app = create_blockchain_node(args.port, config)
    
    # Log startup information
    logger = logging.getLogger('main')
    logger.info(f"Starting blockchain node on port {args.port}")
    logger.info(f"Configuration: difficulty={config.difficulty}, reward={config.mining_reward}")
    
    # Run the Flask app
    try:
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Shutting down blockchain node...")
    except Exception as e:
        logger.error(f"Failed to start blockchain node: {e}")
        sys.exit(1)



def run_blockchain_demo():
    """Run a simple blockchain demonstration"""
    print("=== Blockchain Demo ===")
    
    # Create blockchain
    config = BlockchainConfig(difficulty=2, mining_reward=50.0)
    blockchain = Blockchain(config)
    
    # Create wallets
    alice = Wallet()
    bob = Wallet()
    charlie = Wallet()
    
    print(f"Alice address: {BlockchainUtils.format_hash(alice.address)}")
    print(f"Bob address: {BlockchainUtils.format_hash(bob.address)}")
    print(f"Charlie address: {BlockchainUtils.format_hash(charlie.address)}")
    
    # Mine initial block for Alice (this should give her mining reward)
    print("\n1. Mining initial block for Alice...")
    # Add a dummy transaction to trigger mining
    dummy_tx = Transaction("network", alice.address, 0.1)
    blockchain.add_transaction(dummy_tx)
    
    block1 = blockchain.mine_block(alice.address)
    if block1:
        print(f"Block #{block1.header.index} mined with {len(block1.transactions)} transactions")
        print(f"Alice balance after mining: {blockchain.get_balance(alice.address)}")
    else:
        print("No block mined")
    
    # Alice sends money to Bob
    print("\n2. Alice sends 20 coins to Bob...")
    tx1 = alice.create_transaction(bob.address, 20.0)
    if blockchain.add_transaction(tx1):
        print(f"Transaction added: {BlockchainUtils.format_hash(tx1.hash)}")

    # Mine block to confirm Alice->Bob so Bob has a confirmed balance
    print("\n3. Mining block to confirm Alice->Bob transaction...")
    block2 = blockchain.mine_block(alice.address)
    if block2:
        print(f"Block #{block2.header.index} mined")
        print(f"Alice balance: {blockchain.get_balance(alice.address)}")
        print(f"Bob balance: {blockchain.get_balance(bob.address)}")

    # Bob sends money to Charlie (this should fail - no signature)
    print("\n4. Bob tries to send 5 coins to Charlie (unsigned transaction)...")
    tx2 = Transaction(bob.address, charlie.address, 5.0)  # Not signed
    if blockchain.add_transaction(tx2):
        print("Transaction added (this shouldn't happen!)")
    else:
        print("Transaction correctly rejected (not signed)")

    # Bob properly sends money to Charlie
    print("\n5. Bob properly sends 5 coins to Charlie...")
    tx3 = bob.create_transaction(charlie.address, 5.0)
    if blockchain.add_transaction(tx3):
        print(f"Transaction added: {BlockchainUtils.format_hash(tx3.hash)}")
    
    # Mine another block
    print("\n6. Mining block with Bob->Charlie transaction...")
    block3 = blockchain.mine_block(bob.address)
    if block3:
        print(f"Block #{block3.header.index} mined with {len(block3.transactions)} transactions")
        print(f"Final balances:")
        print(f"  Alice: {blockchain.get_balance(alice.address)}")
        print(f"  Bob: {blockchain.get_balance(bob.address)}")
        print(f"  Charlie: {blockchain.get_balance(charlie.address)}")

    # Show blockchain stats
    print("\n7. Blockchain Statistics:")
    stats = blockchain.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Verify chain integrity
    print("\n8. Chain Validation:")
    validation_result = blockchain.validator.validate_chain(blockchain.get_chain())
    if validation_result:
        print("✓ Blockchain is valid")
    else:
        print("✗ Blockchain validation failed:")
        for error in validation_result.errors:
            print(f"  - {error}")
    
    print("\n=== Demo Complete ===")


def run_another_blockchain_demo():
    """Run a corrected blockchain demonstration"""
    print("=== Corrected Blockchain Demo ===")
    
    # Create blockchain
    config = BlockchainConfig(difficulty=2, mining_reward=50.0)
    blockchain = Blockchain(config)
    
    # Create wallets
    alice = Wallet()
    bob = Wallet()
    charlie = Wallet()
    
    print(f"Alice address: {alice.address[:16]}...")
    print(f"Bob address: {bob.address[:16]}...")
    print(f"Charlie address: {charlie.address[:16]}...")
    
    # Step 1: Mine initial block to give Alice some coins
    print("\n1. Mining initial block for Alice...")
    block1 = blockchain.mine_block(alice.address)
    if block1:
        print(f"✓ Block #{block1.header.index} mined")
        print(f"Alice balance: {blockchain.get_balance(alice.address)}")
    
    # Step 2: Alice sends money to Bob
    print("\n2. Alice sends 20 coins to Bob...")
    tx1 = alice.create_transaction(bob.address, 20.0)
    blockchain.add_transaction(tx1)
    print(f"✓ Transaction added to pending pool")
    
    # Step 3: Mine block to confirm Alice->Bob transaction
    print("\n3. Mining block to confirm Alice->Bob transaction...")
    block2 = blockchain.mine_block(bob.address)  # Bob mines and gets reward
    if block2:
        print(f"✓ Block #{block2.header.index} mined by Bob")
        print(f"Alice balance: {blockchain.get_balance(alice.address)}")
        print(f"Bob balance: {blockchain.get_balance(bob.address)}")
    
    # Step 4: Now Bob can send to Charlie (he has funds)
    print("\n4. Bob sends 5 coins to Charlie...")
    tx2 = bob.create_transaction(charlie.address, 5.0)
    if blockchain.add_transaction(tx2):
        print(f"✓ Transaction added to pending pool")
    
    # Step 5: Mine final block
    print("\n5. Mining final block...")
    block3 = blockchain.mine_block(charlie.address)  # Charlie mines and gets reward
    if block3:
        print(f"✓ Block #{block3.header.index} mined by Charlie")
    
    # Final balances
    print("\n6. Final Balances:")
    print(f"Alice: {blockchain.get_balance(alice.address)}")
    print(f"Bob: {blockchain.get_balance(bob.address)}")  
    print(f"Charlie: {blockchain.get_balance(charlie.address)}")
    
    # Expected results:
    # Alice: 50 (mining) - 20 (sent) = 30
    # Bob: 20 (received) + 50 (mining) - 5 (sent) = 65  
    # Charlie: 5 (received) + 50 (mining) = 55
    
    print("\n7. Chain Validation:")
    validation_result = blockchain.validator.validate_chain(blockchain.get_chain())
    print(f"Chain valid: {validation_result.is_valid}")


if __name__ == "__main__":
    # Check if running as demo
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_blockchain_demo()
        # run_another_blockchain_demo()
    else:
        main()


