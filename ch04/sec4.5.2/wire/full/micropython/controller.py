from machine import Pin, UART
import time
import _thread
from collections import deque
import gc

class UARTController:
    def __init__(self, uart_id=1, baudrate=9600, tx_pin=4, rx_pin=5):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        
        # Buffers
        self.rx_buffer = deque((), 50)
        self.tx_buffer = deque((), 50)
        
        # Control flags
        self.running = True
        self.rx_lock = False
        self.tx_lock = False
        
        # Thread management - track actual status
        self.rx_thread_id = None
        self.tx_thread_id = None
        self.threads_started = False
        self.rx_thread_running = False
        self.tx_thread_running = False
        
        # Command history
        self.command_history = []
        
        # Debug flag
        self.debug = True
    
    def log(self, message):
        if self.debug:
            print(f"[{time.time():.3f}] {message}")
    
    def format_message(self, message):
        return f"#{message}*"
    
    def parse_message(self, raw_message):
        if raw_message.startswith('#') and raw_message.endswith('*'):
            return raw_message[1:-1]
        return None
    
    def safe_buffer_add(self, buffer, item, lock_name):
        """Thread-safe buffer addition with better error handling"""
        retry_count = 0
        lock_attr = getattr(self, lock_name)
        
        while lock_attr and retry_count < 50:  # Reduced timeout
            time.sleep(0.002)  # Slightly longer sleep
            retry_count += 1
            lock_attr = getattr(self, lock_name)
        
        if retry_count >= 50:
            self.log(f"Warning: Timeout acquiring {lock_name}")
            return False
        
        try:
            setattr(self, lock_name, True)
            
            if len(buffer) >= 50:
                buffer.popleft()
            buffer.append(item)
            
            setattr(self, lock_name, False)
            return True
            
        except Exception as e:
            self.log(f"Error in safe_buffer_add: {e}")
            setattr(self, lock_name, False)
            return False
    
    def safe_buffer_get(self, buffer, lock_name):
        """Thread-safe buffer retrieval"""
        retry_count = 0
        lock_attr = getattr(self, lock_name)
        
        while lock_attr and retry_count < 50:
            time.sleep(0.002)
            retry_count += 1
            lock_attr = getattr(self, lock_name)
        
        if retry_count >= 50:
            return None
        
        try:
            setattr(self, lock_name, True)
            
            result = None
            if buffer:
                result = buffer.popleft()
            
            setattr(self, lock_name, False)
            return result
            
        except Exception as e:
            self.log(f"Error in safe_buffer_get: {e}")
            setattr(self, lock_name, False)
            return None
    
    def rx_thread(self):
        self.log("RX Thread starting...")
        self.rx_thread_running = True
        buffer = ""
        error_count = 0
        max_errors = 10
        
        try:
            while self.running and error_count < max_errors:
                try:
                    if self.uart.any():
                        data = self.uart.read()
                        if data:
                            try:
                                new_data = data.decode('utf-8', 'ignore')
                                buffer += new_data
                            except Exception as e:
                                self.log(f"RX decode error: {e}")
                                error_count += 1
                                continue
                            
                            # Process complete messages
                            while '#' in buffer and '*' in buffer:
                                start_idx = buffer.find('#')
                                end_idx = buffer.find('*', start_idx)
                                
                                if start_idx != -1 and end_idx != -1:
                                    raw_message = buffer[start_idx:end_idx+1]
                                    message = self.parse_message(raw_message)
                                    
                                    if message:
                                        success = self.safe_buffer_add(
                                            self.rx_buffer, 
                                            (message, time.time()), 
                                            'rx_lock'
                                        )
                                        if success:
                                            self.log(f"RX buffered: {message}")
                                    
                                    buffer = buffer[end_idx+1:]
                                else:
                                    break
                    
                    time.sleep(0.01)
                    
                except Exception as e:
                    self.log(f"RX Thread error: {e}")
                    error_count += 1
                    time.sleep(0.1)
        
        except Exception as e:
            self.log(f"RX Thread fatal error: {e}")
        
        finally:
            self.rx_thread_running = False
            self.log("RX Thread stopped")
    
    def tx_thread(self):
        self.log("TX Thread starting...")
        self.tx_thread_running = True
        error_count = 0
        max_errors = 10
        
        try:
            while self.running and error_count < max_errors:
                try:
                    message_to_send = self.safe_buffer_get(self.tx_buffer, 'tx_lock')
                    
                    if message_to_send:
                        try:
                            formatted = self.format_message(message_to_send)
                            self.uart.write(formatted.encode('utf-8'))
                            self.log(f"TX sent: {message_to_send}")
                            
                            # Add to history
                            if len(self.command_history) >= 20:
                                self.command_history.pop(0)
                            self.command_history.append((message_to_send, time.time()))
                            
                        except Exception as e:
                            self.log(f"TX send error: {e}")
                            error_count += 1
                    
                    time.sleep(0.01)
                    
                except Exception as e:
                    self.log(f"TX Thread error: {e}")
                    error_count += 1
                    time.sleep(0.1)
        
        except Exception as e:
            self.log(f"TX Thread fatal error: {e}")
        
        finally:
            self.tx_thread_running = False
            self.log("TX Thread stopped")
    
    def start_threads(self):
        """Start RX and TX threads with better error handling"""
        if self.threads_started:
            self.log("Threads already started")
            return True
        
        try:
            self.log("Starting controller threads...")
            
            # Reset flags
            self.running = True
            self.rx_thread_running = False
            self.tx_thread_running = False
            
            # Force garbage collection before starting threads
            gc.collect()
            
            # Start RX thread
            self.log("Starting RX thread...")
            self.rx_thread_id = _thread.start_new_thread(self.rx_thread, ())
            time.sleep(0.2)  # Longer delay between thread starts
            
            # Check if RX thread actually started
            start_time = time.time()
            while not self.rx_thread_running and (time.time() - start_time) < 2.0:
                time.sleep(0.1)
            
            if not self.rx_thread_running:
                self.log("RX thread failed to start!")
                return False
            
            # Start TX thread
            self.log("Starting TX thread...")
            self.tx_thread_id = _thread.start_new_thread(self.tx_thread, ())
            time.sleep(0.2)
            
            # Check if TX thread actually started
            start_time = time.time()
            while not self.tx_thread_running and (time.time() - start_time) < 2.0:
                time.sleep(0.1)
            
            if not self.tx_thread_running:
                self.log("TX thread failed to start!")
                self.running = False  # Stop RX thread
                return False
            
            self.threads_started = True
            self.log("Controller threads started successfully!")
            return True
            
        except OSError as e:
            error_msg = str(e).lower()
            if "core1 in use" in error_msg or "core" in error_msg:
                self.log("Error: Core1 is already in use!")
                self.log("Solutions:")
                self.log("   1. Soft reset: Press Ctrl+D")
                self.log("   2. Hard reset: machine.reset()")
                self.log("   3. Use single-threaded mode")
                return False
            else:
                self.log(f"Thread start OSError: {e}")
                return False
        except Exception as e:
            self.log(f"Unexpected error starting threads: {e}")
            return False
    
    def send_command(self, command):
        message = f"CMD:{command}"
        success = self.safe_buffer_add(self.tx_buffer, message, 'tx_lock')
        if not success:
            self.log(f"Failed to queue command: {command}")
    
    def send_request(self, request):
        message = f"REQ:{request}"
        success = self.safe_buffer_add(self.tx_buffer, message, 'tx_lock')
        if not success:
            self.log(f"Failed to queue request: {request}")
    
    def get_received_messages(self):
        """Get all pending received messages"""
        messages = []
        
        # Get all available messages
        while True:
            message = self.safe_buffer_get(self.rx_buffer, 'rx_lock')
            if message is None:
                break
            messages.append(message)
        
        return messages
    
    def display_messages(self):
        messages = self.get_received_messages()
        for message, timestamp in messages:
            try:
                local_time = time.localtime(timestamp)
                time_str = f"{local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d}"
                print(f"[{time_str}] Received: {message}")
            except:
                print(f"Received: {message}")
    
    def get_status(self):
        """Get current status of threads and buffers"""
        rx_count = len(self.rx_buffer)
        tx_count = len(self.tx_buffer)
        
        print(f"\nController Status:")
        print(f"  Running: {self.running}")
        print(f"  Threads Started: {self.threads_started}")
        print(f"  RX Thread Running: {self.rx_thread_running}")
        print(f"  TX Thread Running: {self.tx_thread_running}")
        print(f"  RX Buffer: {rx_count}/50")
        print(f"  TX Buffer: {tx_count}/50")
        print(f"  Commands in History: {len(self.command_history)}")
    
    def interactive_mode(self):
        print("\n-- UART Controller --")
        print("Commands:")
        print("  STATUS    - Get device status")
        print("  PING      - Ping device")
        print("  LED_ON    - Turn LED on")
        print("  LED_OFF   - Turn LED off")
        print("  TEMP      - Request temperature")
        print("  HISTORY   - Show command history")
        print("  MESSAGES  - Show recent messages")
        print("  INFO      - Show controller status")
        print("  QUIT      - Exit")
        print("------------------------")
        
        while self.running:
            try:
                # Display any new messages
                self.display_messages()
                
                # Get user input
                cmd = input("Enter command: ").strip().upper()
                
                if cmd == "QUIT":
                    break
                elif cmd == "STATUS":
                    self.send_command("STATUS")
                elif cmd == "PING":
                    self.send_command("PING")
                elif cmd == "LED_ON":
                    self.send_command("LED_ON")
                elif cmd == "LED_OFF":
                    self.send_command("LED_OFF")
                elif cmd == "TEMP":
                    self.send_request("TEMP")
                elif cmd == "INFO":
                    self.get_status()
                elif cmd == "HISTORY":
                    print("\nCommand History:")
                    for i, (command, timestamp) in enumerate(self.command_history[-10:]):
                        try:
                            local_time = time.localtime(timestamp)
                            time_str = f"{local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d}"
                            print(f"  {i+1}. [{time_str}] {command}")
                        except:
                            print(f"  {i+1}. {command}")
                elif cmd == "MESSAGES":
                    print("Recent messages displayed above")
                elif cmd == "":
                    continue
                else:
                    print(f"Unknown command: {cmd}")
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def start(self):
        print("UART Controller Starting...")
        print("TX=GP4, RX=GP5")
        
        # Try to start threads
        if not self.start_threads():
            print("Failed to start threads. Exiting...")
            return False
        
        time.sleep(1)  # Let threads stabilize
        
        try:
            self.interactive_mode()
        finally:
            self.stop()
        
        return True
    
    def monitor_mode(self):
        print("Monitor Mode - Press Ctrl+C to exit")
        print("Listening for messages...")
        
        try:
            while self.running:
                self.display_messages()
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nExiting monitor mode...")
    
    def single_threaded_mode(self):
        """Fallback single-threaded mode"""
        print("\nStarting in single-threaded mode...")
        print("TX=GP4, RX=GP5")
        print("This mode processes RX/TX sequentially")
        
        buffer = ""
        
        try:
            while True:
                # Check for incoming data
                if self.uart.any():
                    data = self.uart.read()
                    if data:
                        try:
                            buffer += data.decode('utf-8', 'ignore')
                            
                            # Process complete messages
                            while '#' in buffer and '*' in buffer:
                                start_idx = buffer.find('#')
                                end_idx = buffer.find('*', start_idx)
                                
                                if start_idx != -1 and end_idx != -1:
                                    raw_message = buffer[start_idx:end_idx+1]
                                    message = self.parse_message(raw_message)
                                    
                                    if message:
                                        print(f"[{time.time():.0f}] Received: {message}")
                                    
                                    buffer = buffer[end_idx+1:]
                                else:
                                    break
                        except Exception as e:
                            self.log(f"Single-threaded RX error: {e}")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopped single-threaded mode.")
    
    @staticmethod
    def cleanup_threads():
        """Force cleanup any existing threads"""
        try:
            print("Running garbage collection...")
            gc.collect()
            time.sleep(1.0)  # Longer wait
            gc.collect()  # Second pass
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def stop(self):
        print("\nStopping controller...")
        self.running = False
        
        # Wait for threads to finish
        wait_time = 0
        while (self.rx_thread_running or self.tx_thread_running) and wait_time < 5.0:
            time.sleep(0.1)
            wait_time += 0.1
        
        if self.rx_thread_running or self.tx_thread_running:
            print("Warning: Some threads may still be running")
        
        self.threads_started = False
        print("Controller stopped.")

# Usage with improved error handling
if __name__ == "__main__":
    # Clean up any existing threads
    print("Cleaning up any existing threads...")
    UARTController.cleanup_threads()
    
    controller = UARTController()
    
    # Choose mode
    print("\nSelect mode:")
    print("1. Interactive mode (send commands)")
    print("2. Monitor mode (just listen)")
    print("3. Single-threaded mode (fallback)")
    
    try:
        choice = input("Enter choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            # Interactive mode
            success = controller.start()
            if not success:
                print("\nTrying single-threaded interactive mode...")
                # Could implement single-threaded interactive mode here
                
        elif choice == "2":
            # Monitor mode
            if controller.start_threads():
                controller.monitor_mode()
            else:
                print("\nFalling back to single-threaded monitor...")
                controller.single_threaded_mode()
                
        elif choice == "3":
            # Single-threaded mode
            controller.single_threaded_mode()
            
        else:
            print("Invalid choice")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        controller.stop()
        print("Bye!")