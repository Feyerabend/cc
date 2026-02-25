#!/usr/bin/env python3
"""
Mutex demonstration using the ToyVM

This script demonstrates the classic race condition problem and how mutexes solve it.
"""

from vm import ToyVM


def demo_without_mutex():
    """
    Demonstrate race condition without mutex protection.
    """
    print()
    print("DEMONSTRATION 1: Race Condition WITHOUT Mutex")
    print()
    print("Four threads each increment a shared counter 100 times.")
    print("Expected: 400 | Actual will be less due to race conditions")
    print()
    
    vm = ToyVM()
    vm.debug = False
    vm.globals['counter'] = 0
    
    # Simple increment loop: 100 iterations
    increment_instructions = [
        ("PUSH", 100),
        ("STORE", "loop_count"),
        
        # Loop body (PC=2)
        # Critical section WITHOUT mutex
        ("LOAD", "counter"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "counter"),
        
        # Decrement counter
        ("LOAD", "loop_count"),
        ("PUSH", 1),
        ("SUB",),
        ("STORE", "loop_count"),
        
        # Continue if loop_count > 0
        ("LOAD", "loop_count"),
        ("PUSH", 1),
        ("SUB",),
        ("JUMP_IF", 2),
        
        # Done
        ("LOAD", "counter"),
        ("PRINT", "Thread finished, counter: {}"),
    ]
    
    for i in range(4):
        vm.create_thread(increment_instructions, name=f"thread-{i}")
    
    vm.run()
    
    print("-" * 70)
    print(f"Final counter: {vm.globals.get('counter', 0)}")
    print(f"Expected: 400")
    print(f"Lost updates: {400 - vm.globals.get('counter', 0)}")
    print()


def demo_with_mutex():
    """
    Demonstrate proper synchronisation with mutex.
    """
    print()
    print("DEMONSTRATION 2: Proper Synchronisation WITH Mutex")
    print()
    print("Four threads each increment a shared counter 100 times.")
    print("Expected: 400 | Result will be correct with mutex")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    vm.globals['counter'] = 0
    
    lock_name = vm.create_lock("counter_lock")
    
    increment_with_lock_instructions = [
        ("PUSH", 100),
        ("STORE", "loop_count"),
        
        # Loop body (PC=2)
        # Acquire mutex
        ("PUSH", lock_name),
        ("LOCK_ACQUIRE",),
        
        # Critical section (protected)
        ("LOAD", "counter"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "counter"),
        
        # Release mutex
        ("PUSH", lock_name),
        ("LOCK_RELEASE",),
        
        # Decrement counter
        ("LOAD", "loop_count"),
        ("PUSH", 1),
        ("SUB",),
        ("STORE", "loop_count"),
        
        # Continue if loop_count > 0
        ("LOAD", "loop_count"),
        ("PUSH", 1),
        ("SUB",),
        ("JUMP_IF", 2),
        
        # Done
        ("LOAD", "counter"),
        ("PRINT", "Thread finished, counter: {}"),
    ]
    
    for i in range(4):
        vm.create_thread(increment_with_lock_instructions, name=f"thread-{i}")
    
    vm.run()
    
    print("-" * 70)
    print(f"Final counter: {vm.globals.get('counter', 0)}")
    print(f"Expected: 400")
    print(f"Lost updates: {400 - vm.globals.get('counter', 0)}")
    print()


if __name__ == "__main__":
    print()
    print()
    print(".      MUTEX DEMONSTRATION WITH TOYVM")
    print()
    print()
    
    demo_without_mutex()
    input("\nPress Enter to continue...\n")
    
    demo_with_mutex()
    print()
    
#   1. WITHOUT mutex: Race conditions cause lost updates
#   2. WITH mutex: Proper synchronisation ensures correctness
