import signal
import asyncio
import os
from typing import Callable, Dict, List

# Interrupt Vector Table (IVT)
class InterruptDispatcher:
    def __init__(self):
        self.table: Dict[int, List[Callable[[], None]]] = {}

    def register(self, sig: int, handler: Callable[[], None]):
        if sig not in self.table:
            self.table[sig] = []
        self.table[sig].append(handler)

    def dispatch(self, sig: int):
        print(f"[IVT] Signal {sig} received. Dispatching...")
        for handler in self.table.get(sig, []):
            asyncio.ensure_future(self._run_async(handler))

    async def _run_async(self, handler: Callable[[], None]):
        await asyncio.sleep(0)  # Yield to event loop
        handler()

# Global dispatcher instance
dispatcher = InterruptDispatcher()

# Connect dispatcher to OS-level signal
def signal_handler(sig_num, frame):
    dispatcher.dispatch(sig_num)

# Register signal handler for SIGUSR1
signal.signal(signal.SIGUSR1, signal_handler)

# Example async-safe observer handlers
def handler_A():
    print("Handler A reacting to signal!")

def handler_B():
    print("Handler B doing something else!")

# Register observers to SIGUSR1
dispatcher.register(signal.SIGUSR1, handler_A)
dispatcher.register(signal.SIGUSR1, handler_B)

# Run a simple event loop to await signals
async def main():
    print(f"Send SIGUSR1 using: kill -USR1 {os.getpid()}")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down.")
