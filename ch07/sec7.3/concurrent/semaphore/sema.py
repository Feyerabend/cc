import time
import random
from collections import deque
from typing import List, Dict, Any, Optional, Callable, Tuple
import uuid

from vm import ToyVM

def example_semaphore_usage():
    vm = ToyVM()
    
    worker_instructions = [
        ("LOAD", "semaphore"),
        ("SEMAPHORE_ACQUIRE",),
        ("LOAD", "id"),
        ("PRINT", "Worker {} accessing resource"),
        ("PUSH", 50),
        ("SLEEP",),
        ("LOAD", "id"),
        ("PRINT", "Worker {} releasing resource"),
        ("LOAD", "semaphore"),
        ("SEMAPHORE_RELEASE",),
    ]

    main_instructions = [
        ("PUSH", 2),
        ("SEMAPHORE_CREATE",),
        ("GLOBAL_STORE", "semaphore"),
        ("PUSH", 0),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [worker_instructions]),
        ("PUSH", 1),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [worker_instructions]),
        ("PUSH", 2),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [worker_instructions]),
        ("PUSH", 3),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [worker_instructions]),
        ("PUSH", 200),
        ("SLEEP",),
        ("PRINT", "Semaphore usage simulation complete"),
    ]
    
    vm.create_thread(main_instructions, "main", priority=1)
    vm.run(debug=True)

if __name__ == "__main__":
    print("\n=== Example: Semaphore Usage ===")
    example_semaphore_usage()