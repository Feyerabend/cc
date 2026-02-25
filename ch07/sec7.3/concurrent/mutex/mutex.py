#!/usr/bin/env python3
"""
Mutex demonstration using the ToyVM.

This script demonstrates the classic race condition problem and how mutexes solve it.
We create multiple threads that increment a shared counter without proper synchronisation,
then show how a mutex prevents the race condition.
"""

from vm import ToyVM


def demo_without_mutex():
    """
    Demonstrate race condition without mutex protection.
    Multiple threads increment a shared counter, leading to lost updates.
    """
    print("=" * 70)
    print("DEMONSTRATION 1: Race Condition WITHOUT Mutex")
    print("=" * 70)
    print("Four threads each increment a shared counter 100 times.")
    print("Expected result: 400 | Actual result will likely be less due to races")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    # Create a global counter
    vm.globals['counter'] = 0
    
    # Each thread will:
    # 1. Loop 100 times
    # 2. Load counter value
    # 3. Increment it
    # 4. Store it back (race condition happens between load and store)
    increment_instructions = [
        ("PUSH", 100),           # Loop counter
        ("STORE", "loop_count"),
        
        # Loop start (PC=2)
        ("LOAD", "loop_count"),
        ("PUSH", 1),
        ("SUB",),
        ("DUP",),
        ("STORE", "loop_count"),
        ("PUSH", -1),
        ("JUMP_IF", 16),         # Exit loop if loop_count <= 0
        
        # Critical section WITHOUT mutex protection
        ("LOAD", "counter"),     # Load from global
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "counter"),
        
        ("JUMP", 2),             # Back to loop start
        
        # End - print final value
        ("LOAD", "counter"),
        ("PRINT", "Thread finished, counter is now: {}"),
    ]
    
    # Create 4 threads
    for i in range(4):
        vm.create_thread(increment_instructions, name=f"thread-{i}")
    
    # Run the VM
    vm.run()
    
    print("-" * 70)
    print(f"Final counter value: {vm.globals.get('counter', 0)}")
    print(f"Expected value: 400")
    print(f"Lost updates: {400 - vm.globals.get('counter', 0)}")
    print()


def demo_with_mutex():
    """
    Demonstrate proper synchronisation with mutex protection.
    Multiple threads increment a shared counter with mutex, preventing race conditions.
    """
    print("=" * 70)
    print("DEMONSTRATION 2: Proper Synchronisation WITH Mutex")
    print("=" * 70)
    print("Four threads each increment a shared counter 100 times.")
    print("Expected result: 400 | Protected by mutex, result will be correct")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    # Create a global counter
    vm.globals['counter'] = 0
    
    # Create a shared mutex
    lock_name = vm.create_lock("counter_lock")
    
    # Each thread will:
    # 1. Loop 100 times
    # 2. Acquire the mutex
    # 3. Load counter, increment, store (critical section)
    # 4. Release the mutex
    increment_with_lock_instructions = [
        ("PUSH", 100),
        ("STORE", "loop_count"),
        
        # Loop start (PC=2)
        ("LOAD", "loop_count"),
        ("PUSH", 1),
        ("SUB",),
        ("DUP",),
        ("STORE", "loop_count"),
        ("PUSH", -1),
        ("JUMP_IF", 21),         # Exit loop if loop_count <= 0
        
        # Acquire mutex BEFORE critical section
        ("PUSH", lock_name),
        ("LOCK_ACQUIRE",),       # Blocks if lock is held by another thread
        
        # Critical section (now protected)
        ("LOAD", "counter"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "counter"),
        
        # Release mutex AFTER critical section
        ("PUSH", lock_name),
        ("LOCK_RELEASE",),
        
        ("JUMP", 2),
        
        # End
        ("LOAD", "counter"),
        ("PRINT", "Thread finished, counter is now: {}"),
    ]
    
    # Create 4 threads
    for i in range(4):
        vm.create_thread(increment_with_lock_instructions, name=f"thread-{i}")
    
    # Run the VM
    vm.run()
    
    print("-" * 70)
    print(f"Final counter value: {vm.globals.get('counter', 0)}")
    print(f"Expected value: 400")
    print(f"Lost updates: {400 - vm.globals.get('counter', 0)}")
    print()


def demo_deadlock_scenario():
    """
    Demonstrate a potential deadlock scenario with multiple locks.
    Two threads each try to acquire two locks in opposite order.
    """
    print("=" * 70)
    print("DEMONSTRATION 3: Deadlock Scenario (Multiple Locks)")
    print("=" * 70)
    print("Two threads acquire locks in opposite order - potential deadlock!")
    print("Thread A: lock1 → lock2 | Thread B: lock2 → lock1")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    # Create two locks
    lock1 = vm.create_lock("lock1")
    lock2 = vm.create_lock("lock2")
    
    # Thread A: acquires lock1, then lock2
    thread_a_instructions = [
        ("PRINT", "Attempting to acquire lock1..."),
        ("PUSH", lock1),
        ("LOCK_ACQUIRE",),
        ("PRINT", "Acquired lock1! Now attempting lock2..."),
        
        # Small delay to increase chance of interleaving
        ("PUSH", 10),
        ("SLEEP",),
        
        ("PUSH", lock2),
        ("LOCK_ACQUIRE",),
        ("PRINT", "Acquired lock2! Working in critical section..."),
        
        # Release in reverse order
        ("PUSH", lock2),
        ("LOCK_RELEASE",),
        ("PRINT", "Released lock2"),
        
        ("PUSH", lock1),
        ("LOCK_RELEASE",),
        ("PRINT", "Released lock1 - Thread A complete!"),
    ]
    
    # Thread B: acquires lock2, then lock1 (OPPOSITE ORDER - dangerous!)
    thread_b_instructions = [
        ("PRINT", "Attempting to acquire lock2..."),
        ("PUSH", lock2),
        ("LOCK_ACQUIRE",),
        ("PRINT", "Acquired lock2! Now attempting lock1..."),
        
        # Small delay to increase chance of interleaving
        ("PUSH", 10),
        ("SLEEP",),
        
        ("PUSH", lock1),
        ("LOCK_ACQUIRE",),
        ("PRINT", "Acquired lock1! Working in critical section..."),
        
        # Release in reverse order
        ("PUSH", lock1),
        ("LOCK_RELEASE",),
        ("PRINT", "Released lock1"),
        
        ("PUSH", lock2),
        ("LOCK_RELEASE",),
        ("PRINT", "Released lock2 - Thread B complete!"),
    ]
    
    vm.create_thread(thread_a_instructions, name="Thread-A")
    vm.create_thread(thread_b_instructions, name="Thread-B")
    
    print("\nNote: This may deadlock! If both threads acquire their first lock")
    print("simultaneously, each will wait forever for the other's lock.")
    print("\nRunning (will timeout after a few seconds if deadlocked)...\n")
    
    # Run with timeout to avoid infinite wait
    import threading
    import time
    
    run_thread = threading.Thread(target=vm.run)
    run_thread.daemon = True
    run_thread.start()
    run_thread.join(timeout=3.0)
    
    if run_thread.is_alive():
        print("\n" + "!" * 70)
        print("DEADLOCK DETECTED! Threads are stuck waiting for each other.")
        print("!" * 70)
        vm.running = False
    
    print()


def demo_mutex_best_practices():
    """
    Demonstrate best practices: always acquire locks in the same order.
    """
    print("=" * 70)
    print("DEMONSTRATION 4: Deadlock Prevention (Consistent Lock Ordering)")
    print("=" * 70)
    print("Two threads acquire locks in the SAME order - no deadlock!")
    print("Thread A: lock1 → lock2 | Thread B: lock1 → lock2 (same order)")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    # Create two locks
    lock1 = vm.create_lock("lock1")
    lock2 = vm.create_lock("lock2")
    
    # Both threads acquire in the same order: lock1 first, then lock2
    thread_instructions = [
        ("PRINT", "Attempting to acquire lock1..."),
        ("PUSH", lock1),
        ("LOCK_ACQUIRE",),
        ("PRINT", "Acquired lock1! Now attempting lock2..."),
        
        ("PUSH", lock2),
        ("LOCK_ACQUIRE",),
        ("PRINT", "Acquired both locks! Working in critical section..."),
        
        # Do some "work"
        ("PUSH", 50),
        ("SLEEP",),
        
        # Release in reverse order (common practice)
        ("PUSH", lock2),
        ("LOCK_RELEASE",),
        ("PRINT", "Released lock2"),
        
        ("PUSH", lock1),
        ("LOCK_RELEASE",),
        ("PRINT", "Released lock1 - Thread complete!"),
    ]
    
    vm.create_thread(thread_instructions, name="Thread-A")
    vm.create_thread(thread_instructions, name="Thread-B")
    
    print("\nRunning...\n")
    vm.run()
    
    print("-" * 70)
    print("Success! Both threads completed without deadlock.")
    print("Key: Always acquire multiple locks in a consistent global order.")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "MUTEX DEMONSTRATION WITH TOYVM" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Run all demonstrations
    demo_without_mutex()
    input("Press Enter to continue to next demonstration...\n")
    
    demo_with_mutex()
    input("Press Enter to continue to next demonstration...\n")
    
    demo_deadlock_scenario()
    input("Press Enter to continue to final demonstration...\n")
    
    demo_mutex_best_practices()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("1. WITHOUT mutex: Race conditions cause lost updates")
    print("2. WITH mutex: Proper synchronisation ensures correctness")
    print("3. Multiple locks: Wrong order → deadlock")
    print("4. Multiple locks: Consistent order → safe execution")
    print("=" * 70)
    print("\nMutexes are essential for thread safety, but must be used carefully!")
    print()
