import os
import json


class LogEntry:
    """A single entry in the replicated log."""
    __slots__ = ("term", "command")

    def __init__(self, term, command):
        self.term = term
        self.command = command  # tuple: ("SET", key, value)

    def to_dict(self):
        return {"term": self.term, "command": list(self.command)}

    @staticmethod
    def from_dict(d):
        return LogEntry(d["term"], tuple(d["command"]))

    def __repr__(self):
        return f"LogEntry(term={self.term}, cmd={self.command})"


class RaftDatabase:
    """
    Per-server persistent storage and state machine.

    In a real Raft node three things MUST be written to stable storage
    before responding to any RPC: current_term, voted_for, and the log.
    The commit_index and last_applied are volatile and are derived from
    the log on restart.  Here we keep them in memory and optionally
    persist the log to a JSON file.
    """

    def __init__(self, server_id, persist=False):
        self.server_id = server_id
        self.persist = persist
        self._log_file = f"raft_log_{server_id}.json"

        # Replicated log -- list of LogEntry
        self.log = []

        # Key-value state machine (applied entries)
        self.kv_store = {}

        # Highest index applied to state machine
        self.last_applied = -1

        if persist:
            self._load()


    # Persistence

    def _load(self):
        if os.path.exists(self._log_file):
            with open(self._log_file) as f:
                data = json.load(f)
            self.log = [LogEntry.from_dict(e) for e in data]

    def _save_log(self):
        if self.persist:
            with open(self._log_file, "w") as f:
                json.dump([e.to_dict() for e in self.log], f)


    # Log operations

    def append_entries(self, prev_index, entries):
        """
        Merge new entries into the log starting after prev_index.

        Conflicting entries (same index, different term) and everything
        after them are discarded before the new entries are written.
        """
        insert_at = prev_index + 1
        for i, entry in enumerate(entries):
            idx = insert_at + i
            if idx < len(self.log):
                if self.log[idx].term != entry.term:
                    # Conflict: truncate and replace from here
                    self.log = self.log[:idx]
                    self.log.append(entry)
                # else: identical entry already present, skip
            else:
                self.log.append(entry)
        self._save_log()

    def last_log_index(self):
        return len(self.log) - 1

    def last_log_term(self):
        return self.log[-1].term if self.log else 0

    def term_at(self, index):
        if index < 0 or index >= len(self.log):
            return 0
        return self.log[index].term


    # State machine

    def apply_up_to(self, commit_index):
        """
        Apply all log entries from (last_applied + 1) to commit_index
        against the key-value state machine.  Returns a list of
        (key, value) pairs that were applied.
        """
        applied = []
        while self.last_applied < commit_index and self.last_applied < len(self.log) - 1:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            cmd = entry.command
            if cmd[0] == "SET":
                self.kv_store[cmd[1]] = cmd[2]
                applied.append((cmd[1], cmd[2]))
        return applied

    def get_state(self):
        return dict(self.kv_store)
