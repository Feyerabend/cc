import time
import random
from collections import deque
from typing import List, Dict, Any, Optional, Callable, Tuple
import uuid

class Thread:
    def __init__(self, vm, name: str, instructions: List[Tuple], start_pc: int = 0, priority: int = 0):
        self.vm = vm
        self.name = name
        self.instructions = instructions
        self.pc = start_pc
        self.stack = []
        self.variables = {}
        self.running = True
        self.waiting = False
        self.wait_condition: Optional[Callable[[], bool]] = None
        # Called when a blocking instruction's condition fires via the fallback wakeup
        # path in the run loop, to complete any deferred work (e.g. pop a resource name
        # left on the stack, decrement a semaphore count, deliver a queued message).
        self.wakeup_action: Optional[Callable[[], None]] = None
        self.joined_by = []
        self.priority = priority
        self.last_scheduled = time.time()

    def step(self):
        if not self.running or self.waiting:
            return False
        if self.pc >= len(self.instructions):
            self.running = False
            # Remove from the scheduler's active list immediately so it is not
            # selected as a candidate in future rounds.
            if self.name in self.vm.active_threads:
                self.vm.active_threads.remove(self.name)
            for thread_name in self.joined_by:
                thread = self.vm.threads.get(thread_name)
                if thread and thread.waiting:
                    thread.waiting = False
                    thread.wait_condition = None
                    if thread.wakeup_action:
                        thread.wakeup_action()
                        thread.wakeup_action = None
            return False
        if self.wait_condition and self.wait_condition():
            self.waiting = False
            self.wait_condition = None
        instruction = self.instructions[self.pc]
        opcode = instruction[0]
        args = instruction[1:] if len(instruction) > 1 else []
        self.vm.execute_instruction(self, opcode, args)
        self.pc += 1
        self.last_scheduled = time.time()
        return True

class Lock:
    def __init__(self, name: str):
        self.name = name
        self.locked = False
        self.owner = None
        self.waiting_threads = deque()

    def acquire(self, thread_name: str) -> bool:
        if not self.locked:
            self.locked = True
            self.owner = thread_name
            return True
        self.waiting_threads.append(thread_name)
        return False

    def release(self, thread_name: str) -> Tuple[bool, Optional[str]]:
        if self.locked and self.owner == thread_name:
            if self.waiting_threads:
                next_thread = self.waiting_threads.popleft()
                self.owner = next_thread
                return (True, next_thread)
            else:
                self.locked = False
                self.owner = None
                return (True, None)
        return (False, None)

class Semaphore:
    def __init__(self, name: str, count: int):
        self.name = name
        self.count = count
        self.waiting_threads = deque()

    def acquire(self, thread_name: str) -> bool:
        if self.count > 0:
            self.count -= 1
            return True
        self.waiting_threads.append(thread_name)
        return False

    def release(self) -> Optional[str]:
        if self.waiting_threads:
            next_thread = self.waiting_threads.popleft()
            return next_thread
        self.count += 1
        return None

class MessageQueue:
    def __init__(self, name: str):
        self.name = name
        self.messages = deque()
        self.waiting_receivers = deque()

    def send(self, message: Any) -> Optional[Tuple[str, Any]]:
        if self.waiting_receivers:
            receiver = self.waiting_receivers.popleft()
            return (receiver, message)
        self.messages.append(message)
        return None

    def receive(self, thread_name: str) -> Tuple[bool, Any]:
        if self.messages:
            return (True, self.messages.popleft())
        return (False, None)

class AtomicCounter:
    def __init__(self, name: str, initial_value: int = 0):
        self.name = name
        self.value = initial_value

    def increment(self) -> int:
        self.value += 1
        return self.value

    def decrement(self) -> int:
        self.value -= 1
        return self.value

    def get(self) -> int:
        return self.value

class ToyVM:
    def __init__(self):
        self.threads: Dict[str, Thread] = {}
        self.locks: Dict[str, Lock] = {}
        self.semaphores: Dict[str, Semaphore] = {}
        self.message_queues: Dict[str, MessageQueue] = {}
        self.atomic_counters: Dict[str, AtomicCounter] = {}
        self.globals = {}
        self.next_thread_id = 0
        self.running = False
        self.scheduler_type = "round_robin"
        self.step_interval = 0.01
        self.active_threads = deque()
        self.debug = False

    def create_thread(self, instructions: List[Tuple], name: str = None, priority: int = 0) -> str:
        if name is None:
            name = f"thread-{self.next_thread_id}"
            self.next_thread_id += 1
        thread = Thread(self, name, instructions, priority=priority)
        self.threads[name] = thread
        self.active_threads.append(name)
        if self.debug:
            print(f"[DEBUG] Created thread {name}")
        return name

    def create_lock(self, name: str = None) -> str:
        if name is None:
            name = f"lock-{len(self.locks)}"
        lock = Lock(name)
        self.locks[name] = lock
        return name

    def create_semaphore(self, count: int, name: str = None) -> str:
        if name is None:
            name = f"semaphore-{len(self.semaphores)}"
        semaphore = Semaphore(name, count)
        self.semaphores[name] = semaphore
        return name

    def create_message_queue(self, name: str = None) -> str:
        if name is None:
            name = f"queue-{len(self.message_queues)}"
        queue = MessageQueue(name)
        self.message_queues[name] = queue
        return name

    def create_atomic_counter(self, initial_value: int = 0, name: str = None) -> str:
        if name is None:
            name = f"counter-{len(self.atomic_counters)}"
        counter = AtomicCounter(name, initial_value)
        self.atomic_counters[name] = counter
        return name

    def detect_deadlock(self) -> bool:
        if not self.threads:
            return False
        all_waiting = all(t.waiting or not t.running for t in self.threads.values())
        if all_waiting:
            for thread in self.threads.values():
                if thread.waiting and thread.wait_condition and thread.wait_condition():
                    return False
            return True
        return False

    def get_thread_state(self, thread: Thread) -> str:
        if not thread.running:
            return "terminated"
        if thread.waiting:
            if thread.wait_condition:
                try:
                    can_proceed = thread.wait_condition()
                    return f"waiting (condition: {can_proceed})"
                except:
                    return "waiting (condition error)"
            return "waiting"
        return "runnable"

    def run(self, max_steps: int = 20000, debug: bool = False):
        self.running = True
        self.debug = debug
        step_count = 0
        while self.running and step_count < max_steps:
            step_count += 1
            runnable_threads = [t for t in self.active_threads if self.threads[t].running and not self.threads[t].waiting]
            if not runnable_threads:
                for t in self.active_threads:
                    thread = self.threads[t]
                    if thread.waiting and thread.wait_condition and thread.wait_condition():
                        runnable_threads.append(t)
                        thread.waiting = False
                        thread.wait_condition = None
                        if thread.wakeup_action:
                            thread.wakeup_action()
                            thread.wakeup_action = None
            if not runnable_threads:
                break
            if self.detect_deadlock():
                if debug:
                    print("Deadlock detected!")
                    self.print_thread_states(debug)
                self.running = False
                break
            thread_name = self.select_thread(runnable_threads)
            thread = self.threads[thread_name]
            if debug:
                print(f"Step {step_count}: Running thread {thread_name} (priority {thread.priority}) at PC {thread.pc}")
                if thread.pc < len(thread.instructions):
                    print(f"  Instruction: {thread.instructions[thread.pc]}")
                print(f"  Stack: {thread.stack}")
                print(f"  Variables: {thread.variables}")
                print(f"  State: {self.get_thread_state(thread)}")
            thread.step()
            time.sleep(self.step_interval)
        self.running = False
        if debug:
            if step_count >= max_steps:
                print(f"Stopped after {max_steps} steps - possible incomplete execution")
                self.print_thread_states(debug)
            else:
                print(f"All threads completed after {step_count} steps")
        return step_count

    def select_thread(self, active_threads: List[str]) -> str:
        if not active_threads:
            return None
        if self.scheduler_type == "priority":
            candidates = [
                (t, self.threads[t].priority, -self.threads[t].last_scheduled)
                for t in active_threads
            ]
            selected = max(candidates, key=lambda x: (x[1], x[2]))[0]
        elif self.scheduler_type == "round_robin":
            # Walk self.active_threads in order and pick the first thread that
            # appears in the runnable set, advancing the deque past it so the
            # next call starts from the following thread.
            runnable_set = set(active_threads)
            selected = active_threads[0]  # fallback
            for _ in range(len(self.active_threads)):
                candidate = self.active_threads[0]
                self.active_threads.rotate(-1)
                if candidate in runnable_set:
                    selected = candidate
                    break
        else:
            selected = random.choice(active_threads)
        if selected and self.debug:
            print(f"[DEBUG] Selected thread {selected}")
        return selected

    def print_thread_states(self, debug: bool):
        if not debug:
            return
        print("\nThread States:")
        for name, thread in self.threads.items():
            state = self.get_thread_state(thread)
            print(f"  {name}: {state}, PC: {thread.pc}, Stack: {thread.stack}")
            if thread.waiting and thread.wait_condition:
                print(f"    Waiting on condition: {thread.wait_condition.__name__ if hasattr(thread.wait_condition, '__name__') else 'anonymous'}")

    def execute_instruction(self, thread: Thread, opcode: str, args: List[Any]):
        if opcode == "PUSH":
            thread.stack.append(args[0])
        elif opcode == "POP":
            if thread.stack:
                thread.stack.pop()
        elif opcode == "DUP":
            if thread.stack:
                thread.stack.append(thread.stack[-1])
        elif opcode == "ADD":
            if len(thread.stack) >= 2:
                b = thread.stack.pop()
                a = thread.stack.pop()
                thread.stack.append(a + b)
            else:
                print(f"[{thread.name}] Warning: ADD with fewer than 2 values on stack")
        elif opcode == "SUB":
            if len(thread.stack) >= 2:
                b = thread.stack.pop()
                a = thread.stack.pop()
                thread.stack.append(a - b)
            else:
                print(f"[{thread.name}] Warning: SUB with fewer than 2 values on stack")
        elif opcode == "MUL":
            if len(thread.stack) >= 2:
                b = thread.stack.pop()
                a = thread.stack.pop()
                if args and args[0] == "mod":
                    thread.stack.append(a % b)
                else:
                    thread.stack.append(a * b)
            else:
                print(f"[{thread.name}] Warning: MUL with fewer than 2 values on stack")
        elif opcode == "DIV":
            if len(thread.stack) >= 2:
                # Peek before popping so the stack stays consistent on error.
                b = thread.stack[-1]
                a = thread.stack[-2]
                if b != 0:
                    thread.stack.pop()
                    thread.stack.pop()
                    thread.stack.append(a // b)
                else:
                    thread.stack.pop()
                    thread.stack.pop()
                    thread.stack.append(0)
                    print(f"[{thread.name}] Warning: DIV by zero, result set to 0")
            else:
                print(f"[{thread.name}] Warning: DIV with fewer than 2 values on stack")
        elif opcode == "LOAD":
            var_name = args[0]
            if var_name in thread.variables:
                thread.stack.append(thread.variables[var_name])
            elif var_name in self.globals:
                thread.stack.append(self.globals[var_name])
            else:
                print(f"[{thread.name}] Warning: LOAD of undefined variable '{var_name}'")
        elif opcode == "STORE":
            var_name = args[0]
            if thread.stack:
                thread.variables[var_name] = thread.stack.pop()
        elif opcode == "GLOBAL_STORE":
            var_name = args[0]
            if thread.stack:
                self.globals[var_name] = thread.stack.pop()
        elif opcode == "JUMP":
            target = args[0]
            # Allow target == len(instructions): pc advances to len on next step,
            # which terminates the thread — the canonical way to "exit a loop".
            if 0 <= target <= len(thread.instructions):
                thread.pc = target - 1
            else:
                print(f"[{thread.name}] Warning: JUMP to invalid address {target}")
        elif opcode == "JUMP_IF":
            if not thread.stack:
                print(f"[{thread.name}] Warning: JUMP_IF with empty stack, skipping jump")
                return
            condition = thread.stack.pop()
            if condition >= 0:
                target = args[0]
                if 0 <= target <= len(thread.instructions):
                    thread.pc = target - 1
                else:
                    print(f"[{thread.name}] Warning: JUMP_IF to invalid address {target}")
        elif opcode == "PRINT":
            if args:
                message = args[0]
                if thread.stack and "{}" in message:
                    value = thread.stack[-1]
                    message = message.replace("{}", str(value))
                print(f"[{thread.name}] {message}")
            elif thread.stack:
                print(f"[{thread.name}] {thread.stack[-1]}")
        elif opcode == "THREAD_CREATE":
            if len(thread.stack) >= 1:
                instructions_index = thread.stack.pop()
                new_thread_instructions = args[0][instructions_index]
                new_thread_name = self.create_thread(new_thread_instructions, priority=thread.priority + 1)
                thread.stack.append(new_thread_name)
        elif opcode == "THREAD_JOIN":
            if thread.stack:
                other_thread_name = thread.stack.pop()
                other_thread = self.threads.get(other_thread_name)
                if other_thread and other_thread.running:
                    other_thread.joined_by.append(thread.name)
                    thread.waiting = True
                    thread.wait_condition = lambda: not other_thread.running
        elif opcode == "LOCK_CREATE":
            lock_name = self.create_lock()
            thread.stack.append(lock_name)
        elif opcode == "LOCK_ACQUIRE":
            if thread.stack:
                lock_name = thread.stack[-1]
                lock = self.locks.get(lock_name)
                if lock:
                    if lock.acquire(thread.name):
                        thread.stack.pop()
                    else:
                        thread.waiting = True
                        thread.wait_condition = lambda: lock.owner == thread.name
                        # When woken via the fallback path the lock_name is still
                        # on the stack (it was peeked, not popped).  The wakeup
                        # action removes it so the thread resumes with a clean stack.
                        thread.wakeup_action = lambda: thread.stack.pop() if thread.stack else None
        elif opcode == "LOCK_RELEASE":
            if thread.stack:
                lock_name = thread.stack.pop()
                lock = self.locks.get(lock_name)
                if lock:
                    result, next_thread = lock.release(thread.name)
                    if result and next_thread:
                        next_thread_obj = self.threads.get(next_thread)
                        if next_thread_obj:
                            next_thread_obj.waiting = False
                            next_thread_obj.wait_condition = None
                            # The woken thread left lock_name on its stack when it
                            # blocked; pop it now so it resumes with a clean stack.
                            if next_thread_obj.stack:
                                next_thread_obj.stack.pop()
                            next_thread_obj.wakeup_action = None
        elif opcode == "SEMAPHORE_CREATE":
            if thread.stack:
                count = thread.stack.pop()
                sem_name = self.create_semaphore(count)
                thread.stack.append(sem_name)
        elif opcode == "SEMAPHORE_ACQUIRE":
            if thread.stack:
                sem_name = thread.stack[-1]
                sem = self.semaphores.get(sem_name)
                if sem:
                    if sem.acquire(thread.name):
                        thread.stack.pop()
                    else:
                        thread.waiting = True
                        # Only wake via condition if there is genuinely available
                        # capacity (not because the thread is still in the waiting
                        # queue, which was the previous always-True bug).
                        thread.wait_condition = lambda: sem.count > 0
                        # Fallback wakeup: pop sem_name from the stack and claim
                        # the permit that triggered the condition.
                        def _sem_wakeup(t=thread, s=sem):
                            if t.stack:
                                t.stack.pop()
                            if s.count > 0:
                                s.count -= 1
                            try:
                                s.waiting_threads.remove(t.name)
                            except ValueError:
                                pass
                        thread.wakeup_action = _sem_wakeup
        elif opcode == "SEMAPHORE_RELEASE":
            if thread.stack:
                sem_name = thread.stack.pop()
                sem = self.semaphores.get(sem_name)
                if sem:
                    next_thread = sem.release()
                    if next_thread:
                        next_thread_obj = self.threads.get(next_thread)
                        if next_thread_obj:
                            next_thread_obj.waiting = False
                            next_thread_obj.wait_condition = None
                            # The woken thread left sem_name on its stack; pop it.
                            if next_thread_obj.stack:
                                next_thread_obj.stack.pop()
                            next_thread_obj.wakeup_action = None
        elif opcode == "QUEUE_CREATE":
            queue_name = self.create_message_queue()
            thread.stack.append(queue_name)
        elif opcode == "QUEUE_SEND":
            if len(thread.stack) >= 2:
                message = thread.stack.pop()
                queue_name = thread.stack.pop()
                queue = self.message_queues.get(queue_name)
                if queue:
                    result = queue.send(message)
                    if result:
                        receiver_name, msg = result
                        receiver = self.threads.get(receiver_name)
                        if receiver:
                            receiver.waiting = False
                            receiver.wait_condition = None
                            receiver.wakeup_action = None
                            # The receiver peeked at queue_name (did not pop it)
                            # before blocking.  Replace that stale value with the
                            # delivered message so the receiver's stack matches the
                            # successful non-blocking path.
                            if receiver.stack:
                                receiver.stack[-1] = msg
                            else:
                                receiver.stack.append(msg)
        elif opcode == "QUEUE_RECEIVE":
            if thread.stack:
                queue_name = thread.stack[-1]
                queue = self.message_queues.get(queue_name)
                if queue:
                    success, message = queue.receive(thread.name)
                    if success:
                        thread.stack.pop()
                        thread.stack.append(message)
                    else:
                        queue.waiting_receivers.append(thread.name)
                        thread.waiting = True
                        # Only wake when a message is actually in the queue.
                        # The previous condition also checked
                        # `thread.name in queue.waiting_receivers`, which was
                        # always True immediately after adding the thread, causing
                        # an immediate spurious wakeup with no message delivered.
                        thread.wait_condition = lambda: bool(queue.messages)
                        # Fallback wakeup: receive the message and replace the
                        # queue_name that was peeked and left on the stack.
                        def _queue_wakeup(t=thread, q=queue):
                            if q.messages and t.stack:
                                msg = q.messages.popleft()
                                t.stack[-1] = msg
                            try:
                                q.waiting_receivers.remove(t.name)
                            except ValueError:
                                pass
                        thread.wakeup_action = _queue_wakeup
        elif opcode == "ATOMIC_CREATE":
            if thread.stack:
                initial_value = thread.stack.pop()
                counter_name = self.create_atomic_counter(initial_value)
                thread.stack.append(counter_name)
        elif opcode == "ATOMIC_INCREMENT":
            if thread.stack:
                counter_name = thread.stack.pop()
                counter = self.atomic_counters.get(counter_name)
                if counter:
                    thread.stack.append(counter.increment())
        elif opcode == "ATOMIC_DECREMENT":
            if thread.stack:
                counter_name = thread.stack.pop()
                counter = self.atomic_counters.get(counter_name)
                if counter:
                    thread.stack.append(counter.decrement())
        elif opcode == "ATOMIC_GET":
            if thread.stack:
                counter_name = thread.stack.pop()
                counter = self.atomic_counters.get(counter_name)
                if counter:
                    thread.stack.append(counter.get())
        elif opcode == "SLEEP":
            if thread.stack:
                duration = thread.stack.pop()
                time.sleep(duration / 1000)
        elif opcode == "NOP":
            pass
        else:
            print(f"[{thread.name}] Unknown opcode: {opcode}")
