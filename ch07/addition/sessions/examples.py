"""
Example programs for the Session Types VM

These examples demonstrate:
1. Simple send/receive
2. Client-server with choice
3. Calculator service
4. Protocol violations (commented out)
"""

# for exmples 8, and for the recursive unfolding helper
from session_vm import (
    SessionTypesVM,
    Send_, Recv_, Choice_, Offer_, End_,
    SendChan_, RecvChan_, Rec_, Var_,
    SendProcess, ReceiveProcess, SelectProcess, OfferProcess, CloseProcess,
    _unfold_if_rec,
)


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


def example7_channel_mobility():
    """Example 7: Channel mobility - delegating a channel endpoint"""
    print()
    print("EXAMPLE 7: Channel Mobility (Delegation Chain)")
    print()

    # A Forwarder sits between Sender and Receiver.
    # Sender creates a data channel, passes the remote endpoint to Forwarder,
    # who passes it on to Receiver.  Receiver then uses it to send 99 back to Sender.
    #
    # Session types involved:
    #   data_ch   :  ?int.end          (Sender's end — it will receive the int)
    #   setup_ch  :  !(?int.end).end   — wait, the *remote* end is !int.end, so:
    #               SendChan(!int.end, end)
    #   forward_ch:  SendChan(!int.end, end)  (same shape, Forwarder→Receiver)

    import threading

    vm = SessionTypesVM()

    # data channel: Sender holds the receiving end, remote end sends
    data_ep_sender, data_ep_remote = vm.create_channel(Recv_(int, End_()))

    # setup channel: Sender will delegate data_ep_remote to Forwarder
    setup_ep_sender, setup_ep_forwarder = vm.create_channel(
        SendChan_(data_ep_remote.session_type, End_())
    )

    # forward channel: Forwarder will delegate data_ep_remote onward to Receiver
    forward_ep_forwarder, forward_ep_receiver = vm.create_channel(
        SendChan_(data_ep_remote.session_type, End_())
    )

    def run_sender():
        print("\nSENDER:")
        env = {
            'setup':  setup_ep_sender,
            'data':   data_ep_sender,
            'ep_remote': data_ep_remote,   # the endpoint we're giving away
        }
        SendProcess(
            'setup', 'ep_remote',           # delegate data_ep_remote to Forwarder
            ReceiveProcess(
                'data', 'result',           # wait for Receiver to send back 99
                CloseProcess('data')
            )
        ).run(env)
        print(f"\n  Sender received back: {env['result']}")

    def run_forwarder():
        print("\nFORWARDER:")
        env = {'setup': setup_ep_forwarder, 'fwd': forward_ep_forwarder}
        ReceiveProcess(
            'setup', 'delegated',           # receive the endpoint from Sender
            SendProcess(
                'fwd', 'delegated',         # forward it straight to Receiver
                CloseProcess('setup')
            )
        ).run(env)

    def run_receiver():
        print("\nRECEIVER:")
        env = {'fwd': forward_ep_receiver}
        ReceiveProcess(
            'fwd', 'data_remote',           # receive the delegated endpoint
            SendProcess(
                'data_remote', 99,          # use it to send 99 back to Sender
                CloseProcess('data_remote')
            )
        ).run(env)

    threads = [
        threading.Thread(target=run_sender),
        threading.Thread(target=run_forwarder),
        threading.Thread(target=run_receiver),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print()
    print("Mobility works! Endpoint traveled: Sender → Forwarder → Receiver.")
    print()


def example8_recursive_server():
    """Example 8: Recursive session type - an increment server"""
    print()
    print("EXAMPLE 8: Recursive Session Type (Increment Server)")
    print()

    # Server repeatedly receives an int and sends back int+1.
    # Session type (server's end):  μX. ?int.!int.X
    # The Rec type unfolds transparently on each iteration.

    import threading

    vm = SessionTypesVM()

    server_type = Rec_('X', Recv_(int, Send_(int, Var_('X'))))
    ep_server, ep_client = vm.create_channel(server_type)

    print(f"  Server type: {ep_server.session_type}")
    print(f"  Client type: {ep_client.session_type}")
    print()

    results = []
    num_requests = 3

    def run_server():
        print("\nSERVER:")
        env = {'ch': ep_server}
        for _ in range(num_requests):
            ep_server.session_type = _unfold_if_rec(ep_server.session_type)
            ep_server.used = False
            ReceiveProcess('ch', 'n', None).run(env)
            n = env['n']
            ep_server.session_type = _unfold_if_rec(ep_server.session_type)
            ep_server.used = False
            SendProcess('ch', n + 1, None).run(env)
            ep_server.session_type = _unfold_if_rec(ep_server.session_type)

    def run_client():
        print("\nCLIENT:")
        env = {'ch': ep_client}
        for val in [10, 20, 30]:
            ep_client.session_type = _unfold_if_rec(ep_client.session_type)
            ep_client.used = False
            SendProcess('ch', val, None).run(env)
            ep_client.session_type = _unfold_if_rec(ep_client.session_type)
            ep_client.used = False
            ReceiveProcess('ch', 'resp', None).run(env)
            results.append(env['resp'])
            print(f"  Sent {val}, got back {env['resp']}")
            ep_client.session_type = _unfold_if_rec(ep_client.session_type)

    t1 = threading.Thread(target=run_server)
    t2 = threading.Thread(target=run_client)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results == [11, 21, 31], f"Unexpected results: {results}"
    print()
    print(f"Recursive protocol completed! Results: {results}")
    print()


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
    example7_channel_mobility()
    example8_recursive_server()

    print()
    print("Done.")
    print()
