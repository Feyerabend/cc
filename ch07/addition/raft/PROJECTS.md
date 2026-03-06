
## Projects

### 1. Simulate a Raft Leader Election (No Networking)

*Implement a basic leader election mechanism in a single process (no network).*

- *What You'll Do*:  
  - Model 3-5 nodes (threads or objects) that can be in *follower*, *candidate*, or *leader* state.  
  - Simulate timeouts--if a follower doesn't hear from a leader, it becomes a candidate and starts an election.  
  - Implement simple voting logic (majority wins).  

- *Why It's Useful*: Helps you understand the core of Raft without networking complexity.  


### 2. Build a Simple Key-Value Store with Raft (Single-Node Leader)

*Store key-value pairs where only the leader accepts writes.*

- *What You'll Do*:  
  - Use an in-memory dictionary (`dict` in Python, `HashMap` in Rust/Java) as the "database."  
  - Implement a leader that processes `SET`/`GET` commands and followers that replicate logs (but don't accept writes).  
  - No persistence--just focus on log replication.  
- *Why It's Useful*: Introduces you to log replication without full distributed systems complexity.  


### 3. Visualize Raft States with a CLI or GUI

*Create a tool that shows how nodes change state (leader/follower/candidate).*

- *What You'll Do*:  
  - Use Python (`tkinter`), JavaScript (`D3.js`), or a terminal UI library (`curses`, `tui-rs`) to display node states.  
  - Simulate network partitions (e.g., pausing messages to a node) and show elections happening.  
- *Why It's Useful*: Helps debug and understand Raft dynamics visually.  


### 4. Networked Raft with gRPC/HTTP

*Extend your leader election or KV store to work over the network.*

- *What You'll Do*:  
  - Use gRPC (or raw TCP/HTTP) to send `AppendEntries` and `RequestVote` RPCs between nodes.  
  - Handle basic network issues (dropped messages, delays).  
  - Persist logs to disk (simple file storage).  
- *Why It's Useful*: Moves you toward a real distributed system.  


### 5. Fault-Tolerant Counter Service

*Build a distributed counter that stays consistent even if nodes fail.*

- *What You'll Do*:  
  - Clients can increment/decrement a counter.  
  - The leader replicates changes, and followers apply them.  
  - Test by killing the leader and verifying a new one takes over.  
- *Why It's Useful*: Teaches you about fault tolerance in a concrete way.  


### 6. Snapshots and Log Compaction

*Prevent logs from growing infinitely by adding snapshotting.*

- *What You'll Do*:  
  - Periodically save the database state (e.g., `{"counter": 5}`) to disk.  
  - Truncate the log up to the snapshot point.  
  - Handle follower snapshots (send snapshots if their logs are too far behind).  
- *Why It's Useful*: Critical for real-world systems with long uptimes.  


### 7. Full Distributed Database with Raft

*Build a mini-etcd or Redis-like system.*

- *What You'll Do*:  
  - Support transactions (multi-key updates).  
  - Add persistence (write-ahead logs, snapshots).  
  - Optimize throughput (batching, pipelining).  
- *Why It's Useful*: Prepares you for real distributed databases.  


### 8. Dynamic Cluster Membership Changes

*Allow adding/removing nodes at runtime.*

- *What You'll Do*:  
  - Implement Raft's `AddServer`/`RemoveServer` mechanics.  
  - Handle joint consensus (if following the Raft paper).  
- *Why It's Useful*: Needed for scaling real clusters.  


### 9. Benchmark Raft vs. Paxos (or Zab)

*Compare performance under different failure scenarios.*

- *What You'll Do*:  
  - Simulate network partitions, crashes, and high load.  
  - Measure latency, recovery time, and throughput.  
- *Why It's Useful*: Deepens understanding of trade-offs in consensus algorithms.  
