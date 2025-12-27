from machine import Pin, UART
import time

class MailClient:
    # Also see server.py
    def __init__(self, uart_id=1, baudrate=9600, tx_pin=4, rx_pin=5):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.response_timeout = 2.0  # Seconds to wait for server response
        print(f"Mail Client initialised on UART{uart_id}")
    
    def send_command(self, command):
        self.uart.write(f"{command}\n".encode('utf-8'))
        print(f"Command sent: {command}")
    
    def receive_response(self):
        start_time = time.time()
        
        while time.time() - start_time < self.response_timeout:
            if self.uart.any():
                try:
                    response = self.uart.readline().decode('utf-8').strip()
                    print(f"Server response: {response}")
                    return response
                except Exception as e:
                    print(f"Error reading response: {e}")
                    return None
            time.sleep(0.1)
        
        print("Response timeout")
        return None
    
    def send_mail(self, message):
        print(f"Sending mail: {message}")
        self.send_command(f"SEND:{message}")
        
        response = self.receive_response()
        return response and response.startswith("ACK:")
    
    def retrieve_mail(self):
        print("Retrieving mail..")
        self.send_command("RETR")
        
        response = self.receive_response()
        if response and response.startswith("MSG:"):
            return response.split(":", 1)[1]
        return None
    
    def delete_all_mail(self):
        print("Deleting all mail..")
        self.send_command("DELE")
        
        response = self.receive_response()
        return response and response.startswith("ACK:")
    
    def get_status(self):
        print("Requesting server status..")
        self.send_command("STAT")
        
        return self.receive_response()
    
    def run_demo(self):
        print("Starting mail client demo..")
        
        demo_messages = [
            "Hello from the client!",
            "This is message number 2",
            "Testing the mail system",
            "Final demo message"
        ]
        
        # Send multiple messages
        for i, message in enumerate(demo_messages, 1):
            success = self.send_mail(f"Demo {i}: {message}")
            if not success:
                print(f"Failed to send message {i}")
            time.sleep(1)
        
        # Check server status
        self.get_status()
        time.sleep(1)
        
        # Retrieve all messages
        print("\nRetrieving all messages:")
        while True:
            message = self.retrieve_mail()
            if message:
                print(f"Retrieved: {message}")
                time.sleep(1)
            else:
                break
        
        # Verify queue is empty
        self.get_status()
        
        print("Demo completed")

# Main execution
if __name__ == "__main__":
    client = MailClient()
    client.run_demo()
