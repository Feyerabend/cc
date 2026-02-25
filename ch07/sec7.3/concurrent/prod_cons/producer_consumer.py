#!/usr/bin/env python3
"""
Producer-Consumer Problem demonstration using the ToyVM.

This script demonstrates the classic producer-consumer synchronisation problem
with a bounded buffer. Producers generate items and add them to a shared buffer,
while consumers retrieve and process those items. Proper synchronisation prevents
buffer overflow, underflow, and race conditions.
"""

from vm import ToyVM


def demo_without_synchronisation():
    """
    Demonstrate the chaos that ensues without proper synchronisation.
    Producers and consumers access a shared buffer without coordination,
    leading to potential data loss and corruption.
    """
    print("=" * 70)
    print("DEMONSTRATION 1: Producer-Consumer WITHOUT Synchronisation")
    print("=" * 70)
    print("2 producers, 2 consumers, buffer size 3 - NO synchronisation!")
    print("Expected: Data loss, race conditions, unpredictable behaviour")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    # Shared state (unsynchronised)
    vm.globals['buffer_count'] = 0
    vm.globals['items_produced'] = 0
    vm.globals['items_consumed'] = 0
    
    # Producer: creates 5 items without checking if buffer is full
    producer_instructions = [
        ("PUSH", 5),
        ("STORE", "produce_count"),
        
        # Production loop (PC=2)
        ("LOAD", "produce_count"),
        ("PUSH", 1),
        ("SUB",),
        ("DUP",),
        ("STORE", "produce_count"),
        ("PUSH", -1),
        ("JUMP_IF", 18),  # Exit if produce_count <= 0
        
        # "Produce" item (increment global counter - RACE CONDITION!)
        ("LOAD", "items_produced"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "items_produced"),
        
        # Add to buffer count (RACE CONDITION!)
        ("LOAD", "buffer_count"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "buffer_count"),
        ("PRINT", "Produced item, buffer count now: {}"),
        
        ("JUMP", 2),
        
        ("PRINT", "Producer finished"),
    ]
    
    # Consumer: consumes 5 items without checking if buffer is empty
    consumer_instructions = [
        ("PUSH", 5),
        ("STORE", "consume_count"),
        
        # Consumption loop (PC=2)
        ("LOAD", "consume_count"),
        ("PUSH", 1),
        ("SUB",),
        ("DUP",),
        ("STORE", "consume_count"),
        ("PUSH", -1),
        ("JUMP_IF", 18),  # Exit if consume_count <= 0
        
        # Remove from buffer count (RACE CONDITION!)
        ("LOAD", "buffer_count"),
        ("PUSH", 1),
        ("SUB",),
        ("GLOBAL_STORE", "buffer_count"),
        
        # "Consume" item (increment global counter - RACE CONDITION!)
        ("LOAD", "items_consumed"),
        ("PUSH", 1),
        ("ADD",),
        ("GLOBAL_STORE", "items_consumed"),
        ("PRINT", "Consumed item, buffer count now: {}"),
        
        ("JUMP", 2),
        
        ("PRINT", "Consumer finished"),
    ]
    
    # Create producers and consumers
    vm.create_thread(producer_instructions, name="Producer-1")
    vm.create_thread(producer_instructions, name="Producer-2")
    vm.create_thread(consumer_instructions, name="Consumer-1")
    vm.create_thread(consumer_instructions, name="Consumer-2")
    
    vm.run()
    
    print("-" * 70)
    print(f"Items produced: {vm.globals.get('items_produced', 0)} (expected: 10)")
    print(f"Items consumed: {vm.globals.get('items_consumed', 0)} (expected: 10)")
    print(f"Final buffer count: {vm.globals.get('buffer_count', 0)} (expected: 0)")
    print("Note: Race conditions cause unpredictable and incorrect results!")
    print()


def demo_with_semaphores():
    """
    Proper producer-consumer implementation using semaphores.
    Uses counting semaphores to signal buffer full/empty conditions.
    """
    print("=" * 70)
    print("DEMONSTRATION 2: Producer-Consumer WITH Semaphores (Proper Solution)")
    print("=" * 70)
    print("2 producers, 3 consumers, buffer size 5 - Full synchronisation")
    print("Expected: Correct synchronisation, no busy-waiting, all items processed")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    BUFFER_SIZE = 5
    ITEMS_PER_PRODUCER = 8
    TOTAL_ITEMS = 2 * ITEMS_PER_PRODUCER
    
    # Create synchronisation primitives
    buffer_lock = vm.create_lock("buffer_lock")
    empty_slots = vm.create_semaphore(BUFFER_SIZE, "empty_sem")  # Initially 5 empty slots
    filled_slots = vm.create_semaphore(0, "filled_sem")          # Initially 0 filled slots
    
    # Create message queue for actual data transfer
    buffer_queue = vm.create_message_queue("buffer_queue")
    
    # Atomic counters for tracking
    item_id_counter = vm.create_atomic_counter(0, "item_id")
    consumed_counter = vm.create_atomic_counter(0, "consumed_count")
    
    # Producer instructions
    producer_instructions = [
        ("PUSH", ITEMS_PER_PRODUCER),
        ("STORE", "items_to_produce"),
        
        # Production loop (PC=2)
        ("LOAD", "items_to_produce"),
        ("PUSH", 1),
        ("SUB",),
        ("DUP",),
        ("STORE", "items_to_produce"),
        ("PUSH", -1),
        ("JUMP_IF", 27),  # Exit if items_to_produce <= 0
        
        # Wait for empty slot (semaphore acquire)
        ("PUSH", empty_slots),
        ("SEMAPHORE_ACQUIRE",),
        
        # Acquire buffer lock for mutual exclusion
        ("PUSH", buffer_lock),
        ("LOCK_ACQUIRE",),
        
        # Generate unique item ID
        ("PUSH", item_id_counter),
        ("ATOMIC_INCREMENT",),
        ("DUP",),
        ("PRINT", "Produced item {}"),
        
        # Send item to queue
        ("PUSH", buffer_queue),
        ("PUSH", buffer_queue),  # Dummy value for QUEUE_SEND (it needs 2 stack items)
        ("QUEUE_SEND",),
        
        # Release buffer lock
        ("PUSH", buffer_lock),
        ("LOCK_RELEASE",),
        
        # Signal filled slot (semaphore release)
        ("PUSH", filled_slots),
        ("SEMAPHORE_RELEASE",),
        
        ("JUMP", 2),
        
        ("PRINT", "Producer finished all items"),
    ]
    
    # Consumer instructions  
    consumer_instructions = [
        # Infinite consumption loop (PC=0)
        
        # Check if we've consumed all items
        ("PUSH", consumed_counter),
        ("ATOMIC_GET",),
        ("PUSH", TOTAL_ITEMS),
        ("SUB",),
        ("PUSH", -1),
        ("JUMP_IF", 26),  # Exit if consumed >= TOTAL_ITEMS
        
        # Wait for filled slot (semaphore acquire)
        ("PUSH", filled_slots),
        ("SEMAPHORE_ACQUIRE",),
        
        # Acquire buffer lock for mutual exclusion
        ("PUSH", buffer_lock),
        ("LOCK_ACQUIRE",),
        
        # Receive item from queue
        ("PUSH", buffer_queue),
        ("QUEUE_RECEIVE",),
        ("DUP",),
        ("PRINT", "Consumed item {}"),
        ("POP",),
        
        # Increment consumed counter
        ("PUSH", consumed_counter),
        ("ATOMIC_INCREMENT",),
        ("POP",),
        
        # Release buffer lock
        ("PUSH", buffer_lock),
        ("LOCK_RELEASE",),
        
        # Signal empty slot (semaphore release)
        ("PUSH", empty_slots),
        ("SEMAPHORE_RELEASE",),
        
        ("JUMP", 0),  # Continue loop
        
        ("PRINT", "Consumer finished - all items processed"),
    ]
    
    # Create threads
    vm.create_thread(producer_instructions, name="Producer-1")
    vm.create_thread(producer_instructions, name="Producer-2")
    vm.create_thread(consumer_instructions, name="Consumer-1")
    vm.create_thread(consumer_instructions, name="Consumer-2")
    vm.create_thread(consumer_instructions, name="Consumer-3")
    
    print("\nRunning producer-consumer with semaphore synchronisation...\n")
    vm.run(max_steps=5000)
    
    print("-" * 70)
    consumed = vm.atomic_counters["consumed_count"].get()
    print(f"Total items consumed: {consumed} (expected: {TOTAL_ITEMS})")
    print(f"Empty slots semaphore: {vm.semaphores['empty_sem'].count}")
    print(f"Filled slots semaphore: {vm.semaphores['filled_sem'].count}")
    print(f"Messages remaining in queue: {len(vm.message_queues['buffer_queue'].messages)}")
    
    if consumed == TOTAL_ITEMS:
        print("\n✓ SUCCESS: All items correctly produced and consumed!")
    else:
        print(f"\n✗ WARNING: Expected {TOTAL_ITEMS} items, got {consumed}")
    print()


def demo_multiple_buffers():
    """
    Demonstrate a pipeline with multiple bounded buffers.
    Stage 1: Producers → Buffer A → Processors
    Stage 2: Processors → Buffer B → Consumers
    """
    print("=" * 70)
    print("DEMONSTRATION 3: Multi-Stage Pipeline (Two Bounded Buffers)")
    print("=" * 70)
    print("Pipeline: Producer → [Buffer A] → Processor → [Buffer B] → Consumer")
    print("Expected: Items flow through both stages correctly")
    print("-" * 70)
    
    vm = ToyVM()
    vm.debug = False
    
    BUFFER_SIZE = 3
    ITEMS_TO_PROCESS = 10
    
    # Buffer A: Producer → Processor
    lock_a = vm.create_lock("lock_a")
    empty_a = vm.create_semaphore(BUFFER_SIZE, "empty_a")
    filled_a = vm.create_semaphore(0, "filled_a")
    queue_a = vm.create_message_queue("queue_a")
    
    # Buffer B: Processor → Consumer
    lock_b = vm.create_lock("lock_b")
    empty_b = vm.create_semaphore(BUFFER_SIZE, "empty_b")
    filled_b = vm.create_semaphore(0, "filled_b")
    queue_b = vm.create_message_queue("queue_b")
    
    # Counters
    item_counter = vm.create_atomic_counter(0, "item_id")
    processed_counter = vm.create_atomic_counter(0, "processed_count")
    consumed_counter = vm.create_atomic_counter(0, "final_consumed_count")
    
    # Producer: Generate items → Buffer A
    producer_instructions = [
        ("PUSH", ITEMS_TO_PROCESS),
        ("STORE", "items_left"),
        
        # Loop (PC=2)
        ("LOAD", "items_left"),
        ("PUSH", 1),
        ("SUB",),
        ("DUP",),
        ("STORE", "items_left"),
        ("PUSH", -1),
        ("JUMP_IF", 23),
        
        # Acquire empty slot in Buffer A
        ("PUSH", empty_a),
        ("SEMAPHORE_ACQUIRE",),
        
        ("PUSH", lock_a),
        ("LOCK_ACQUIRE",),
        
        # Create item
        ("PUSH", item_counter),
        ("ATOMIC_INCREMENT",),
        ("DUP",),
        ("PRINT", "Produced item {} → Buffer A"),
        ("PUSH", queue_a),
        ("PUSH", queue_a),  # Dummy for QUEUE_SEND
        ("QUEUE_SEND",),
        
        ("PUSH", lock_a),
        ("LOCK_RELEASE",),
        
        ("PUSH", filled_a),
        ("SEMAPHORE_RELEASE",),
        
        ("JUMP", 2),
        
        ("PRINT", "Producer done"),
    ]
    
    # Processor: Buffer A → Process → Buffer B
    processor_instructions = [
        # Check if all items processed (PC=0)
        ("PUSH", processed_counter),
        ("ATOMIC_GET",),
        ("PUSH", ITEMS_TO_PROCESS),
        ("SUB",),
        ("PUSH", -1),
        ("JUMP_IF", 34),
        
        # Get from Buffer A
        ("PUSH", filled_a),
        ("SEMAPHORE_ACQUIRE",),
        
        ("PUSH", lock_a),
        ("LOCK_ACQUIRE",),
        
        ("PUSH", queue_a),
        ("QUEUE_RECEIVE",),
        ("DUP",),
        ("STORE", "item"),
        ("PRINT", "Processing item {}..."),
        
        ("PUSH", lock_a),
        ("LOCK_RELEASE",),
        
        ("PUSH", empty_a),
        ("SEMAPHORE_RELEASE",),
        
        # Put into Buffer B
        ("PUSH", empty_b),
        ("SEMAPHORE_ACQUIRE",),
        
        ("PUSH", lock_b),
        ("LOCK_ACQUIRE",),
        
        ("LOAD", "item"),
        ("DUP",),
        ("PRINT", "Processed item {} → Buffer B"),
        ("PUSH", queue_b),
        ("PUSH", queue_b),  # Dummy for QUEUE_SEND
        ("QUEUE_SEND",),
        
        ("PUSH", processed_counter),
        ("ATOMIC_INCREMENT",),
        ("POP",),
        
        ("PUSH", lock_b),
        ("LOCK_RELEASE",),
        
        ("PUSH", filled_b),
        ("SEMAPHORE_RELEASE",),
        
        ("JUMP", 0),
        
        ("PRINT", "Processor done"),
    ]
    
    # Consumer: Buffer B → Final consumption
    consumer_instructions = [
        # Check if all items consumed (PC=0)
        ("PUSH", consumed_counter),
        ("ATOMIC_GET",),
        ("PUSH", ITEMS_TO_PROCESS),
        ("SUB",),
        ("PUSH", -1),
        ("JUMP_IF", 20),
        
        # Get from Buffer B
        ("PUSH", filled_b),
        ("SEMAPHORE_ACQUIRE",),
        
        ("PUSH", lock_b),
        ("LOCK_ACQUIRE",),
        
        ("PUSH", queue_b),
        ("QUEUE_RECEIVE",),
        ("DUP",),
        ("PRINT", "Consumed final item {}"),
        ("POP",),
        
        ("PUSH", consumed_counter),
        ("ATOMIC_INCREMENT",),
        ("POP",),
        
        ("PUSH", lock_b),
        ("LOCK_RELEASE",),
        
        ("PUSH", empty_b),
        ("SEMAPHORE_RELEASE",),
        
        ("JUMP", 0),
        
        ("PRINT", "Consumer done"),
    ]
    
    # Create threads
    vm.create_thread(producer_instructions, name="Producer")
    vm.create_thread(processor_instructions, name="Processor")
    vm.create_thread(consumer_instructions, name="Consumer")
    
    print("\nRunning multi-stage pipeline...\n")
    vm.run(max_steps=5000)
    
    print("-" * 70)
    processed = vm.atomic_counters["processed_count"].get()
    consumed = vm.atomic_counters["final_consumed_count"].get()
    print(f"Items processed (through Buffer A): {processed}")
    print(f"Items consumed (from Buffer B): {consumed}")
    print(f"Expected: {ITEMS_TO_PROCESS}")
    
    if processed == ITEMS_TO_PROCESS and consumed == ITEMS_TO_PROCESS:
        print("\n✓ SUCCESS: Pipeline processed all items correctly!")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "PRODUCER-CONSUMER PROBLEM WITH TOYVM" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Run all demonstrations
    demo_without_synchronisation()
    input("Press Enter to continue to next demonstration...\n")
    
    demo_with_semaphores()
    input("Press Enter to continue to final demonstration...\n")
    
    demo_multiple_buffers()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("1. NO synchronisation: Race conditions, data corruption")
    print("2. SEMAPHORES: Proper solution - safe and efficient")
    print("3. PIPELINE: Multiple stages with separate bounded buffers")
    print("=" * 70)
    print("\nSemaphores elegantly solve the producer-consumer problem by")
    print("combining mutual exclusion with condition synchronisation!")
    print()
