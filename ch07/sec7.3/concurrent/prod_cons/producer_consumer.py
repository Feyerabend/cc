#!/usr/bin/env python3
"""
Producer-Consumer Problem demonstration using the ToyVM
"""

from vm import ToyVM


def demo_without_synchronisation():
    """
    Chaos without synchronisation.
    """
    print()
    print("DEMONSTRATION 1: Producer-Consumer WITHOUT Synchronisation")
    print()
    print("2 producers (5 items each), 2 consumers (5 items each)")
    print("Expected: Chaos, race conditions, incorrect counts")
    print()
    
    vm = ToyVM()
    vm.debug = False
    
    vm.globals['buffer_count'] = 0
    vm.globals['items_produced'] = 0
    vm.globals['items_consumed'] = 0
    
    # Producer
    producer_instructions = [
        ("PUSH", 5),
        ("STORE", "count"),
        
        # Loop (PC=2)
        # Produce (RACE CONDITION!)
        ("LOAD", "items_produced"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "items_produced"),
        
        ("LOAD", "buffer_count"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "buffer_count"),
        ("PRINT", "Produced, buffer: {}"),
        
        # Decrement
        ("LOAD", "count"),
        ("PUSH", 1),
        ("SUB",),
        ("STORE", "count"),
        
        # Continue if count > 0
        ("LOAD", "count"),
        ("PUSH", 1),
        ("SUB",),
        ("JUMP_IF", 2),
        
        ("PRINT", "Producer done"),
    ]
    
    # Consumer
    consumer_instructions = [
        ("PUSH", 5),
        ("STORE", "count"),
        
        # Loop (PC=2)
        # Consume (RACE CONDITION!)
        ("LOAD", "buffer_count"),
        ("PUSH", 1),
        ("SUB",),
        ("GLOBAL_STORE", "buffer_count"),
        
        ("LOAD", "items_consumed"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "items_consumed"),
        ("PRINT", "Consumed, buffer: {}"),
        
        # Decrement
        ("LOAD", "count"),
        ("PUSH", 1),
        ("SUB",),
        ("STORE", "count"),
        
        # Continue if count > 0
        ("LOAD", "count"),
        ("PUSH", 1),
        ("SUB",),
        ("JUMP_IF", 2),
        
        ("PRINT", "Consumer done"),
    ]
    
    vm.create_thread(producer_instructions, name="Producer-1")
    vm.create_thread(producer_instructions, name="Producer-2")
    vm.create_thread(consumer_instructions, name="Consumer-1")
    vm.create_thread(consumer_instructions, name="Consumer-2")
    
    vm.run()
    
    print("-" * 70)
    print(f"Items produced: {vm.globals.get('items_produced', 0)} (expected: 10)")
    print(f"Items consumed: {vm.globals.get('items_consumed', 0)} (expected: 10)")
    print(f"Buffer count: {vm.globals.get('buffer_count', 0)} (expected: 0)")
    print("Race conditions cause incorrect results!")
    print()


def demo_with_semaphores():
    """
    Proper solution with semaphores.
    """
    print()
    print("DEMONSTRATION 2: Producer-Consumer WITH Semaphores")
    print()
    print("2 producers (8 items each), 3 consumers")
    print("Expected: All 16 items correctly processed")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    BUFFER_SIZE = 5
    ITEMS_PER_PRODUCER = 8
    TOTAL_ITEMS = 16
    
    # Synchronisation primitives
    buffer_lock = vm.create_lock("buffer_lock")
    empty_slots = vm.create_semaphore(BUFFER_SIZE, "empty_sem")
    filled_slots = vm.create_semaphore(0, "filled_sem")
    buffer_queue = vm.create_message_queue("buffer_queue")
    
    # Counters
    item_id = vm.create_atomic_counter(0, "item_id")
    consumed_count = vm.create_atomic_counter(0, "consumed_count")
    
    # Producer
    producer_instructions = [
        ("PUSH", ITEMS_PER_PRODUCER),
        ("STORE", "count"),
        
        # Loop (PC=2)
        # Wait for empty slot
        ("PUSH", empty_slots),
        ("SEMAPHORE_ACQUIRE",),
        
        # Lock buffer
        ("PUSH", buffer_lock),
        ("LOCK_ACQUIRE",),
        
        # Create item
        ("PUSH", item_id),
        ("ATOMIC_INCREMENT",),
        ("DUP",),
        ("PRINT", "Produced item {}"),
        
        # Send to queue
        ("PUSH", buffer_queue),
        ("PUSH", buffer_queue),  # Dummy value
        ("QUEUE_SEND",),
        
        # Unlock buffer
        ("PUSH", buffer_lock),
        ("LOCK_RELEASE",),
        
        # Signal filled slot
        ("PUSH", filled_slots),
        ("SEMAPHORE_RELEASE",),
        
        # Decrement
        ("LOAD", "count"),
        ("PUSH", 1),
        ("SUB",),
        ("STORE", "count"),
        
        # Continue if count > 0
        ("LOAD", "count"),
        ("PUSH", 1),
        ("SUB",),
        ("JUMP_IF", 2),
        
        ("PRINT", "Producer done"),
    ]
    
    # Consumer
    consumer_instructions = [
        # Loop (PC=0)
        # Check if all consumed
        ("PUSH", consumed_count),
        ("ATOMIC_GET",),
        ("PUSH", TOTAL_ITEMS),
        ("SUB",),
        ("PUSH", -1),
        ("JUMP_IF", 24),  # Exit if consumed >= TOTAL
        
        # Wait for filled slot
        ("PUSH", filled_slots),
        ("SEMAPHORE_ACQUIRE",),
        
        # Lock buffer
        ("PUSH", buffer_lock),
        ("LOCK_ACQUIRE",),
        
        # Receive from queue
        ("PUSH", buffer_queue),
        ("QUEUE_RECEIVE",),
        ("DUP",),
        ("PRINT", "Consumed item {}"),
        ("POP",),
        
        # Increment consumed count
        ("PUSH", consumed_count),
        ("ATOMIC_INCREMENT",),
        ("POP",),
        
        # Unlock buffer
        ("PUSH", buffer_lock),
        ("LOCK_RELEASE",),
        
        # Signal empty slot
        ("PUSH", empty_slots),
        ("SEMAPHORE_RELEASE",),
        
        ("JUMP", 0),
        
        ("PRINT", "Consumer done"),
    ]
    
    vm.create_thread(producer_instructions, name="Producer-1")
    vm.create_thread(producer_instructions, name="Producer-2")
    vm.create_thread(consumer_instructions, name="Consumer-1")
    vm.create_thread(consumer_instructions, name="Consumer-2")
    vm.create_thread(consumer_instructions, name="Consumer-3")
    
    print("\nRunning...\n")
    vm.run(max_steps=5000)
    
    print("-" * 70)
    consumed = vm.atomic_counters["consumed_count"].get()
    print(f"Total consumed: {consumed} (expected: {TOTAL_ITEMS})")
    
    if consumed == TOTAL_ITEMS:
        print("\n  SUCCESS: All items correctly processed!")
    print()


if __name__ == "__main__":
    print()
    print()
    print(".   PRODUCER-CONSUMER PROBLEM WITH TOYVM")
    print()
    print()
    
    demo_without_synchronisation()
    input("\nPress Enter to continue...\n")
    
    demo_with_semaphores()
    print()

#    1. NO synchronisation: Race conditions, data corruption
#    2. SEMAPHORES: Proper solution - safe and efficient
