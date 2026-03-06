import random
import threading
import time
import logging

from raft_database import RaftDatabase, LogEntry

logger = logging.getLogger(__name__)

# Raft timing parameters
# (a recommendation is 150-300 ms election timeout
# and a heartbeat interval well below that).
ELECTION_TIMEOUT_MIN = 0.15   # 150 ms
ELECTION_TIMEOUT_MAX = 0.30   # 300 ms
HEARTBEAT_INTERVAL   = 0.05   # 50 ms
NETWORK_DELAY_MAX    = 0.008  # 8 ms simulated one-way latency


class RaftServer:
    """
    A single node in a Raft cluster.

    Each server runs its own background thread and communicates with peers
    via direct method calls (simulating RPCs without real networking).

    Roles
    -----
    FOLLOWER  -- passive; resets election timer on each heartbeat.
    CANDIDATE -- requests votes from peers; becomes LEADER on quorum.
    LEADER    -- sends periodic AppendEntries / heartbeats; accepts client
                 commands; advances commit index once a majority has
                 replicated an entry.

    Persistent state (current_term, voted_for, log) would be written to
    stable storage before responding to any RPC in a real deployment.
    """

    def __init__(self, server_id, cluster_size):
        self.id           = server_id
        self.cluster_size = cluster_size
        self.peers        = []   # set after all servers are created

        # --- Persistent state (survive crashes in a real system) ---
        self.current_term = 0
        self.voted_for    = None   # candidate id this server voted for in current term
        self.db           = RaftDatabase(server_id)

        # --- Volatile state ---
        self.state        = "FOLLOWER"
        self.commit_index = -1     # highest log entry known to be committed
        self.leader_id    = None   # hint so followers can redirect clients

        # --- Volatile leader state (re-initialised on each election win) ---
        self.next_index   = {}     # peer_id -> next log index to send
        self.match_index  = {}     # peer_id -> highest index known replicated on peer

        # --- Synchronisation ---
        self._lock              = threading.Lock()
        self._heartbeat_event   = threading.Event()   # set whenever a valid leader message arrives
        self._stop              = threading.Event()
        self._thread            = threading.Thread(
            target=self._run, daemon=True, name=f"raft-{server_id}"
        )


    # Lifecycle

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._heartbeat_event.set()   # unblock any blocked wait()


    # Main loop

    def _run(self):
        while not self._stop.is_set():
            with self._lock:
                state = self.state
            if state == "FOLLOWER":
                self._do_follower()
            elif state == "CANDIDATE":
                self._do_candidate()
            elif state == "LEADER":
                self._do_leader()


    # FOLLOWER behaviour

    def _do_follower(self):
        timeout     = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        got_message = self._heartbeat_event.wait(timeout=timeout)
        self._heartbeat_event.clear()

        if self._stop.is_set():
            return

        if not got_message:
            # Election timeout fired without hearing from a leader.
            with self._lock:
                if self.state == "FOLLOWER":
                    logger.info(
                        f"[S{self.id}] election timeout -- starting election "
                        f"for term {self.current_term + 1}"
                    )
                    self.state = "CANDIDATE"


    # CANDIDATE behaviour

    def _do_candidate(self):
        with self._lock:
            self.current_term += 1
            self.voted_for     = self.id   # vote for self
            term               = self.current_term
            last_idx           = self.db.last_log_index()
            last_term          = self.db.last_log_term()
            peers              = list(self.peers)
            logger.info(f"[S{self.id}] CANDIDATE -- term {term}")

        # Gather votes from peers concurrently.
        vote_count     = [1]   # already voted for self; mutable for threads
        step_down_term = [None]
        vote_lock      = threading.Lock()

        def ask_vote(peer):
            time.sleep(random.uniform(0, NETWORK_DELAY_MAX))
            granted, peer_term = peer.rpc_request_vote(term, self.id, last_idx, last_term)
            with vote_lock:
                if peer_term > term:
                    step_down_term[0] = peer_term
                elif granted:
                    vote_count[0] += 1

        threads = [threading.Thread(target=ask_vote, args=(p,), daemon=True) for p in peers]
        for t in threads:
            t.start()

        # Wait up to one election timeout for votes to arrive.
        deadline = time.monotonic() + random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        for t in threads:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                t.join(timeout=remaining)

        with self._lock:
            # A concurrent RPC may have already moved us to FOLLOWER.
            if self.state != "CANDIDATE" or self.current_term != term:
                return

            if step_down_term[0]:
                self.current_term = step_down_term[0]
                self.voted_for    = None
                self.state        = "FOLLOWER"
                return

            quorum = self.cluster_size // 2 + 1
            if vote_count[0] >= quorum:
                logger.info(
                    f"[S{self.id}] WON election for term {term} "
                    f"({vote_count[0]}/{self.cluster_size} votes)"
                )
                self.state     = "LEADER"
                self.leader_id = self.id
                # Initialise per-peer tracking indices.
                for p in self.peers:
                    self.next_index[p.id]  = len(self.db.log)
                    self.match_index[p.id] = -1
            else:
                logger.info(
                    f"[S{self.id}] lost election for term {term} "
                    f"({vote_count[0]}/{self.cluster_size} votes)"
                )
                self.state = "FOLLOWER"


    # LEADER behaviour

    def _do_leader(self):
        with self._lock:
            term  = self.current_term
            peers = list(self.peers)

        # Send AppendEntries (or heartbeat if no new entries) to every peer.
        threads = [
            threading.Thread(target=self._replicate_to, args=(p, term), daemon=True)
            for p in peers
        ]
        for t in threads:
            t.start()

        time.sleep(HEARTBEAT_INTERVAL)

        with self._lock:
            if self.current_term != term:
                self.state = "FOLLOWER"

    def _replicate_to(self, peer, term):
        """Send one round of AppendEntries to a single peer."""
        with self._lock:
            if self.state != "LEADER" or self.current_term != term:
                return
            ni         = self.next_index.get(peer.id, len(self.db.log))
            prev_idx   = ni - 1
            prev_term  = self.db.term_at(prev_idx)
            entries    = list(self.db.log[ni:])
            lc         = self.commit_index

        time.sleep(random.uniform(0, NETWORK_DELAY_MAX))
        success, peer_term = peer.rpc_append_entries(
            term, self.id, prev_idx, prev_term, entries, lc
        )

        with self._lock:
            if peer_term > self.current_term:
                self.current_term = peer_term
                self.voted_for    = None
                self.state        = "FOLLOWER"
                return

            if self.state != "LEADER" or self.current_term != term:
                return

            if success:
                new_match              = prev_idx + len(entries)
                old_match              = self.match_index.get(peer.id, -1)
                self.match_index[peer.id] = max(old_match, new_match)
                self.next_index[peer.id]  = self.match_index[peer.id] + 1
                self._try_advance_commit(term)
            else:
                # Log inconsistency: back up and retry next heartbeat.
                self.next_index[peer.id] = max(0, self.next_index.get(peer.id, 1) - 1)

    def _try_advance_commit(self, term):
        """
        Advance commit_index to the highest N where a quorum has
        replicated index N *and* log[N].term == current_term.
        Caller must hold self._lock.
        """
        quorum = self.cluster_size // 2 + 1
        for n in range(len(self.db.log) - 1, self.commit_index, -1):
            # Safety: only commit entries from the current term
            # (older entries are committed implicitly when a current-term
            # entry is committed).
            if self.db.log[n].term != term:
                continue
            count = 1   # leader itself
            for p in self.peers:
                if self.match_index.get(p.id, -1) >= n:
                    count += 1
            if count >= quorum:
                self.commit_index = n
                applied = self.db.apply_up_to(self.commit_index)
                for k, v in applied:
                    logger.info(f"[S{self.id}] COMMITTED  SET {k}={v}")
                break


    # RPC handlers
    # (In a real cluster these would be called over the network.
    #  Here they are direct method calls with simulated latency.)

    def rpc_request_vote(self, term, candidate_id, last_log_index, last_log_term):
        """
        RequestVote RPC.
        Returns (vote_granted: bool, current_term: int).
        """
        with self._lock:
            # Stale term: reject.
            if term < self.current_term:
                return False, self.current_term

            # Higher term: step down and update.
            if term > self.current_term:
                self.current_term = term
                self.voted_for    = None
                self.state        = "FOLLOWER"

            # Check candidate log is at least as up-to-date as ours.
            my_last_term = self.db.last_log_term()
            my_last_idx  = self.db.last_log_index()
            log_ok = (
                last_log_term > my_last_term
                or (last_log_term == my_last_term and last_log_index >= my_last_idx)
            )

            already_voted = self.voted_for not in (None, candidate_id)
            if already_voted or not log_ok:
                return False, self.current_term

            self.voted_for = candidate_id
            self._heartbeat_event.set()   # reset election timer
            logger.debug(f"[S{self.id}] voted for S{candidate_id} in term {term}")
            return True, self.current_term

    def rpc_append_entries(
        self, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit
    ):
        """
        AppendEntries RPC (also serves as heartbeat when entries is empty).
        Returns (success: bool, current_term: int).
        """
        with self._lock:
            # Stale term: reject.
            if term < self.current_term:
                return False, self.current_term

            # Valid message from current or newer leader.
            self._heartbeat_event.set()

            if term > self.current_term:
                self.current_term = term
                self.voted_for    = None

            self.state     = "FOLLOWER"
            self.leader_id = leader_id

            # Log consistency check.
            if prev_log_index >= 0:
                if prev_log_index >= len(self.db.log):
                    # We are missing entries the leader expects.
                    return False, self.current_term
                if self.db.term_at(prev_log_index) != prev_log_term:
                    # Conflicting entry at prev_log_index: ask leader to back up.
                    return False, self.current_term

            # Merge new entries (handles conflicts and duplicates).
            if entries:
                self.db.append_entries(prev_log_index, entries)

            # Advance commit index and apply newly committed entries.
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.db.log) - 1)
                applied = self.db.apply_up_to(self.commit_index)
                for k, v in applied:
                    logger.debug(f"[S{self.id}] applied  SET {k}={v}")

            return True, self.current_term


    # Client interface

    def client_request(self, command):
        """
        Submit a command to be replicated across the cluster.
        Only accepted if this server is the current leader.
        Returns (accepted: bool, leader_hint: int | None).
        """
        with self._lock:
            if self.state != "LEADER":
                return False, self.leader_id
            entry = LogEntry(self.current_term, command)
            self.db.log.append(entry)
            logger.info(f"[S{self.id}] client command appended: {entry}")
            return True, self.id


    # Introspection

    def get_state(self):
        with self._lock:
            return {
                "id":      self.id,
                "role":    self.state,
                "term":    self.current_term,
                "log_len": len(self.db.log),
                "commit":  self.commit_index,
                "applied": self.db.last_applied,
                "kv":      dict(self.db.kv_store),
                "leader":  self.leader_id,
            }
