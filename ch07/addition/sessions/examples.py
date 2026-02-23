"""
Example programs for the Session Types VM

These examples demonstrate:
1. Simple send/receive
2. Client-server with choice
3. Calculator service
4. Protocol violations (commented out)
"""

from session_vm import *


def example1_simple_communication():
    """Example 1: Simple send and receive"""
    print()
    print("EXAMPLE 1: Simple Send/Receive")
    print()
    
    vm = SessionTypesVM()
    
    # Session type: !Int.?String.end
    session_type = Send_(int, Recv_(str, End_()))
    
    # Create channel
    client_ch, server_ch = vm.create_channel(session_type)
    
    # Client process: send 42, receive response, close
    client = SendProcess(
        "ch", 42,
        ReceiveProcess(
            "ch", "response",
            CloseProcess("ch")
        )
    )
    
    # Server process: receive number, send response, close
    server = ReceiveProcess(
        "ch", "num",
        SendProcess(
            "ch", "Got your number!",
            CloseProcess("ch")
        )
    )
    
    # Run in parallel using threads
    import threading
    
    def run_client():
        print("\nCLIENT:")
        client.run({"ch": client_ch})
    
    def run_server():
        print("\nSERVER:")
        server.run({"ch": server_ch})
    
    t1 = threading.Thread(target=run_client)
    t2 = threading.Thread(target=run_server)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def example2_calculator_service():
    """Example 2: Calculator with choice"""
    print()
    print("EXAMPLE 2: Calculator Service with Choice")
    print()
    
    vm = SessionTypesVM()
    
    # Session type: 
    # Server offers choices, so server has Offer (&), client has Choice (⊕)
    # ⊕{ add: !Int.!Int.?Int.end,
    #    multiply: !Int.!Int.?Int.end,
    #    done: end }
    
    session_type = Choice_({
        "add": Send_(int, Send_(int, Recv_(int, End_()))),
        "multiply": Send_(int, Send_(int, Recv_(int, End_()))),
        "done": End_()
    })
    
    # Create channel
    client_ch, server_ch = vm.create_channel(session_type)
    
    # Client: choose "add", send 5 and 3, receive result
    client = SelectProcess(
        "ch", "add",
        SendProcess(
            "ch", 5,
            SendProcess(
                "ch", 3,
                ReceiveProcess(
                    "ch", "result",
                    CloseProcess("ch")
                )
            )
        )
    )
    
    # Server: offer choice, handle branches
    server = OfferProcess(
        "ch",
        {
            "add": ReceiveProcess(
                "ch", "x",
                ReceiveProcess(
                    "ch", "y",
                    # Here we'd compute x+y, but for now just send a dummy value
                    SendProcess("ch", 8, CloseProcess("ch"))
                )
            ),
            "multiply": ReceiveProcess(
                "ch", "x",
                ReceiveProcess(
                    "ch", "y",
                    SendProcess("ch", 15, CloseProcess("ch"))
                )
            ),
            "done": CloseProcess("ch")
        }
    )
    
    # Run in parallel
    import threading
    
    def run_client():
        print("\nCLIENT:")
        client.run({"ch": client_ch})
    
    def run_server():
        print("\nSERVER:")
        server.run({"ch": server_ch})
    
    t1 = threading.Thread(target=run_client)
    t2 = threading.Thread(target=run_server)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def example3_type_error():
    """Example 3: Type error - sending wrong type"""
    print()
    print("EXAMPLE 3: Type Error Demo")
    print()
    
    vm = SessionTypesVM()
    
    # Session type expects Int
    session_type = Send_(int, End_())
    
    client_ch, server_ch = vm.create_channel(session_type)
    
    # Try to send a string instead
    try:
        client = SendProcess("ch", "wrong type!", CloseProcess("ch"))
        client.run({"ch": client_ch})
    except TypeError as e:
        print(f"\n✓ Caught type error as expected: {e}")


def example4_linearity_violation():
    """Example 4: Linearity violation - using channel twice"""
    print()
    print("EXAMPLE 4: Linearity Violation Demo")
    print()
    
    vm = SessionTypesVM()
    
    # Session type: !Int.!Int.end (send twice)
    session_type = Send_(int, Send_(int, End_()))
    
    client_ch, server_ch = vm.create_channel(session_type)
    
    # Try to use same channel in two sequential sends from same state
    # We'll create a bad process that tries to send on "ch" twice in parallel
    try:
        # Create a process that sends 42
        send1 = SendProcess("ch", 42, None)
        # Store the channel in env
        env = {"ch": client_ch}
        # Run first send
        send1.run(env)
        # Now channel has continuation Send(int, End())
        # Try to use the ORIGINAL channel again (before we updated it)
        # This simulates trying to use the same linear resource twice
        
        # Reset the channel to original state (cheating to demonstrate)
        client_ch.session_type = session_type
        client_ch.used = True  # Already marked as used
        
        send2 = SendProcess("ch", 43, None)
        send2.run(env)
        
    except RuntimeError as e:
        print(f"\n✓ Caught linearity violation as expected: {e}")


def example5_protocol_mismatch():
    """Example 5: Protocol mismatch - wrong operation"""
    print()
    print("EXAMPLE 5: Protocol Mismatch Demo")
    print()
    
    vm = SessionTypesVM()
    
    # Session type expects Send
    session_type = Send_(int, End_())
    
    client_ch, server_ch = vm.create_channel(session_type)
    
    # Try to receive instead of send
    try:
        wrong = ReceiveProcess("ch", "x", CloseProcess("ch"))
        wrong.run({"ch": client_ch})
    except TypeError as e:
        print(f"\n✓ Caught protocol mismatch as expected: {e}")


def example6_producer_consumer():
    """Example 6: Producer-Consumer pattern"""
    print()
    print("EXAMPLE 6: Producer-Consumer")
    print()
    
    vm = SessionTypesVM()
    
    # Producer sends 3 items then signals done
    # !Int.!Int.!Int.!String.end  (where String is "done")
    session_type = Send_(int, Send_(int, Send_(int, Send_(str, End_()))))
    
    producer_ch, consumer_ch = vm.create_channel(session_type)
    
    # Producer
    producer = SendProcess(
        "ch", 10,
        SendProcess(
            "ch", 20,
            SendProcess(
                "ch", 30,
                SendProcess(
                    "ch", "done",
                    CloseProcess("ch")
                )
            )
        )
    )
    
    # Consumer
    consumer = ReceiveProcess(
        "ch", "item1",
        ReceiveProcess(
            "ch", "item2",
            ReceiveProcess(
                "ch", "item3",
                ReceiveProcess(
                    "ch", "signal",
                    CloseProcess("ch")
                )
            )
        )
    )
    
    # Run in parallel
    import threading
    
    def run_producer():
        print("\nPRODUCER:")
        producer.run({"ch": producer_ch})
    
    def run_consumer():
        print("\nCONSUMER:")
        consumer.run({"ch": consumer_ch})
    
    t1 = threading.Thread(target=run_producer)
    t2 = threading.Thread(target=run_consumer)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    print()
    print("SESSION TYPES ..")
    print()
    
    # Run examples
    example1_simple_communication()
    example2_calculator_service()
    example3_type_error()
    example4_linearity_violation()
    example5_protocol_mismatch()
    example6_producer_consumer()
    
    print()
    print("Done.")
    print()
