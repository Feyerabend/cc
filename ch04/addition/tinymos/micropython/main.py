# TinyMOS
# RPI Pico

import time
import gc

class ProcessState:
    READY = 0
    RUNNING = 1
    BLOCKED = 2
    TERMINATED = 3

class Priority:
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class ProcessControlBlock:    
    def __init__(self, pid, name, function, priority=Priority.NORMAL):
        self.pid = pid
        self.name = name
        self.function = function
        self.priority = priority
        self.state = ProcessState.READY
        
        # Process statistics
        self.created_at = time.ticks_ms()
        self.cpu_time = 0
        self.context_switches = 0
        self.last_run = 0
        
        # Process context (generator state)
        self.context = None
        
        # I/O blocking
        self.blocked_until = 0
        self.blocked_reason = None
        
        # Inter-process communication (simple list instead of deque)
        self.messages = []
        
    def __repr__(self):
        states = ["READY", "RUNNING", "BLOCKED", "TERMINATED"]
        return "PCB(pid={}, name={}, state={})".format(
            self.pid, self.name, states[self.state])

# System call classes
class SystemCall:
    pass

class Yield(SystemCall):
    def __init__(self, reason="voluntary"):
        self.reason = reason

class Sleep(SystemCall):
    def __init__(self, duration_ms):
        self.duration_ms = duration_ms

class WaitForMessage(SystemCall):
    pass

class SendMessage(SystemCall):
    def __init__(self, target_pid, message):
        self.target_pid = target_pid
        self.message = message

class Exit(SystemCall):
    def __init__(self, exit_code=0):
        self.exit_code = exit_code

class IOOperation(SystemCall):
    def __init__(self, operation, duration_ms):
        self.operation = operation
        self.duration_ms = duration_ms


class TinyMOS:    
    def __init__(self, time_slice_ms=100, debug=True):
        self.process_table = {}
        self.ready_queue = []
        self.blocked_processes = []
        
        self.current_process = None
        self.next_pid = 1
        self.time_slice_ms = time_slice_ms
        self.debug = debug
        self.running = False
        
        # Scheduler statistics
        self.total_context_switches = 0
        self.start_time = 0
        
        # Priority queues (lists of lists)
        self.priority_queues = [[], [], [], []]  # indexes 0-3 for priorities 1-4
        self.use_priority_scheduling = False
    
    def create_process(self, function, name, priority=Priority.NORMAL):
        pid = self.next_pid
        self.next_pid += 1
        
        pcb = ProcessControlBlock(pid, name, function, priority)
        self.process_table[pid] = pcb
        
        # Init the process context (generator)
        pcb.context = function()
        
        # Add to appropriate queue
        if self.use_priority_scheduling:
            self.priority_queues[priority - 1].append(pcb)
        else:
            self.ready_queue.append(pcb)
        
        if self.debug:
            priorities = ["", "LOW", "NORMAL", "HIGH", "CRITICAL"]
            print("Created process: {} (PID: {}, Priority: {})".format(
                name, pid, priorities[priority]))
        
        return pid

    # priority scheduling
    def enable_priority_scheduling(self):
        self.use_priority_scheduling = True
        # Move existing processes to priority queues
        while self.ready_queue:
            pcb = self.ready_queue.pop(0)
            self.priority_queues[pcb.priority - 1].append(pcb)
    
    def get_next_process(self):
        if self.use_priority_scheduling:
            # Priority scheduling - check highest priority first (index 3 = CRITICAL)
            for i in range(3, -1, -1):  # 3, 2, 1, 0
                if self.priority_queues[i]:
                    return self.priority_queues[i].pop(0)
            return None
        else:
            # Round-robin scheduling
            return self.ready_queue.pop(0) if self.ready_queue else None
    
    def add_to_ready_queue(self, pcb):
        if self.use_priority_scheduling:
            self.priority_queues[pcb.priority - 1].append(pcb)
        else:
            self.ready_queue.append(pcb)
    
    def context_switch(self, next_process):
        current_time = time.ticks_ms()
        
        # Save current process state
        if self.current_process:
            self.current_process.state = ProcessState.READY
            self.current_process.cpu_time += time.ticks_diff(current_time, self.current_process.last_run)
            self.current_process.context_switches += 1
        
        # Switch to next process
        self.current_process = next_process
        next_process.state = ProcessState.RUNNING
        next_process.last_run = current_time
        
        self.total_context_switches += 1
        
        if self.debug:
            print("Context switch to {} (PID: {})".format(next_process.name, next_process.pid))
    
    def handle_system_call(self, syscall):
        if not self.current_process:
            return
        
        pcb = self.current_process
        
        if isinstance(syscall, Yield):
            if self.debug:
                print("{}: yield ({})".format(pcb.name, syscall.reason))
            # Process voluntarily gives up CPU
            self.add_to_ready_queue(pcb)
        
        elif isinstance(syscall, Sleep):
            if self.debug:
                print("{}: sleep({}ms)".format(pcb.name, syscall.duration_ms))
            pcb.state = ProcessState.BLOCKED
            pcb.blocked_until = time.ticks_ms() + syscall.duration_ms
            pcb.blocked_reason = "sleep({}ms)".format(syscall.duration_ms)
            self.blocked_processes.append(pcb)
        
        elif isinstance(syscall, WaitForMessage):
            if pcb.messages:
                # Message available, don't block
                if self.debug:
                    print("{}: message available, continuing".format(pcb.name))
                self.add_to_ready_queue(pcb)
            else:
                if self.debug:
                    print("{}: waiting for message".format(pcb.name))
                pcb.state = ProcessState.BLOCKED
                pcb.blocked_reason = "waiting for message"
                self.blocked_processes.append(pcb)
        
        elif isinstance(syscall, SendMessage):
            target_pcb = self.process_table.get(syscall.target_pid)
            if target_pcb:
                target_pcb.messages.append(syscall.message)
                if self.debug:
                    print("{}: sent message to {}".format(pcb.name, target_pcb.name))
                
                # Wake up target if it was waiting for a message
                if (target_pcb.state == ProcessState.BLOCKED and 
                    target_pcb.blocked_reason == "waiting for message"):
                    self.unblock_process(target_pcb)
            
            self.add_to_ready_queue(pcb)
        
        elif isinstance(syscall, IOOperation):
            if self.debug:
                print("{}: I/O operation '{}' ({}ms)".format(
                    pcb.name, syscall.operation, syscall.duration_ms))
            pcb.state = ProcessState.BLOCKED
            pcb.blocked_until = time.ticks_ms() + syscall.duration_ms
            pcb.blocked_reason = "I/O: {}".format(syscall.operation)
            self.blocked_processes.append(pcb)
        
        elif isinstance(syscall, Exit):
            if self.debug:
                print("{}: exit({})".format(pcb.name, syscall.exit_code))
            pcb.state = ProcessState.TERMINATED
            del self.process_table[pcb.pid]
    
    def unblock_process(self, pcb):
        if pcb in self.blocked_processes:
            self.blocked_processes.remove(pcb)
        pcb.state = ProcessState.READY
        pcb.blocked_reason = None
        self.add_to_ready_queue(pcb)
        
        if self.debug:
            print("Unblocked process: {}".format(pcb.name))
    
    def check_blocked_processes(self):
        current_time = time.ticks_ms()
        to_unblock = []
        
        for pcb in self.blocked_processes:
            if (pcb.blocked_until > 0 and 
                time.ticks_diff(current_time, pcb.blocked_until) >= 0):
                to_unblock.append(pcb)
        
        for pcb in to_unblock:
            self.unblock_process(pcb)
    
    def print_process_table(self):
        print("\n=== Process Table ===")
        states = ["READY", "RUNNING", "BLOCKED", "TERMINATED"]
        priorities = ["", "LOW", "NORMAL", "HIGH", "CRITICAL"]
        
        for pcb in self.process_table.values():
            print("PID: {}, Name: {}, State: {}, Priority: {}, CPU: {}ms, Switches: {}".format(
                pcb.pid, pcb.name, states[pcb.state], priorities[pcb.priority],
                pcb.cpu_time, pcb.context_switches))
        
        if self.blocked_processes:
            print("Blocked processes: {}".format(len(self.blocked_processes)))
            for pcb in self.blocked_processes:
                print("  {}: {}".format(pcb.name, pcb.blocked_reason))
    
    def run(self, duration_ms=None):
        self.running = True
        self.start_time = time.ticks_ms()
        
        print("TinyMOS Starting...")
        sched_type = "Priority-based" if self.use_priority_scheduling else "Round-robin"
        print("Scheduler: {}".format(sched_type))
        print("Time slice: {}ms".format(self.time_slice_ms))
        
        end_time = self.start_time + duration_ms if duration_ms else None
        
        try:
            while self.running:
                if end_time and time.ticks_diff(time.ticks_ms(), end_time) >= 0:
                    break
                
                # Check for processes that can be unblocked
                self.check_blocked_processes()
                
                # Get next process to run
                next_process = self.get_next_process()
                
                if not next_process:
                    if not self.blocked_processes:
                        print("No processes left to run. Shutting down.")
                        break
                    else:
                        # All processes blocked, wait a bit
                        time.sleep_ms(10)
                        continue
                
                # Context switch
                self.context_switch(next_process)
                
                # Run the process for one time slice
                slice_start = time.ticks_ms()
                try:
                    # Execute process until it yields or time slice expires
                    syscall = next(next_process.context)
                    
                    # Handle system call
                    self.handle_system_call(syscall)
                    
                except StopIteration:
                    # Process finished normally
                    if self.debug:
                        print("{}: finished".format(next_process.name))
                    next_process.state = ProcessState.TERMINATED
                    del self.process_table[next_process.pid]
                
                except Exception as e:
                    # Process crashed
                    print("Process {} crashed: {}".format(next_process.name, str(e)))
                    next_process.state = ProcessState.TERMINATED
                    del self.process_table[next_process.pid]
                
                # Enforce time slice
                elapsed = time.ticks_diff(time.ticks_ms(), slice_start)
                if elapsed < self.time_slice_ms:
                    time.sleep_ms(self.time_slice_ms - elapsed)
                
                # Periodic garbage collection to manage memory
                if self.total_context_switches % 50 == 0:
                    gc.collect()
        
        except KeyboardInterrupt:
            print("Shutdown requested...")
        
        finally:
            self.running = False
            print("TinyMOS Shutdown")
            self.print_process_table()
            total_time = time.ticks_diff(time.ticks_ms(), self.start_time)
            print("System Statistics:")
            print("  Total context switches: {}".format(self.total_context_switches))
            print("  Running time: {}ms".format(total_time))

# System calls
class OS:
    current_os = None
    
    @staticmethod
    def yield_cpu(reason="voluntary"):
        return Yield(reason)
    
    @staticmethod
    def sleep(duration_ms):
        return Sleep(duration_ms)
    
    @staticmethod
    def wait_for_message():
        return WaitForMessage()
    
    @staticmethod
    def send_message(target_pid, message):
        return SendMessage(target_pid, message)
    
    @staticmethod
    def exit(exit_code=0):
        return Exit(exit_code)
    
    @staticmethod
    def do_io(operation, duration_ms):
        return IOOperation(operation, duration_ms)
    
    @staticmethod
    def get_message():
        if OS.current_os and OS.current_os.current_process:
            pcb = OS.current_os.current_process
            if pcb.messages:
                return pcb.messages.pop(0)
        return None


# Example processes

def counter_process():
    count = 0
    while count < 10:
        print("Counter: {}".format(count))
        count += 1
        yield OS.yield_cpu("counting")
    yield OS.exit()

def blinker_process():
    try:
        from machine import Pin
        led = Pin(25, Pin.OUT)  # Pico built-in LED
        has_led = True
    except:
        has_led = False
        
    for i in range(5):
        if has_led:
            led.on()
            print("LED ON")
        else:
            print("Blink ON (no LED)")
        yield OS.sleep(500)  # 500ms
        
        if has_led:
            led.off()
            print("LED OFF")
        else:
            print("Blink OFF (no LED)")
        yield OS.sleep(500)
        yield OS.yield_cpu("blinking")
    
    yield OS.exit()

def temperature_reader():
    try:
        from machine import ADC
        sensor = ADC(4)  # Pico internal temperature sensor
        has_sensor = True
    except:
        has_sensor = False
        sensor = None
    
    for i in range(5):
        if has_sensor:
            # Convert ADC reading to temperature (Pico specific)
            reading = sensor.read_u16() * 3.3 / 65535
            temperature = 27 - (reading - 0.706) / 0.001721
            print("Temperature: {:.1f}C".format(temperature))
        else:
            # Simulate temperature
            temp = 20.0 + (time.ticks_ms() % 10000) / 1000
            print("Simulated temp: {:.1f}C".format(temp))
        
        yield OS.sleep(2000)  # Read every 2 seconds
        yield OS.yield_cpu("temperature reading")
    
    yield OS.exit()

def producer_process():
    consumer_pid = 2  # Assume consumer has PID 2
    
    for i in range(5):
        message = "data_{}".format(i)
        print("Producer: sending {}".format(message))
        yield OS.send_message(consumer_pid, message)
        yield OS.sleep(800)  # Produce every 800ms
    
    # Send termination signal
    yield OS.send_message(consumer_pid, "STOP")
    yield OS.exit()

def consumer_process():
    while True:
        print("Consumer: waiting for message...")
        yield OS.wait_for_message()
        
        message = OS.get_message()
        if message == "STOP":
            print("Consumer: received stop signal")
            break
        
        print("Consumer: processing {}".format(message))
        yield OS.sleep(300)  # Process for 300ms
    
    yield OS.exit()

def high_priority_process():
    for i in range(3):
        print("HIGH PRIORITY: Critical task {}".format(i))
        yield OS.sleep(200)
        yield OS.yield_cpu("high priority work")
    yield OS.exit()


# Demos

def demo_basic_multitasking():
    print("--- Basic Multitasking Demo ---")

    os_instance = TinyMOS(time_slice_ms=200, debug=True)
    OS.current_os = os_instance
    
    # Create processes
    os_instance.create_process(counter_process, "Counter")
    os_instance.create_process(blinker_process, "Blinker")
    os_instance.create_process(temperature_reader, "TempReader")
    
    # Run for 15 seconds
    os_instance.run(duration_ms=15000)

def demo_producer_consumer():
    print("\n--- Producer-Consumer Demo ---")

    os_instance = TinyMOS(time_slice_ms=100, debug=True)
    OS.current_os = os_instance
    
    # Create producer and consumer
    os_instance.create_process(producer_process, "Producer")
    os_instance.create_process(consumer_process, "Consumer")
    
    # Run for 10 seconds
    os_instance.run(duration_ms=10000)

def demo_priority_scheduling():
    print("\n--- Priority Scheduling Demo ---")
    
    os_instance = TinyMOS(time_slice_ms=100, debug=True)
    os_instance.enable_priority_scheduling()
    OS.current_os = os_instance
    
    # Create processes with different priorities
    os_instance.create_process(counter_process, "LowPrio", Priority.LOW)
    os_instance.create_process(blinker_process, "NormalPrio", Priority.NORMAL)
    os_instance.create_process(high_priority_process, "HighPrio", Priority.HIGH)
    
    # Run for 8 seconds
    os_instance.run(duration_ms=8000)

# Main execution
if __name__ == "__main__":
    print("TinyMOS for MicroPython")
    print("-----------------------")
    
    # Run demos
    demo_basic_multitasking()
    
    print("\nPress Ctrl+C to stop between demos")
    time.sleep(2)
    
    demo_producer_consumer()
    
    time.sleep(2)
    
    demo_priority_scheduling()
    
    print("All demos completed!")
