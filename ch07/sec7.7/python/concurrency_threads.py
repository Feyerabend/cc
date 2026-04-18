"""concurrency_threads.py   thread-based concurrency

Five workers each sleep 2 s (simulating slow I/O).
With threads the total wall time is ~2 s, not 10 s.

Run: python concurrency_threads.py
"""

import threading
import time


def worker(i: int) -> None:
    print(f"Worker {i} starting")
    time.sleep(2)      # simulate blocking I/O (network call, disk read ..)
    print(f"Worker {i} done")


if __name__ == "__main__":
    start = time.perf_counter()

    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start
    print(f"\nAll 5 workers finished in {elapsed:.2f} s  "
          "(would have taken 10 s sequentially)")
