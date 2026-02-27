import asyncio
import sys

async def handle_server(reader, writer):
    while True:
        data = await reader.read(1024)
        if not data:
            print("Server disconnected")
            return False
        print(f"Server: {data.decode().strip()}")
        return True

async def handle_user_input(writer):
    loop = asyncio.get_event_loop()
    while True:
        # Read user input non-blocking using asyncio
        message = await loop.run_in_executor(None, lambda: sys.stdin.readline().strip())
        if message.lower() == "quit":
            return False
        if message:
            writer.write((message + "\n").encode())
            await writer.drain()
        return True

async def tcp_client():
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8080)
        print("Connected to server 127.0.0.1:8080")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    try:
        # Run server reading and user input tasks concurrently
        tasks = [
            asyncio.create_task(handle_server(reader, writer)),
            asyncio.create_task(handle_user_input(writer))
        ]
        # Wait for either task to complete (i.e., disconnect or quit)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()  # Cancel remaining tasks
    finally:
        writer.close()
        await writer.wait_closed()
        print("Client disconnected")

def main():
    asyncio.run(tcp_client())

if __name__ == "__main__":
    main()