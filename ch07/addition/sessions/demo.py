"""
Quick Start - Session Types VM

A simple example to get you started
"""

from session_vm import *
import threading


def simple_ping_pong():
    """
    Simplest possible example: ping-pong
    
    Session type: !String.?String.end
    Client sends "ping", server responds "pong"
    """
    
    print("="*60)
    print("PING-PONG EXAMPLE")
    print("="*60)
    
    # Create VM
    vm = SessionTypesVM()
    
    # Define session type: send string, receive string, done
    session_type = Send_(str, Recv_(str, End_()))
    
    # Create channel with this protocol
    client_ch, server_ch = vm.create_channel(session_type)
    
    # CLIENT: Send "ping", receive response, close
    client_process = SendProcess(
        "ch", "ping",
        ReceiveProcess(
            "ch", "response",
            CloseProcess("ch")
        )
    )
    
    # SERVER: Receive message, send "pong", close  
    server_process = ReceiveProcess(
        "ch", "msg",
        SendProcess(
            "ch", "pong",
            CloseProcess("ch")
        )
    )
    
    # Run client and server in parallel threads
    def run_client():
        print("\n[CLIENT]")
        client_process.run({"ch": client_ch})
    
    def run_server():
        print("\n[SERVER]")
        server_process.run({"ch": server_ch})
    
    client_thread = threading.Thread(target=run_client)
    server_thread = threading.Thread(target=run_server)
    
    client_thread.start()
    server_thread.start()
    
    client_thread.join()
    server_thread.join()
    
    print()
    print("SUCCESS! The protocol was followed correctly.")
    print()


def menu_example():
    """
    Example with choice: a simple menu
    
    Client chooses between "hello" and "goodbye"
    Server responds appropriately
    """
    
    print()
    print("MENU CHOICE EXAMPLE")
    print()
    
    vm = SessionTypesVM()
    
    # Session type with choice:
    # Client chooses: hello (get a greeting) or goodbye (get a farewell)
    session_type = Choice_({
        "hello": Recv_(str, End_()),
        "goodbye": Recv_(str, End_())
    })
    
    client_ch, server_ch = vm.create_channel(session_type)
    
    # CLIENT: Choose "hello" and receive greeting
    client_process = SelectProcess(
        "ch", "hello",
        ReceiveProcess(
            "ch", "greeting",
            CloseProcess("ch")
        )
    )
    
    # SERVER: Offer both options
    server_process = OfferProcess(
        "ch",
        {
            "hello": SendProcess(
                "ch", "Hi there! Welcome!",
                CloseProcess("ch")
            ),
            "goodbye": SendProcess(
                "ch", "Goodbye! See you later!",
                CloseProcess("ch")
            )
        }
    )
    
    # Run in parallel
    def run_client():
        print("\n[CLIENT]")
        client_process.run({"ch": client_ch})
    
    def run_server():
        print("\n[SERVER]")
        server_process.run({"ch": server_ch})
    
    client_thread = threading.Thread(target=run_client)
    server_thread = threading.Thread(target=run_server)
    
    client_thread.start()
    server_thread.start()
    
    client_thread.join()
    server_thread.join()
    
    print()
    print("Choice handled correctly!")
    print()


if __name__ == "__main__":

    simple_ping_pong()    
    menu_example()
