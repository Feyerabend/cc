from machine import Pin, UART
import time

# set up UART for server
uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# simple message queue for storing messages
message_queue = []

def process_incoming():
    if uart1.any():
        try:
            # read incoming message from client
            incoming_message = uart1.readline().decode('utf-8').strip()
            print(f"Received: {incoming_message}")
            handle_client_request(incoming_message)
        except Exception as e:
            print(f"Error processing incoming message: {e}")

def handle_client_request(request):
    if request.startswith("SEND"):
        # Extract the message payload to store
        message = request.split(":", 1)[1]
        message_queue.append(message)
        uart1.write(f"ACK: Message received\n")
    elif request == "RETR":
        if message_queue:
            message = message_queue.pop(0)  # Send the oldest message
            uart1.write(f"MSG: {message}\n")
        else:
            uart1.write("NO MSG: No messages in queue\n")
    elif request == "DELE":
        if message_queue:
            message_queue.clear()  # Clear all messages
            uart1.write("ACK: All messages deleted\n")
        else:
            uart1.write("NO MSG: No messages to delete\n")
    else:
        uart1.write("ERR: Invalid command\n")

def main():
    print("Mail Server is running...")
    while True:
        process_incoming()
        time.sleep(0.1)

main()
