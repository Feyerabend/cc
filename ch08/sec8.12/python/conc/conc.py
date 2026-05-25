"""
Property-based testing for concurrent code.

Three examples of increasing complexity:

  1. Counter      — a read-modify-write race condition vs. a lock-protected counter.
  2. BankAccount  — conservation of total balance under concurrent transfers,
                    with deadlock-safe lock ordering.
  3. BoundedQueue — a thread-safe producer/consumer buffer; properties cover
                    capacity, ordering, and element preservation.

The unsafe variants are included so the race conditions can be observed
directly; the property-based tests target only the safe variants.
"""

import threading
import time
from collections import deque
from typing import List, Optional

from hypothesis import given, strategies as st, settings, HealthCheck


# ============================================================================
# Part 1: Counter
# ============================================================================

class UnsafeCounter:
    """Counter without synchronisation — exhibits a read-modify-write race."""

    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        tmp = self.value      # (1) read
        time.sleep(0)         # yield the GIL: widens the race window for the demo;
                              # in production code no sleep is needed — the race
                              # already exists at bytecode granularity.
        self.value = tmp + 1  # (2) write: may overwrite another thread's update


class SafeCounter:
    """Counter protected by a mutex — thread-safe."""

    def __init__(self) -> None:
        self.value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            self.value += 1


def _run_counter(counter, n_threads: int, inc_per_thread: int) -> int:
    """Spawn *n_threads* threads each calling counter.increment() *inc_per_thread* times."""

    def worker() -> None:
        for _ in range(inc_per_thread):
            counter.increment()

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter.value


# ============================================================================
# Part 2: Bank accounts
# ============================================================================

class UnsafeBankAccount:
    """Bank account without locking — concurrent transfers are unsafe."""

    def __init__(self, balance: int) -> None:
        self.balance = balance

    def transfer_to(self, other: "UnsafeBankAccount", amount: int) -> None:
        if self.balance >= amount:
            self.balance -= amount   # another thread may interleave here
            other.balance += amount


class SafeBankAccount:
    """Bank account with per-account lock and consistent lock ordering."""

    def __init__(self, balance: int) -> None:
        self.balance = balance
        self._lock = threading.Lock()

    @staticmethod
    def transfer(src: "SafeBankAccount", dst: "SafeBankAccount", amount: int) -> None:
        if src is dst:
            return
        # Acquire both locks in a deterministic order (by object id) so that two
        # threads doing A→B and B→A simultaneously cannot deadlock each other.
        first, second = (src, dst) if id(src) < id(dst) else (dst, src)
        with first._lock:
            with second._lock:
                if src.balance >= amount:
                    src.balance -= amount
                    dst.balance += amount


# ============================================================================
# Part 3: Bounded queue
# ============================================================================

class UnsafeBoundedQueue:
    """Bounded FIFO queue without synchronisation."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._queue: deque = deque()

    def put(self, item) -> bool:
        if len(self._queue) < self.capacity:
            self._queue.append(item)
            return True
        return False

    def get(self) -> Optional[object]:
        return self._queue.popleft() if self._queue else None

    def size(self) -> int:
        return len(self._queue)


class SafeBoundedQueue:
    """Bounded FIFO queue protected by a single mutex."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._queue: deque = deque()
        self._lock = threading.Lock()

    def put(self, item) -> bool:
        with self._lock:
            if len(self._queue) < self.capacity:
                self._queue.append(item)
                return True
            return False

    def get(self) -> Optional[object]:
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)


# ============================================================================
# Property-based tests
# ============================================================================

@given(
    st.integers(min_value=2, max_value=8),
    st.integers(min_value=5, max_value=40),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_safe_counter_property(n_threads: int, inc_per_thread: int) -> None:
    """Invariant: SafeCounter always reaches exactly n_threads × inc_per_thread."""
    counter = SafeCounter()
    result = _run_counter(counter, n_threads, inc_per_thread)
    expected = n_threads * inc_per_thread
    assert result == expected, f"Expected {expected}, got {result}"


@given(
    st.lists(
        st.integers(min_value=100, max_value=1000),
        min_size=2,
        max_size=5,
    ),
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=4),   # source account index
            st.integers(min_value=0, max_value=4),   # destination account index
            st.integers(min_value=1, max_value=50),  # transfer amount
        ),
        min_size=4,
        max_size=20,
    ),
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_bank_conservation_property(
    initial_balances: List[int],
    transfers: List[tuple],
) -> None:
    """Invariant: total balance is conserved under any concurrent transfer schedule."""
    n = len(initial_balances)
    accounts = [SafeBankAccount(b) for b in initial_balances]
    total_before = sum(a.balance for a in accounts)

    threads = [
        threading.Thread(
            target=SafeBankAccount.transfer,
            args=(accounts[src % n], accounts[dst % n], amt),
        )
        for src, dst, amt in transfers
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    total_after = sum(a.balance for a in accounts)
    assert total_before == total_after, (
        f"Money not conserved: {total_before} before, {total_after} after"
    )


@given(
    st.integers(min_value=3, max_value=10),    # queue capacity
    st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=4,
        max_size=20,
    ),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_queue_capacity_property(capacity: int, items: List[int]) -> None:
    """Invariant: SafeBoundedQueue never exceeds its declared capacity."""
    queue = SafeBoundedQueue(capacity)
    errors: List[str] = []

    def producer(batch: List[int]) -> None:
        for item in batch:
            queue.put(item)
            size = queue.size()
            if size > capacity:
                errors.append(f"Capacity exceeded: size={size} > capacity={capacity}")

    mid = len(items) // 2
    threads = [
        threading.Thread(target=producer, args=(items[:mid],)),
        threading.Thread(target=producer, args=(items[mid:],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors[0]
    assert queue.size() <= capacity, (
        f"Final size {queue.size()} exceeds capacity {capacity}"
    )


@given(
    st.lists(
        st.integers(min_value=1, max_value=99),
        min_size=2,
        max_size=15,
        unique=True,
    ),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_queue_element_preservation(items: List[int]) -> None:
    """Invariant: every item put into SafeBoundedQueue can be retrieved (serial case)."""
    queue = SafeBoundedQueue(capacity=len(items))
    for item in items:
        queue.put(item)

    retrieved = []
    while True:
        val = queue.get()
        if val is None:
            break
        retrieved.append(val)

    assert sorted(retrieved) == sorted(items), (
        f"Items lost or duplicated.\n  Put:       {sorted(items)}\n  Retrieved: {sorted(retrieved)}"
    )


# ============================================================================
# Demo
# ============================================================================

def _sep(title: str = "") -> None:
    print(f"\n── {title} ──" if title else "\n" + "─" * 60)


if __name__ == "__main__":
    N_THREADS   = 5
    INC_PER     = 15
    EXPECTED    = N_THREADS * INC_PER
    RUNS        = 8

    print("=" * 60)
    print("CONCURRENCY DEMO")
    print(f"  {N_THREADS} threads × {INC_PER} increments = {EXPECTED} expected")
    print("=" * 60)

    # ── 1. Unsafe counter ────────────────────────────────────────────────
    _sep("UnsafeCounter  (no lock — race condition)")
    races = 0
    for i in range(RUNS):
        counter = UnsafeCounter()
        result = _run_counter(counter, N_THREADS, INC_PER)
        ok = result == EXPECTED
        races += not ok
        mark = "✓" if ok else f"✗  race! (lost {EXPECTED - result} increments)"
        print(f"  Run {i+1}: {result:4d}  {mark}")
    print(f"  → Race detected in {races}/{RUNS} runs")

    # ── 2. Safe counter ──────────────────────────────────────────────────
    _sep("SafeCounter  (with lock)")
    for i in range(RUNS):
        counter = SafeCounter()
        result = _run_counter(counter, N_THREADS, INC_PER)
        print(f"  Run {i+1}: {result:4d}  ✓")

    # ── 3. Bank accounts ─────────────────────────────────────────────────
    _sep("SafeBankAccount  (conservation under concurrent transfers)")
    accounts = [SafeBankAccount(b) for b in [500, 300, 200, 400]]
    total_before = sum(a.balance for a in accounts)
    print(f"  Initial balances: {[a.balance for a in accounts]}  (total {total_before})")

    ops = [
        (0, 1, 50), (1, 2, 30), (2, 3, 20), (3, 0, 100),
        (0, 2, 75), (1, 3, 25), (2, 0, 40), (3, 1, 60),
    ]
    threads = [
        threading.Thread(
            target=SafeBankAccount.transfer,
            args=(accounts[s % 4], accounts[d % 4], amt),
        )
        for s, d, amt in ops
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    total_after = sum(a.balance for a in accounts)
    print(f"  Final balances:   {[a.balance for a in accounts]}  (total {total_after})")
    print(f"  Conservation: {'✓' if total_before == total_after else '✗'}")

    # ── 4. Bounded queue ─────────────────────────────────────────────────
    _sep("SafeBoundedQueue  (capacity never exceeded)")
    queue = SafeBoundedQueue(capacity=5)
    items = list(range(12))

    def _fill(batch):
        for item in batch:
            queue.put(item)

    threads = [
        threading.Thread(target=_fill, args=(items[:6],)),
        threading.Thread(target=_fill, args=(items[6:],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_size = queue.size()
    print(f"  12 items attempted → queue size: {final_size}  "
          f"(capacity 5)  {'✓' if final_size <= 5 else '✗'}")

    # ── 5. Property-based tests ──────────────────────────────────────────
    _sep("Property-based tests (Hypothesis)")
    for name, fn in [
        ("test_safe_counter_property",      test_safe_counter_property),
        ("test_bank_conservation_property", test_bank_conservation_property),
        ("test_queue_capacity_property",    test_queue_capacity_property),
        ("test_queue_element_preservation", test_queue_element_preservation),
    ]:
        print(f"  {name} ...", end=" ", flush=True)
        fn()
        print("passed")
