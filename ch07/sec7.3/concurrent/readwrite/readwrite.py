import time
import random
from collections import deque
from typing import List, Dict, Any, Optional, Callable, Tuple
import uuid

from vm import ToyVM

def example_readers_writers():
    vm = ToyVM()
    
    reader_instructions = [
        ("LOAD", "lock"),
        ("LOCK_ACQUIRE",),
        ("LOAD", "counter"),
        ("ATOMIC_GET",),
        ("LOAD", "id"),
        ("PRINT", "Reader {} read value {}"),
        ("LOAD", "lock"),
        ("LOCK_RELEASE",),
        ("PUSH", 10),
        ("SLEEP",),
    ]

    writer_instructions = [
        ("LOAD", "lock"),
        ("LOCK_ACQUIRE",),
        ("LOAD", "counter"),
        ("ATOMIC_INCREMENT",),
        ("POP",),
        ("LOAD", "counter"),
        ("ATOMIC_GET",),
        ("PRINT", "Writer wrote value {}"),
        ("LOAD", "lock"),
        ("LOCK_RELEASE",),
        ("PUSH", 20),
        ("SLEEP",),
    ]

    main_instructions = [
        ("PUSH", 0),
        ("ATOMIC_CREATE",),
        ("GLOBAL_STORE", "counter"),
        ("LOCK_CREATE",),
        ("GLOBAL_STORE", "lock"),
        ("PUSH", 0),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [reader_instructions]),
        ("PUSH", 1),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [reader_instructions]),
        ("PUSH", 0),
        ("GLOBAL_STORE", "id"),
        ("PUSH", 0),
        ("THREAD_CREATE", [writer_instructions]),
        ("PUSH", 100),
        ("SLEEP",),
        ("LOAD", "counter"),
        ("ATOMIC_GET",),
        ("PRINT", "Final counter value: {}"),
        ("PRINT", "Readers-Writers simulation complete"),
    ]
    
    vm.create_thread(main_instructions, "main", priority=1)
    vm.run(debug=True)

if __name__ == "__main__":
    print("\n=== Example: Readers-Writers Problem ===")
    example_readers_writers()