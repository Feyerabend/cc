import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"New client connected: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode().strip()
            print(f"Received from {addr}: {message}")

            writer.write("ACK\n".encode())
            await writer.drain()
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        print(f"Client {addr} disconnected")
        writer.close()
        await writer.wait_closed()

async def event_loop():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8080)
    print("Server listening on port 8080...")

    async with server:
        await server.serve_forever()

def main():
    try:
        asyncio.run(event_loop())
    except KeyboardInterrupt:
        print("Server stopped.")

if __name__ == "__main__":
    main()