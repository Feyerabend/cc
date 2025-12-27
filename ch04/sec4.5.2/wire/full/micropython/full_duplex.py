from machine import Pin, UART, ADC
import time
import _thread
from collections import deque
import gc

class FullDuplexUART:
    def __init__(self, uart_id=1, baudrate=9600, tx_pin=4, rx_pin=5):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.temp_sensor = ADC(4)
        self.led = Pin(25, Pin.OUT)
        
        # Buffers for incoming and outgoing messages
        self.rx_buffer = deque((), 50)
        self.tx_buffer = deque((), 50)
        
        # Control flags
        self.running = True
        self.counter = 0
        
        # Thread management - improved tracking
        self.rx_thread_id = None
        self.tx_thread_id = None
        self.rx_thread_running = False
        self.tx_thread_running = False
        self.threads_started = False
        
        # Locks for thread safety (simple flags since MicroPython threading is limited)
        self.rx_lock = False
        self.tx_lock = False
        
        # Debug
        self.debug = True
    
    def log(self, message):
        if self.debug:
            print(f"[{time.time():.3f}] {message}")
    
    def read_temperature(self):
        try:
            reading = self.temp_sensor.read_u16()
            voltage = reading * 3.3 / 65535
            temperature = 27 - (voltage - 0.706) / 0.001721
            return round(temperature, 1)
        except Exception as e:
            print(f"Unexpected error starting threads: {e}")
            return False
    
    def get_status(self):
        """Display current status"""
        rx_count = len(self.rx_buffer)
        tx_count = len(self.tx_buffer)
        
        print(f"\nSystem Status:")
        print(f"  Running: {self.running}")
        print(f"  Threads Started: {self.threads_started}")
        print(f"  RX Thread: {'Running' if self.rx_thread_running else 'Stopped'}")
        print(f"  TX Thread: {'Running' if self.tx_thread_running else 'Stopped'}")
        print(f"  RX Buffer: {rx_count}/50")
        print(f"  TX Buffer: {tx_count}/50")
        print(f"  Counter: {self.counter}")
        print(f"  Temperature: {self.read_temperature()}°C")
    
    def start(self):
        print("Full-Duplex UART Communication Starting...")
        print("TX=GP4, RX=GP5")
        print("Commands: STATUS, PING, LED_ON, LED_OFF")
        print("Requests: TEMP")
        
        # Try to start threads with error handling
        if not self.start_threads():
            print("Failed to start threads!")
            return False
        
        print("Threads started successfully!")
        
        # Main loop - sends periodic temperature data and processes received messages
        try:
            last_temp_send = 0
            temp_interval = 5.0  # Send temperature every 5 seconds
            
            while self.running:
                current_time = time.time()
                
                # Send periodic temperature data
                if current_time - last_temp_send >= temp_interval:
                    temp_c = self.read_temperature()
                    temp_f = (temp_c * 9/5) + 32
                    temp_message = f"TEMP:{temp_c}C,{temp_f:.1f}F,COUNT:{self.counter}"
                    self.send_message(temp_message)
                    last_temp_send = current_time
                    self.counter += 1
                
                # Process any received messages
                self.process_received_messages()
                
                # Check thread health
                if not self.rx_thread_running or not self.tx_thread_running:
                    self.log("Warning: One or more threads stopped!")
                    break
                
                # Sleep with periodic message checking
                for _ in range(10):  # Check every 0.1s for 1s total
                    if not self.running:
                        break
                    self.process_received_messages()
                    time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping communication...")
            self.stop()
        except Exception as e:
            print(f"Main loop error: {e}")
            self.stop()
        
        return True
    
    def stop(self):
        print("Stopping threads...")
        self.running = False
        
        # Wait for threads to finish with timeout
        wait_time = 0
        max_wait = 5.0
        
        while (self.rx_thread_running or self.tx_thread_running) and wait_time < max_wait:
            time.sleep(0.1)
            wait_time += 0.1
        
        if self.rx_thread_running or self.tx_thread_running:
            print("Warning: Some threads may still be running")
        else:
            print("All threads stopped cleanly")
        
        self.threads_started = False
        
        # Turn off LED
        try:
            self.led.off()
        except:
            pass
    
    def start_single_threaded(self):
        """Alternative single-threaded mode if threading fails"""
        print("Starting in single-threaded mode...")
        print("TX=GP4, RX=GP5")
        print("Note: This mode has limited simultaneous RX/TX capability")
        
        buffer = ""
        last_temp_send = 0
        temp_interval = 5.0
        
        try:
            while True:
                current_time = time.time()
                
                # Check for received data
                if self.uart.any():
                    data = self.uart.read()
                    if data:
                        try:
                            new_data = data.decode('utf-8', 'ignore')
                            buffer += new_data
                            
                            # Process complete messages
                            while '#' in buffer and '*' in buffer:
                                start_idx = buffer.find('#')
                                end_idx = buffer.find('*', start_idx)
                                
                                if start_idx != -1 and end_idx != -1:
                                    raw_message = buffer[start_idx:end_idx+1]
                                    message = self.parse_message(raw_message)
                                    
                                    if message:
                                        print(f"Received: {message}")
                                        
                                        # Handle immediately in single-threaded mode
                                        if message.startswith("CMD:"):
                                            self.handle_command_direct(message[4:])
                                        elif message.startswith("REQ:"):
                                            self.handle_request_direct(message[4:])
                                    
                                    buffer = buffer[end_idx+1:]
                                else:
                                    break
                        except Exception as e:
                            self.log(f"Single-threaded RX error: {e}")
                
                # Send periodic temperature
                if current_time - last_temp_send >= temp_interval:
                    temp_c = self.read_temperature()
                    temp_f = (temp_c * 9/5) + 32
                    temp_message = f"TEMP:{temp_c}C,{temp_f:.1f}F,COUNT:{self.counter}"
                    
                    try:
                        formatted = self.format_message(temp_message)
                        self.uart.write(formatted.encode('utf-8'))
                        self.blink_led(0.05)
                        print(f"Sent: {temp_message}")
                    except Exception as e:
                        self.log(f"Single-threaded TX error: {e}")
                    
                    last_temp_send = current_time
                    self.counter += 1
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopped single-threaded mode.")
        except Exception as e:
            print(f"Single-threaded error: {e}")
        finally:
            try:
                self.led.off()
            except:
                pass

    @staticmethod
    def cleanup_threads():
        """Force cleanup any existing threads - call before creating new instance"""
        try:
            print("Running garbage collection...")
            gc.collect()
            time.sleep(1.0)  # Give more time for cleanup
            gc.collect()  # Second pass
            print("Cleanup complete.")
        except Exception as e:
            print(f"Cleanup error: {e}")
    

    def handle_command_direct(self, command):
        """Direct command handling for single-threaded mode"""
        print(f"Processing command: {command}")
        
        try:
            if command == "STATUS":
                temp_c = self.read_temperature()
                response = f"STATUS:TEMP={temp_c}C,COUNT={self.counter}"
            elif command == "PING":
                response = "PONG"
            elif command == "LED_ON":
                self.led.on()
                response = "ACK:LED_ON"
            elif command == "LED_OFF":
                self.led.off()
                response = "ACK:LED_OFF"
            else:
                response = f"ERROR:UNKNOWN_CMD:{command}"
            
            # Send response immediately
            formatted = self.format_message(response)
            self.uart.write(formatted.encode('utf-8'))
            self.blink_led(0.05)
            print(f"Sent: {response}")
            
        except Exception as e:
            self.log(f"Direct command handling error: {e}")
    
    def handle_request_direct(self, request):
        """Direct request handling for single-threaded mode"""
        print(f"Processing request: {request}")
        
        try:
            if request == "TEMP":
                temp_c = self.read_temperature()
                temp_f = (temp_c * 9/5) + 32
                response = f"TEMP:{temp_c}C,{temp_f:.1f}F"
            else:
                response = f"ERROR:UNKNOWN_REQ:{request}"
            
            # Send response immediately
            formatted = self.format_message(response)
            self.uart.write(formatted.encode('utf-8'))
            self.blink_led(0.05)
            print(f"Sent: {response}")
            
        except Exception as e:
            self.log(f"Direct request handling error: {e}")

    
    def blink_led(self, duration=0.1):
        try:
            self.led.on()
            time.sleep(duration)
            self.led.off()
        except Exception as e:
            self.log(f"LED error: {e}")
    
    def format_message(self, message):
        return f"#{message}*"
    
    def parse_message(self, raw_message):
        if raw_message.startswith('#') and raw_message.endswith('*'):
            return raw_message[1:-1]
        return None
    
    def safe_buffer_operation(self, buffer, item, lock_name, operation='add'):
        """Thread-safe buffer operations with better error handling"""
        retry_count = 0
        max_retries = 50
        
        # Wait for lock to be free
        while getattr(self, lock_name) and retry_count < max_retries:
            time.sleep(0.002)
            retry_count += 1
        
        if retry_count >= max_retries:
            self.log(f"Timeout acquiring {lock_name}")
            return None
        
        try:
            # Acquire lock
            setattr(self, lock_name, True)
            
            if operation == 'add':
                if len(buffer) >= 50:
                    buffer.popleft()  # Remove oldest
                buffer.append(item)
                result = True
            elif operation == 'get':
                result = buffer.popleft() if buffer else None
            else:
                result = None
            
            # Release lock
            setattr(self, lock_name, False)
            return result
            
        except Exception as e:
            self.log(f"Buffer operation error: {e}")
            setattr(self, lock_name, False)
            return None if operation == 'get' else False
    
    def rx_thread(self):
        self.log("RX Thread starting...")
        self.rx_thread_running = True
        buffer = ""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while self.running and consecutive_errors < max_consecutive_errors:
                try:
                    if self.uart.any():
                        data = self.uart.read()
                        if data:
                            try:
                                buffer += data.decode('utf-8', 'ignore')
                                consecutive_errors = 0  # Reset error count on success
                            except Exception as e:
                                self.log(f"RX decode error: {e}")
                                consecutive_errors += 1
                                continue
                            
                            # Look for complete messages
                            while '#' in buffer and '*' in buffer:
                                start_idx = buffer.find('#')
                                end_idx = buffer.find('*', start_idx)
                                
                                if start_idx != -1 and end_idx != -1:
                                    raw_message = buffer[start_idx:end_idx+1]
                                    message = self.parse_message(raw_message)
                                    
                                    if message:
                                        # Thread-safe buffer access
                                        success = self.safe_buffer_operation(
                                            self.rx_buffer, message, 'rx_lock', 'add'
                                        )
                                        if success:
                                            self.log(f"RX: {message}")
                                    
                                    buffer = buffer[end_idx+1:]  # remove processed part
                                else:
                                    break
                    
                    time.sleep(0.01)  # small delay to prevent busy waiting
                    
                except Exception as e:
                    self.log(f"RX Thread error: {e}")
                    consecutive_errors += 1
                    time.sleep(0.1)
        
        except Exception as e:
            self.log(f"RX Thread fatal error: {e}")
        
        finally:
            self.rx_thread_running = False
            self.log("RX Thread stopped")
    
    def tx_thread(self):
        self.log("TX Thread starting...")
        self.tx_thread_running = True
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while self.running and consecutive_errors < max_consecutive_errors:
                try:
                    # Check if there are messages to send
                    message_to_send = self.safe_buffer_operation(
                        self.tx_buffer, None, 'tx_lock', 'get'
                    )
                    
                    if message_to_send:
                        try:
                            formatted_message = self.format_message(message_to_send)
                            self.uart.write(formatted_message.encode('utf-8'))
                            self.blink_led(0.05)  # quick blink for TX
                            self.log(f"TX: {message_to_send}")
                            consecutive_errors = 0  # Reset on success
                        except Exception as e:
                            self.log(f"TX send error: {e}")
                            consecutive_errors += 1
                    
                    time.sleep(0.01)  # small delay
                    
                except Exception as e:
                    self.log(f"TX Thread error: {e}")
                    consecutive_errors += 1
                    time.sleep(0.1)
        
        except Exception as e:
            self.log(f"TX Thread fatal error: {e}")
        
        finally:
            self.tx_thread_running = False
            self.log("TX Thread stopped")
    
    def send_message(self, message):
        """Queue a message for sending"""
        success = self.safe_buffer_operation(self.tx_buffer, message, 'tx_lock', 'add')
        if not success:
            self.log(f"Failed to queue message: {message}")
    
    def get_received_message(self):
        """Get one received message"""
        return self.safe_buffer_operation(self.rx_buffer, None, 'rx_lock', 'get')
    
    def process_received_messages(self):
        """Process all pending received messages"""
        while True:
            message = self.get_received_message()
            if not message:
                break
                
            print(f"Received: {message}")
            
            # Process different message types
            if message.startswith("CMD:"):
                self.handle_command(message[4:])
            elif message.startswith("REQ:"):
                self.handle_request(message[4:])
    
    def handle_command(self, command):
        print(f"Processing command: {command}")
        
        try:
            if command == "STATUS":
                temp_c = self.read_temperature()
                status_msg = f"STATUS:TEMP={temp_c}C,COUNT={self.counter}"
                self.send_message(status_msg)
            elif command == "PING":
                self.send_message("PONG")
            elif command == "LED_ON":
                self.led.on()
                self.send_message("ACK:LED_ON")
            elif command == "LED_OFF":
                self.led.off()
                self.send_message("ACK:LED_OFF")
            else:
                self.send_message(f"ERROR:UNKNOWN_CMD:{command}")
        except Exception as e:
            self.log(f"Command handling error: {e}")
            self.send_message(f"ERROR:CMD_FAILED:{command}")
    
    def handle_request(self, request):
        print(f"Processing request: {request}")
        
        try:
            if request == "TEMP":
                temp_c = self.read_temperature()
                temp_f = (temp_c * 9/5) + 32
                self.send_message(f"TEMP:{temp_c}C,{temp_f:.1f}F")
            else:
                self.send_message(f"ERROR:UNKNOWN_REQ:{request}")
        except Exception as e:
            self.log(f"Request handling error: {e}")
            self.send_message(f"ERROR:REQ_FAILED:{request}")
    
    def start_threads(self):
        """Start threads with better error detection"""
        if self.threads_started:
            return True
            
        try:
            self.log("Starting threads...")
            
            # Reset state
            self.running = True
            self.rx_thread_running = False
            self.tx_thread_running = False
            
            # Force garbage collection
            gc.collect()
            
            # Start RX thread
            self.log("Starting RX thread...")
            self.rx_thread_id = _thread.start_new_thread(self.rx_thread, ())
            time.sleep(0.3)  # Longer delay
            
            # Wait for RX thread to start
            start_time = time.time()
            while not self.rx_thread_running and (time.time() - start_time) < 3.0:
                time.sleep(0.1)
            
            if not self.rx_thread_running:
                self.log("RX thread failed to start!")
                return False
            
            # Start TX thread
            self.log("Starting TX thread...")
            self.tx_thread_id = _thread.start_new_thread(self.tx_thread, ())
            time.sleep(0.3)
            
            # Wait for TX thread to start
            start_time = time.time()
            while not self.tx_thread_running and (time.time() - start_time) < 3.0:
                time.sleep(0.1)
            
            if not self.tx_thread_running:
                self.log("TX thread failed to start!")
                self.running = False  # Stop RX thread
                return False
            
            self.threads_started = True
            self.log("Both threads started successfully!")
            return True
            
        except OSError as e:
            error_str = str(e).lower()
            if "core1 in use" in error_str or "core" in error_str:
                print("Error: Core1 is already in use!")
                print("Solutions:")
                print("1. Reset the device (Ctrl+D)")
                print("2. Or call machine.reset()")
                print("3. Or use single-threaded mode")
                return False
            else:
                print(f"Thread start OSError: {e}")
                return False
    
        except Exception as e:
            self.log(f"Unexpected error starting threads: {e}")
            self.running = False  # Stop any partially started threads
            self.rx_thread_running = False
            self.tx_thread_running = False
            self.threads_started = False
            return False

# Usage with error handling
if __name__ == "__main__":
    print("Full Duplex UART System")
    print("======================")
    
    # Clean up any existing threads
    FullDuplexUART.cleanup_threads()
    
    comm = FullDuplexUART()
    
    print("\nSelect mode:")
    print("1. Multi-threaded mode (recommended)")
    print("2. Single-threaded mode (fallback)")
    print("3. Status check only")
    
    try:
        choice = input("Enter choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            # Try threaded mode first
            success = comm.start()
            if not success:
                print("\nMulti-threaded mode failed.")
                print("Would you like to try single-threaded mode? (y/n): ", end="")
                fallback = input().strip().lower()
                if fallback == 'y':
                    comm.start_single_threaded()
                    
        elif choice == "2":
            # Single-threaded mode
            comm.start_single_threaded()
            
        elif choice == "3":
            # Just show status
            comm.get_status()
            
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        comm.stop()
        print("System shutdown complete.")
