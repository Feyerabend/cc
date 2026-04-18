"""concurrency_async.py   async/await concurrency with asyncio

Same five-worker scenario as concurrency_threads.py, but using a single
event loop instead of OS threads.  Better suited to high-concurrency
network I/O (e.g. a web server or microservice gateway).

Run: python concurrency_async.py
"""

import asyncio
import time


async def task(i: int) -> None:
    print(f"Task {i} start")
    await asyncio.sleep(2)      # yields control back to the event loop
    print(f"Task {i} end")


async def main() -> None:
    start = time.perf_counter()

    # gather() schedules all coroutines concurrently on the single event loop
    await asyncio.gather(*(task(i) for i in range(5)))

    elapsed = time.perf_counter() - start
    print(f"\nAll 5 tasks finished in {elapsed:.2f} s  "
          "(single thread, no OS threads needed)")


if __name__ == "__main__":
    asyncio.run(main())
