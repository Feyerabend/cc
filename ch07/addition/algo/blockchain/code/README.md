
## Blockchain

Blockchain is a decentralised, secure, and transparent digital ledger technology that has reshaped
how data is stored, shared, and verified across networks. It enables trust without intermediaries
by creating tamper-resistant records of transactions or data, distributed across multiple computers.
Since its inception, blockchain has evolved from a niche concept underpinning cryptocurrencies to
a transformative tool with applications spanning finance, supply chains, healthcare, and beyond.


### History in Brief

The concept of blockchain emerged in 2008 with the publication of a whitepaper by an anonymous individual
or group under the pseudonym Satoshi Nakamoto, titled *Bitcoin: A Peer-to-Peer Electronic Cash System*.
This introduced Bitcoin, the first cryptocurrency, and its underlying blockchain as a solution to the
problem of double-spending in digital currencies without relying on centralised institutions like banks.
The first Bitcoin block, known as the genesis block, was mined in January 2009, marking the birth of
blockchain in practice. While Bitcoin initially gained traction in niche tech and libertarian circles,
the broader potential of blockchain became evident by the mid-2010s. Ethereum, launched in 2015 by
Vitalik Buterin, expanded the technology's scope by introducing smart contracts--self-executing code
stored on the blockchain--unlocking applications beyond currency. Since then, blockchain has seen waves
of innovation, from enterprise adoption by companies like IBM and JPMorgan to decentralised finance
(DeFi) and non-fungible tokens (NFTs), though it has also faced scrutiny over scalability, energy
consumption, and regulatory challenges.


### The Technology

At its core, blockchain is a distributed database that records transactions in a chronological, immutable
sequence of blocks. Each block contains a list of transactions or data, a timestamp, and a cryptographic
hash of the previous block, forming a chain that is resistant to alteration. This structure ensures that
once data is added, it cannot be changed without altering all subsequent blocks, which requires consensus
from the network--a computationally expensive and practically infeasible task in large, secure blockchains.

The technology relies on several key components. First, *decentralisation* distinguishes blockchain from
traditional databases. Instead of a central authority, data is stored across a network of nodes (computers)
that maintain identical copies of the ledger. These nodes communicate through a peer-to-peer network,
ensuring no single point of failure. Second, *consensus mechanisms* govern how nodes agree on the validity
of transactions. Bitcoin uses Proof of Work (PoW), where miners solve complex mathematical puzzles to
validate transactions and earn rewards, a process that, while secure, is energy-intensive. Ethereum and
newer blockchains often use Proof of Stake (PoS), where validators stake cryptocurrency to participate,
reducing energy use. Other mechanisms, like Delegated Proof of Stake or Practical Byzantine Fault Tolerance,
cater to specific needs like speed or scalability.

Cryptography underpins blockchain's security. Transactions are signed with private-public key pairs,
ensuring only authorised parties can initiate them. Hashes--fixed-length strings generated from data--link
blocks and detect tampering. If even a single character in a block changes, its hash becomes invalid, breaking
the chain's integrity. Additionally, *smart contracts*, pioneered by Ethereum, allow programmable logic on
the blockchain, automating agreements like payments or asset transfers when predefined conditions are met.

Blockchains can be public (permissionless, like Bitcoin, where anyone can join), private (permissioned,
restricted to authorised participants), or hybrid. Public blockchains prioritise transparency and censorship
resistance but face scalability issues, processing only a few transactions per second compared to centralised
systems like Visa. Innovations like sharding, layer-2 solutions (e.g., Lightning Network for Bitcoin), and
alternative blockchains (e.g., Solana, Polkadot) aim to address these limitations by improving throughput
and reducing costs.


### Applications

Blockchain's applications extend far beyond cryptocurrencies. In *finance*, decentralised finance (DeFi) platforms
like Uniswap or Aave use blockchain to offer lending, borrowing, and trading without banks, relying on smart
contracts to automate processes. Stablecoins, cryptocurrencies pegged to assets like the dollar, facilitate fast,
low-cost cross-border payments. In *supply chain management*, companies like Walmart use blockchain to track goods
from source to shelf, ensuring transparency and reducing fraud--IBM's Food Trust network, for instance, traces food
products to verify authenticity and safety. *Healthcare* leverages blockchain to secure patient records, enabling
interoperable, tamper-proof data sharing while preserving privacy. *Digital identity* solutions use blockchain to
create verifiable, self-sovereign identities, reducing reliance on centralised databases vulnerable to breaches.
In the creative sector, *NFTs* enable artists to tokenise digital assets, proving ownership and authenticity, though
their speculative nature has sparked debate. Blockchain also supports *voting systems*, offering transparent, auditable
elections, and *energy markets*, where peer-to-peer trading of renewable energy is piloted in projects like Australia's
Power Ledger.

The technology's potential lies in its ability to eliminate intermediaries, reduce costs, and enhance trust in
systems where parties don't inherently trust each other. However, challenges like regulatory uncertainty, high
energy consumption in some networks, and user adoption hurdles remain. As blockchain matures, its integration
with AI, IoT, and other technologies promises to unlock further innovation, making it a cornerstone of a
decentralised digital future.


### The Implementations

Three Python files of increasing sophistication illustrate how these ideas translate into working code.


#### `block.py` -- the skeleton

About 50 lines. No dependencies beyond the standard library. The whole point is to make the chain
structure legible:

```python
class Block:
    def __init__(self, index, previous_hash, timestamp, data):
        ...
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}"
        return hashlib.sha256(block_string.encode()).hexdigest()
```

Each block encodes its own position (`index`), the hash of the block before it (`previous_hash`),
the time it was created, and whatever payload is being stored (`data`). The SHA-256 digest of those
four fields becomes the block's identity. If any field changes--even by one character--the digest
changes entirely, and the `previous_hash` stored in the next block no longer matches, breaking the
chain. `is_chain_valid` exploits this: it re-computes every block's hash and confirms that adjacent
`previous_hash` fields agree.

There is no proof-of-work and no cryptographic signing here. The chain is a data structure, not
yet a security mechanism.


#### `coins.py` -- a working coin system

About 770 lines. Introduces four ideas absent from the skeleton.

*Digital signatures.* Wallets are ECDSA keypairs on the secp256k1 curve--the same elliptic curve
specified in Bitcoin's original design. The wallet's address is simply its base64-encoded public key.
When Alice creates a transaction, she signs the concatenation of sender, recipient, amount, and
timestamp with her private key. Anyone holding her public key (i.e., her address) can verify
that signature without learning the private key. A transaction whose signature cannot be verified
against its stated sender address is rejected before it reaches the pending pool.

*Proof of Work.* Mining increments a `nonce` field and re-hashes the block until the digest begins
with a required number of leading zeros:

```python
target = "0" * difficulty
while block.hash[:difficulty] != target:
    block.nonce += 1
    block.hash = block.calculate_hash()
```

With `difficulty=4`, the target is `0000...`. The probability that any single hash meets this is
roughly 1/65,536, so the miner must try tens of thousands of candidates on average. Raising the
difficulty to 6 pushes that to ~16 million attempts. This expenditure of work is what makes
retroactively rewriting a block expensive--every subsequent block would need to be re-mined too.

*Design patterns.* Three classic OO patterns appear explicitly. The *Strategy* pattern wraps the
mining algorithm in an abstract `MiningStrategy` interface with `ProofOfWorkStrategy` as the
concrete implementation; swapping in Proof of Stake or any other mechanism requires only a new
class that satisfies the same interface. The *Factory* pattern centralises block and transaction
construction in `BlockFactory` and `TransactionFactory`, keeping instantiation logic out of the
core chain class. The *Observer* pattern lets `Blockchain` broadcast events to peer nodes: every
registered node is wrapped in a `NodeObserver` that HTTP-POSTs new transactions and blocks to
that peer automatically, without the chain needing to know anything about HTTP.

*Longest-chain consensus.* `resolve_conflicts` iterates all known peers, fetches their chains,
and replaces the local chain if a longer valid one is found. The rule is intentionally simple:
the chain representing the most accumulated proof-of-work wins. An attacker who wanted to rewrite
history would need to outpace the rest of the network indefinitely--an astronomically expensive
proposition on a large network.


#### `blockchain/blockchain.py` -- the refined version

About 1,240 lines. Builds on the same ideas with several structural improvements.

*Merkle root.* Rather than hashing all transaction data as a flat string, transaction hashes are
arranged in a binary tree and reduced to a single 32-byte root stored in the block header:

```
       root
      /    \
   h(AB)  h(CD)
   /  \   /  \
  hA  hB hC  hD
```

This means a single transaction can be verified against a block by supplying only the sibling
hashes along the path from leaf to root (a Merkle proof), rather than all transactions. The
root is recomputed on any tampering, so the block hash detects corruption without exposing
every transaction.

*Separated header.* `BlockHeader` is a `@dataclass` containing only the metadata (index,
hashes, timestamp, nonce, difficulty). `Block` holds the header plus the transaction list.
Proof-of-Work grinds against the header hash alone, which is a closer model to how Bitcoin
actually works (the block header is 80 bytes; the transaction list can be megabytes).

*Validation as a first-class object.* `BlockchainValidator` is its own class, and its methods
return a `ValidationResult(is_valid, errors)` rather than a bare boolean. Callers receive the
full list of violations--useful for debugging and for deciding whether to accept a block from
a peer.

*Thread safety.* The `Blockchain` class uses a `threading.RLock`. Crucially, `mine_block`
acquires the lock only to set up the candidate block and again to commit the result; the
actual proof-of-work loop runs outside the lock, so `get_balance`, `add_transaction`, and
other fast operations remain available to other threads while mining is in progress.

*JSON persistence.* The `PersistenceManager` serialises the chain as JSON using each block's
`to_dict` method. This is both human-readable and safe--unlike `pickle`, it cannot execute
arbitrary code when loaded.


### Design Choices Worth Noting

*Why secp256k1?* It is the elliptic curve from Bitcoin's original design. The `ecdsa` library
used here is pure Python, which keeps the dependency simple at the cost of speed.

*Why SHA-256?* Collision resistance--no two distinct inputs are known to produce the same digest.
Even a one-character change in a block's data produces a completely different hash, which then
invalidates every subsequent block's `previous_hash`, making silent tampering detectable immediately.

*What does* `difficulty=4` *actually mean?* A valid hash must start with `0000`. The probability
of any random SHA-256 hash satisfying this is 1/16^4, roughly 1 in 65,000. In practice the
miner loops for tens of thousands of iterations per block at this difficulty. Each additional
level of difficulty multiplies the expected work by 16.

*The genesis block is special.* Its `previous_hash` is the string `"0"` by convention, and
validation skips its proof-of-work check. Every other block's validity traces back to it
through the unbroken chain of hashes--the genesis block is the single trusted anchor.

*Why does the longest chain win?* If two miners solve a block at nearly the same time, the
network temporarily holds two valid forks. Nodes always adopt whichever fork grows longer
first, because length represents accumulated computational effort. A fraudulent fork can only
persist if its author can outpace all honest miners indefinitely--which becomes statistically
impossible as the network grows.


### Running the Code

#### `block.py` (no external dependencies)

```bash
python3 block.py
```

Expected output:

```
Index: 0
Timestamp: 1671234567.123456
Data: Genesis Block
Previous Hash: 0
Hash: a1b2c3d4...

Index: 1
...
Blockchain valid: True
```

Hashes and timestamps differ on every run since they encode the current time.


#### `coins.py` (Flask API node)

Install dependencies first:

```bash
pip install flask ecdsa requests waitress
```

Run a single development node:

```bash
python3 coins.py                        # default port 5000, difficulty 4
python3 coins.py --port 5001            # custom port
python3 coins.py --difficulty 2         # faster mining for testing
python3 coins.py --reward 25.0          # custom mining reward
python3 coins.py --production --port 8080   # production mode (requires waitress)
```

On startup in development mode the node creates test wallets for Alice, Bob, and a miner,
funds them via reward transactions, runs a pair of signed transfers, mines a block, and
logs the resulting balances--so the API is exercisable immediately.

Interact with the running node:

```bash
# View the blockchain
curl http://localhost:5000/chain

# Create a transaction (sender must sign externally)
curl -X POST http://localhost:5000/transaction/new \
  -H "Content-Type: application/json" \
  -d '{"sender":"<pub_key>","recipient":"<pub_key>","amount":10.0,"signature":"<base64_sig>"}'

# Mine pending transactions into a new block
curl -X POST http://localhost:5000/mine \
  -H "Content-Type: application/json" \
  -d '{"miner_address": "<pub_key>"}'

# Check a wallet balance
curl http://localhost:5000/balance/<address>

# Register peer nodes (for multi-node network)
curl -X POST http://localhost:5000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"nodes": ["http://localhost:5001", "http://localhost:5002"]}'

# Trigger consensus (adopt longest valid chain from peers)
curl http://localhost:5000/nodes/resolve
```

To simulate a network, start three nodes in separate terminals on ports 5000, 5001, and
5002, then register each node's peers via the `/nodes/register` endpoint.


#### `blockchain/blockchain.py` (refined node)

Same dependencies as `coins.py`. Supports a `demo` subcommand that runs a self-contained
demonstration without starting a server:

```bash
pip install flask ecdsa requests

python3 blockchain/blockchain.py demo         # walkthrough demo
python3 blockchain/blockchain.py              # start API server on port 5000
python3 blockchain/blockchain.py --port 5001 --difficulty 2 --debug
```

The Makefile in `blockchain/` wraps common operations:

```bash
cd blockchain
make run-node          # start node on port 5000
make run-multi-node    # start three nodes on 5000, 5001, 5002
make stop-nodes        # kill all running nodes
make test              # run validation
make clean             # remove logs and data files
```
