#!/usr/bin/env python3
"""
Simple Print Queue with Signal Handling

Usage:
  python3 simple_queue.py

Signals:
  kill -USR1 <pid>  # Add normal job
  kill -USR2 <pid>  # Add priority job
  kill -TERM <pid>  # Shutdown
"""

import signal
import time
import os
import random
from collections import deque
from threading import Thread

class SimpleQueue:
    def __init__(self):
        self.normal_jobs = deque()
        self.priority_jobs = deque()
        self.job_count = 0
        self.running = True
        self.current_job = None

    def add_job(self, is_priority=False):
        self.job_count += 1
        job_name = f"Document_{self.job_count}"
        pages = random.randint(1, 10)
        
        job = {
            'id': self.job_count,
            'name': job_name,
            'pages': pages
        }
        
        if is_priority:
            self.priority_jobs.append(job)
            print(f"[PRIORITY] Added Job #{job['id']}: {job['name']} ({job['pages']} pages)")
        else:
            self.normal_jobs.append(job)
            print(f"[NORMAL] Added Job #{job['id']}: {job['name']} ({job['pages']} pages)")
        
        self.show_status()

    def get_next_job(self):
        # priority jobs first
        if self.priority_jobs:
            return self.priority_jobs.popleft()
        elif self.normal_jobs:
            return self.normal_jobs.popleft()
        return None

    def process_job(self, job):
        print(f"Processing Job #{job['id']}: {job['name']}")
        
        # simulate printing each page
        for page in range(1, job['pages'] + 1):
            if not self.running:
                print(f"Job #{job['id']} cancelled!")
                return
            
            print(f"  Printing page {page}/{job['pages']}...")
            time.sleep(0.5)  # simulate print time
        
        print(f"Job #{job['id']} completed!")

    def show_status(self):
        total_jobs = len(self.priority_jobs) + len(self.normal_jobs)
        print(f"Queue status: {len(self.priority_jobs)} priority, {len(self.normal_jobs)} normal ({total_jobs} total)")

    def worker(self):
        print("Print worker started...")
        
        while self.running:
            job = self.get_next_job()
            
            if job:
                self.current_job = job
                self.process_job(job)
                self.current_job = None
            else:
                time.sleep(1)  # wait for jobs
        
        print("Print worker stopped.")

#gGlobal queue instance
queue = SimpleQueue()

def signal_handler(signum, frame):
    if signum == signal.SIGUSR1:
        queue.add_job(is_priority=False)
    elif signum == signal.SIGUSR2:
        queue.add_job(is_priority=True)
    elif signum == signal.SIGTERM:
        print("\nShutdown signal received...")
        queue.running = False
    elif signum == signal.SIGINT:
        print("\nCtrl+C pressed - shutting down...")
        queue.running = False

def main():
    # setup signal handlers
    signal.signal(signal.SIGUSR1, signal_handler)
    signal.signal(signal.SIGUSR2, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # start worker thread
    worker_thread = Thread(target=queue.worker, daemon=True)
    worker_thread.start()
    
    # show instructions
    print("=" * 50)
    print("         SIMPLE PRINT QUEUE SYSTEM")
    print("=" * 50)
    print(f"Process ID: {os.getpid()}")
    print()
    print("Commands (run in another terminal):")
    print(f"  kill -USR1 {os.getpid()}  # Add normal job")
    print(f"  kill -USR2 {os.getpid()}  # Add priority job")
    print(f"  kill -TERM {os.getpid()}  # Shutdown")
    print()
    print("Ready! Send signals to add jobs...")
    print("=" * 50)
    
    # main loop
    try:
        while queue.running:
            time.sleep(1)
    except KeyboardInterrupt:
        queue.running = False
    
    print("\nWaiting for current job to finish...")
    worker_thread.join(timeout=10)
    print("Shutdown complete!")

if __name__ == "__main__":
    main()