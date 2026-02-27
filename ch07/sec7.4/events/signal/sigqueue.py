import queue
import signal
import threading
import time
import os

# setup queues per signal
signal_queues = {
    signal.SIGUSR1: queue.Queue(),
    signal.SIGUSR2: queue.Queue()
}

# signal handler that enqueues
def signal_handler(signum, frame):
    if signum in signal_queues:
        signal_queues[signum].put(signum)
        print(f"Enqueued signal {signum}")

# worker function
def signal_worker(signum):
    q = signal_queues[signum]
    while True:
        sig = q.get()
        print(f"Handled signal {sig} in worker")
        q.task_done()

# register and start threads
def setup_signal_handling():
    for sig in signal_queues:
        signal.signal(sig, signal_handler)
        thread = threading.Thread(target=signal_worker, args=(sig,), daemon=True)
        thread.start()

setup_signal_handling()
print(f"Python process PID: {os.getpid()}")
print("Send SIGUSR1 or SIGUSR2 to this process using:")
print(f"  kill -USR1 {os.getpid()}")
print(f"  kill -USR2 {os.getpid()}")

while True:
    time.sleep(1)