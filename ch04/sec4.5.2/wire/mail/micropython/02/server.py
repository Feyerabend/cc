from machine import Pin, UART
import time

class MailServer:
    # Simple mail server implementation using UART communication
    def __init__(self, uart_id=1, baudrate=9600, tx_pin=4, rx_pin=5):
        # Init UART communication:
        # uart_id (int): UART peripheral number (0 or 1)
        # baudrate (int): Communication speed in bits per second
        # tx_pin (int): GPIO pin for transmission
        # rx_pin (int): GPIO pin for reception
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.message_queue = []
        self.max_queue_size = 10  # Prevent memory overflow
        
        print(f"Mail Server initialised on UART{uart_id}")
        print(f"Configuration: {baudrate} baud, TX=GPIO{tx_pin}, RX=GPIO{rx_pin}")
    
    def send_response(self, response):
        self.uart.write(f"{response}\n".encode('utf-8'))
        print(f"Response sent: {response}")
    
    def process_incoming(self):
        if self.uart.any():
            try:
                # Read complete line from client
                raw_data = self.uart.readline()
                if raw_data:
                    request = raw_data.decode('utf-8').strip()
                    print(f"Received request: {request}")
                    self.handle_client_request(request)
            except Exception as e:
                print(f"Error processing request: {e}")
                self.send_response("ERR: Processing error")
    
    def handle_client_request(self, request):
        if request.startswith("SEND:"):
            self._handle_send_command(request)
        elif request == "RETR":
            self._handle_retrieve_command()
        elif request == "DELE":
            self._handle_delete_command()
        elif request == "STAT":
            self._handle_status_command()
        else:
            self.send_response("ERR: Unknown command")
    
    def _handle_send_command(self, request):
        try:
            message = request.split(":", 1)[1]  # Extract message after ':'
            
            if len(self.message_queue) >= self.max_queue_size:
                self.send_response("ERR: Queue full")
                return
            
            self.message_queue.append(message)
            self.send_response(f"ACK: Message stored (queue size: {len(self.message_queue)})")
            
        except IndexError:
            self.send_response("ERR: SEND command requires message")
    
    def _handle_retrieve_command(self):
        if self.message_queue:
            message = self.message_queue.pop(0)  # FIFO retrieval
            self.send_response(f"MSG: {message}")
        else:
            self.send_response("NO MSG: Queue empty")
    
    def _handle_delete_command(self):
        deleted_count = len(self.message_queue)
        self.message_queue.clear()
        self.send_response(f"ACK: {deleted_count} messages deleted")
    
    def _handle_status_command(self):
        count = len(self.message_queue)
        self.send_response(f"ACK: {count} messages in queue")
    
    def run(self):
        # Main server loop - continuously process client requests
        print("Mail server is running..")
        print("Supported commands: SEND:<msg>, RETR, DELE, STAT")
        
        while True:
            self.process_incoming()
            time.sleep(0.1)  # Prevent excessive CPU usage

# Main execution
if __name__ == "__main__":
    server = MailServer()
    server.run()
