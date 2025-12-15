import machine
import sdcard
import uos
import ujson
import utime
import network
import socket
import gc

# VFS Component with improved metadata
class SimpleVFS:
    def __init__(self, mount_point="/sd"):
        self.mount_point = mount_point
        self.metadata_file = f"{mount_point}/.vfs_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        try:
            with open(self.metadata_file, "r") as f:
                return ujson.load(f)
        except:
            return {}
    
    def _save_metadata(self):
        with open(self.metadata_file, "w") as f:
            ujson.dump(self.metadata, f)
    
    def _detect_file_type(self, filename):
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext in ['txt', 'log', 'cfg', 'ini', 'json', 'py', 'md']:
            return 'text'
        elif ext in ['img', 'raw', 'rgb', 'rgb565']:
            return 'image'
        elif ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
            return 'image'
        elif ext in ['bin', 'dat']:
            return 'binary'
        else:
            return 'unknown'
    
    def create_file(self, filename, data, permissions="rw", file_type=None):
        full_path = f"{self.mount_point}/{filename}"
        with open(full_path, "wb") as f:
            if isinstance(data, str):
                f.write(data.encode())
            else:
                f.write(data)
        
        if file_type is None:
            file_type = self._detect_file_type(filename)
        
        self.metadata[filename] = {
            "permissions": permissions,
            "created": utime.time(),
            "size": len(data),
            "type": file_type
        }
        self._save_metadata()
        print(f"Created: {filename} ({len(data)} bytes, type: {file_type})")
    
    def read_file(self, filename):
        if filename not in self.metadata:
            raise FileNotFoundError(f"File not found: {filename}")
        
        if 'r' not in self.metadata[filename]["permissions"]:
            raise OSError(f"No read permission: {filename}")
        
        full_path = f"{self.mount_point}/{filename}"
        with open(full_path, "rb") as f:
            return f.read()
    
    def read_file_chunked(self, filename, chunk_size=1024):
        if filename not in self.metadata:
            raise FileNotFoundError(f"File not found: {filename}")
        
        if 'r' not in self.metadata[filename]["permissions"]:
            raise OSError(f"No read permission: {filename}")
        
        full_path = f"{self.mount_point}/{filename}"
        with open(full_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def list_files(self):
        return [{"name": f, 
                 "size": m["size"],
                 "type": m.get("type", "unknown")} 
                for f, m in self.metadata.items()]
    
    def file_exists(self, filename):
        return filename in self.metadata
    
    def get_file_info(self, filename):
        if filename not in self.metadata:
            return None
        return self.metadata[filename]


# Improved compression with better buffer handling
class RLECompressor:    
    @staticmethod
    def compress(data, max_chunk=4096):
        if len(data) == 0:
            return bytes()
        
        compressed = bytearray()
        i = 0
        
        while i < len(data):
            current = data[i]
            count = 1
            
            # Count consecutive identical bytes (max 255)
            while i + count < len(data) and data[i + count] == current and count < 255:
                count += 1
            
            compressed.append(count)
            compressed.append(current)
            i += count
            
            # Yield control periodically for large files
            if len(compressed) % max_chunk == 0:
                gc.collect()
        
        return bytes(compressed)
    
    @staticmethod
    def decompress(data):
        decompressed = bytearray()
        i = 0
        while i < len(data) - 1:
            count = data[i]
            value = data[i + 1]
            decompressed.extend([value] * count)
            i += 2
        return bytes(decompressed)


# Improved File Server with better buffer handling
class FileServer:
    def __init__(self, vfs, ssid="PicoFiles", port=8080):
        self.vfs = vfs
        self.ssid = ssid
        self.port = port
        self.ap = None
        self.server_socket = None
        self.led = None
        
        # Buffer settings
        self.RECV_BUFFER = 256
        self.SEND_BUFFER = 2048
        self.MAX_CHUNK = 4096
        
        # Try to initialize LED
        try:
            self.led = machine.Pin(25, machine.Pin.OUT)
            print("DEBUG: LED initialized on pin 25")
        except Exception as e:
            print(f"DEBUG: LED not available: {e}")
        
    def setup_access_point(self):
        print("\n" + "-"*50)
        print("SETTING UP ACCESS POINT")
        print("-"*50)
        
        # First, make sure STA interface is OFF
        print("\nDEBUG: Checking STA interface..")
        try:
            sta = network.WLAN(network.STA_IF)
            if sta.active():
                print("DEBUG: STA interface is active, deactivating..")
                sta.active(False)
                utime.sleep(2)
                print("DEBUG: STA interface deactivated")
            else:
                print("DEBUG: STA interface already inactive")
        except Exception as e:
            print(f"DEBUG: STA interface check error: {e}")
        
        # Create and configure AP
        print("\nDEBUG: Creating AP interface..")
        self.ap = network.WLAN(network.AP_IF)
        
        # Make sure it's off first
        if self.ap.active():
            print("DEBUG: AP was already active, deactivating first..")
            self.ap.active(False)
            utime.sleep(2)
        
        print(f"DEBUG: Activating AP with SSID: '{self.ssid}'")
        self.ap.active(True)
        utime.sleep(2)
        
        # Try multiple configuration methods
        print("\nDEBUG: Configuring AP..")
        config_success = False
        
        # Method 1: No password (open network)
        try:
            print("DEBUG: Trying config(essid=..., password='')..")
            self.ap.config(essid=self.ssid, password='')
            config_success = True
            print("DEBUG: Config method 1 succeeded")
        except Exception as e1:
            print(f"DEBUG: Config method 1 failed: {e1}")
            
            # Method 2: Just ESSID
            try:
                print("DEBUG: Trying config(essid=...)..")
                self.ap.config(essid=self.ssid)
                config_success = True
                print("DEBUG: Config method 2 succeeded")
            except Exception as e2:
                print(f"DEBUG: Config method 2 failed: {e2}")
                
                # Method 3: With channel
                try:
                    print("DEBUG: Trying config(essid=..., channel=6)..")
                    self.ap.config(essid=self.ssid, channel=6)
                    config_success = True
                    print("DEBUG: Config method 3 succeeded")
                except Exception as e3:
                    print(f"DEBUG: Config method 3 failed: {e3}")
        
        if not config_success:
            print("WARNING: All config methods failed, but continuing anyway..")
        
        # Wait for interface to become active and stable
        print("\nDEBUG: Waiting for AP to become active...")
        max_wait = 20
        while max_wait > 0:
            if self.ap.active():
                print(f"DEBUG: AP is active (waited {20-max_wait} seconds)")
                break
            print(".", end="")
            utime.sleep(1)
            max_wait -= 1
        
        if not self.ap.active():
            print("\nERROR: Failed to activate Access Point!")
            raise RuntimeError("AP activation failed")
        
        # Extra stabilization time
        print("\nDEBUG: Allowing AP to stabilise..")
        utime.sleep(3)
        
        # Get and display configuration
        try:
            config = self.ap.ifconfig()
            print("\n" + "-"*50)
            print("ACCESS POINT ACTIVE")
            print("-"*50)
            print(f"SSID: {self.ssid}")
            print(f"IP Address: {config[0]}")
            print(f"Netmask: {config[1]}")
            print(f"Gateway: {config[2]}")
            print(f"DNS: {config[3]}")
            
            try:
                print(f"\nDEBUG: AP Status: {self.ap.status()}")
            except:
                pass
            
            try:
                mac = self.ap.config('mac')
                mac_str = ':'.join(['%02X' % b for b in mac])
                print(f"DEBUG: MAC Address: {mac_str}")
            except Exception as e:
                print(f"DEBUG: Could not get MAC: {e}")
            
            try:
                channel = self.ap.config('channel')
                print(f"DEBUG: Channel: {channel}")
            except Exception as e:
                print(f"DEBUG: Could not get channel: {e}")
            
            print("-"*50)
            
            if self.led:
                self.led.value(1)
                print("DEBUG: LED turned on")
                
        except Exception as e:
            print(f"ERROR: Could not get AP config: {e}")
            import sys
            sys.print_exception(e)
    
    def setup_tcp_server(self):
        print("\n" + "-"*50)
        print("SETTING UP TCP SERVER")
        print("-"*50)
        
        try:
            print(f"DEBUG: Creating socket on port {self.port}..")
            addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
            print(f"DEBUG: Address info: {addr}")
            
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("DEBUG: Socket created")
            
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("DEBUG: SO_REUSEADDR set")
            
            self.server_socket.bind(addr)
            print(f"DEBUG: Socket bound to {addr}")
            
            self.server_socket.listen(5)
            print("DEBUG: Socket listening (backlog=5)")
            
            print(f"\nTCP SERVER READY on port {self.port}")
            print("="*50)
            
        except Exception as e:
            print(f"ERROR: Failed to setup TCP server: {e}")
            import sys
            sys.print_exception(e)
            raise
    
    def send_with_buffer(self, conn, data, chunk_size=None):
        if chunk_size is None:
            chunk_size = self.SEND_BUFFER
        
        total_sent = 0
        data_len = len(data)
        
        while total_sent < data_len:
            chunk_end = min(total_sent + chunk_size, data_len)
            chunk = data[total_sent:chunk_end]
            
            try:
                sent = conn.send(chunk)
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent
                
                # Progress feedback for large transfers
                if total_sent % (chunk_size * 4) == 0 or total_sent == data_len:
                    progress = (total_sent / data_len) * 100
                    print(f"  Sent: {total_sent}/{data_len} bytes ({progress:.1f}%)")
                
            except OSError as e:
                print(f"ERROR: Send failed at {total_sent}/{data_len} bytes: {e}")
                raise
        
        return total_sent
    
    def recv_with_buffer(self, conn, expected_size, chunk_size=None):
        if chunk_size is None:
            chunk_size = self.RECV_BUFFER
        
        data = bytearray()
        
        while len(data) < expected_size:
            remaining = expected_size - len(data)
            to_recv = min(chunk_size, remaining)
            
            try:
                chunk = conn.recv(to_recv)
                if not chunk:
                    print(f"WARNING: Connection closed, received {len(data)}/{expected_size}")
                    break
                data.extend(chunk)
                
            except OSError as e:
                print(f"ERROR: Receive failed at {len(data)}/{expected_size} bytes: {e}")
                raise
        
        return bytes(data)
    
    def handle_list_request(self, conn):
        try:
            print("DEBUG: Processing LIST request..")
            files = self.vfs.list_files()
            response = ujson.dumps(files)
            
            # Send response with header
            header = f"OK|{len(response)}|\n"
            print(f"DEBUG: Sending header: {header.strip()}")
            conn.send(header.encode())
            
            print(f"DEBUG: Sending data: {len(response)} bytes")
            self.send_with_buffer(conn, response.encode())
            
            print(f"SUCCESS: Sent file list ({len(files)} files)")
            
        except Exception as e:
            error_msg = f"ERROR|{str(e)}\n"
            conn.send(error_msg.encode())
            print(f"ERROR: List error: {e}")
    
    def handle_info_request(self, conn, filename):
        try:
            print(f"DEBUG: Processing INFO request for: {filename}")
            
            info = self.vfs.get_file_info(filename)
            if not info:
                conn.send(b"ERROR|File not found\n")
                print(f"ERROR: File not found: {filename}")
                return
            
            response = ujson.dumps(info)
            header = f"OK|{len(response)}|\n"
            
            print(f"DEBUG: Sending info header: {header.strip()}")
            conn.send(header.encode())
            conn.send(response.encode())
            
            print(f"SUCCESS: Sent file info for {filename}")
            
        except Exception as e:
            error_msg = f"ERROR|{str(e)}\n"
            conn.send(error_msg.encode())
            print(f"ERROR: Info error: {e}")
    
    def handle_get_request(self, conn, filename, compress=True):
        try:
            print(f"DEBUG: Processing GET request for: {filename}")
            
            if not self.vfs.file_exists(filename):
                conn.send(b"ERROR|File not found\n")
                print(f"ERROR: File not found: {filename}")
                return
            
            info = self.vfs.get_file_info(filename)
            file_type = info.get('type', 'unknown')
            print(f"DEBUG: File type: {file_type}")
            
            # Read file
            print(f"DEBUG: Reading file: {filename}")
            raw_data = self.vfs.read_file(filename)
            print(f"DEBUG: Read {len(raw_data)} bytes")
            
            # Decide whether to compress
            should_compress = compress and len(raw_data) > 512
            
            if should_compress:
                print("DEBUG: Compressing..")
                compressed = RLECompressor.compress(raw_data, self.MAX_CHUNK)
                ratio = len(compressed) / len(raw_data) * 100 if len(raw_data) > 0 else 0
                print(f"DEBUG: Compressed to {len(compressed)} bytes ({ratio:.1f}%)")
                data_to_send = compressed
                compressed_size = len(compressed)
            else:
                print("DEBUG: Sending uncompressed")
                data_to_send = raw_data
                compressed_size = len(raw_data)
            
            # Send header: OK|original_size|compressed_size|file_type|
            header = f"OK|{len(raw_data)}|{compressed_size}|{file_type}|\n"
            print(f"DEBUG: Sending header: {header.strip()}")
            conn.send(header.encode())
            
            # Send data with buffering
            print(f"DEBUG: Sending {len(data_to_send)} bytes...")
            self.send_with_buffer(conn, data_to_send, self.SEND_BUFFER)
            
            print("SUCCESS: Transfer complete")
            gc.collect()
            print(f"DEBUG: Free memory: {gc.mem_free()}")
            
        except Exception as e:
            error_msg = f"ERROR|{str(e)}\n"
            try:
                conn.send(error_msg.encode())
            except:
                pass
            print(f"ERROR: Transfer error: {e}")
            import sys
            sys.print_exception(e)
    
    def handle_client_connection(self, client_socket, client_addr):
        print(f"\n{'-'*50}")
        print(f"CLIENT CONNECTED: {client_addr}")
        print(f"{'-'*50}")
        client_socket.settimeout(30.0)
        
        try:
            print("DEBUG: Waiting for request..")
            request = client_socket.recv(self.RECV_BUFFER).decode().strip()
            print(f"DEBUG: Received request: '{request}'")
            
            if request.startswith("LIST"):
                self.handle_list_request(client_socket)
                
            elif request.startswith("INFO|"):
                parts = request.split("|")
                if len(parts) >= 2:
                    filename = parts[1]
                    self.handle_info_request(client_socket, filename)
                else:
                    client_socket.send(b"ERROR|Invalid INFO format\n")
                    
            elif request.startswith("GET|"):
                parts = request.split("|")
                if len(parts) >= 2:
                    filename = parts[1]
                    compress = parts[2].lower() != 'raw' if len(parts) > 2 else True
                    self.handle_get_request(client_socket, filename, compress)
                else:
                    client_socket.send(b"ERROR|Invalid GET format\n")
                    print("ERROR: Invalid GET format")
                    
            else:
                error_msg = b"ERROR|Unknown command. Use LIST, INFO|filename, or GET|filename\n"
                client_socket.send(error_msg)
                print(f"ERROR: Unknown command: {request}")
            
        except socket.timeout:
            print(f"ERROR: Client {client_addr} timed out")
        except Exception as e:
            print(f"ERROR: Error handling client {client_addr}: {e}")
            import sys
            sys.print_exception(e)
        finally:
            try:
                client_socket.close()
                print(f"DEBUG: Client socket closed")
            except:
                pass
            print(f"CLIENT DISCONNECTED: {client_addr}\n")
    
    def run(self):
        print("\n" + "-"*50)
        print("FILE SERVER STARTING")
        print("-"*50)
        
        self.setup_access_point()
        self.setup_tcp_server()
        
        print("\n" + "-"*50)
        print("SERVER READY - WAITING FOR CLIENTS")
        print("-"*50)
        print(f"\nInstructions for client:")
        print(f"1. Connect to WiFi: '{self.ssid}' (no password)")
        print(f"2. Client will connect to: 192.168.4.1:{self.port}")
        print(f"\nSupported commands:")
        print(f"  LIST - Get file listing")
        print(f"  INFO|filename - Get file metadata")
        print(f"  GET|filename - Download file (compressed)")
        print(f"  GET|filename|raw - Download file (uncompressed)")
        print("\nListening for connections..\n")
        
        try:
            while True:
                try:
                    print("DEBUG: Waiting for client connection...")
                    client_socket, client_addr = self.server_socket.accept()
                    self.handle_client_connection(client_socket, client_addr)
                    gc.collect()
                    print(f"DEBUG: Memory collected, free: {gc.mem_free()}")
                    
                except KeyboardInterrupt:
                    print("\n\nSERVER SHUTDOWN REQUESTED")
                    break
                except Exception as e:
                    print(f"ERROR: Server error: {e}")
                    import sys
                    sys.print_exception(e)
                    utime.sleep(1)
        finally:
            self.cleanup()
    
    def cleanup(self):
        print("\nDEBUG: Cleaning up..")
        if self.server_socket:
            try:
                self.server_socket.close()
                print("DEBUG: Server socket closed")
            except:
                pass
        if self.ap:
            self.ap.active(False)
            print("DEBUG: AP deactivated")
        if self.led:
            self.led.value(0)
            print("DEBUG: LED turned off")
        print("Server cleanup completed")


def main():
    print("\n" + "-"*70)
    print(" "*20 + "FILE SERVER INITIALIZATION")
    print("-"*70)
    
    # Print system info
    try:
        import sys
        print(f"\nSystem Information:")
        print(f"  Platform: {sys.platform}")
        print(f"  Version: {sys.version}")
        print(f"  Free memory: {gc.mem_free()} bytes")
    except:
        pass
    
    # Initialize SD card
    try:
        print("\n" + "-"*50)
        print("Mounting SD card..")
        print("-"*50)
        
        cs = machine.Pin(1, machine.Pin.OUT)
        print("DEBUG: CS pin initialised (Pin 1)")
        
        spi = machine.SPI(0,
                          baudrate=1000000,
                          polarity=0,
                          phase=0,
                          bits=8,
                          firstbit=machine.SPI.MSB,
                          sck=machine.Pin(2),
                          mosi=machine.Pin(3),
                          miso=machine.Pin(4))
        print("DEBUG: SPI initialised (SPI0, 1MHz)")
        
        sd = sdcard.SDCard(spi, cs)
        print("DEBUG: SDCard object created")
        
        vfs_fat = uos.VfsFat(sd)
        print("DEBUG: VfsFat created")
        
        uos.mount(vfs_fat, "/sd")
        print("SUCCESS: SD card mounted at /sd")
        
    except Exception as e:
        print(f"ERROR: SD card error: {e}")
        import sys
        sys.print_exception(e)
        raise
    
    # Create VFS wrapper
    print("\nDEBUG: Creating VFS wrapper..")
    vfs = SimpleVFS("/sd")
    
    # Check for existing files
    files = vfs.list_files()
    if not files:
        print("\n" + "-"*50)
        print("No files found, creating test files..")
        print("-"*50)
        
        # Create test text file
        test_text = "Hello from Pico File Server!\nThis is a test text file.\nLine 3\nLine 4"
        vfs.create_file("readme.txt", test_text, file_type='text')
        
        # Create test image (320x240 RGB565 for DisplayPack 2.0)
        test_image = bytearray()
        for i in range(320 * 240):
            val = (i % 256)
            test_image.append(val)
            test_image.append(val)
        vfs.create_file("test.img", bytes(test_image), file_type='image')
        
        print("SUCCESS: Test files created")
    else:
        print(f"\n" + "-"*50)
        print(f"Found {len(files)} existing file(s):")
        print("-"*50)
        for f in files:
            print(f"  - {f['name']} ({f['size']} bytes, type: {f['type']})")
    
    # Start server
    print("\n" + "-"*50)
    print("Starting file server..")
    print("-"*50)
    server = FileServer(vfs, ssid="PicoFiles")
    server.run()

if __name__ == "__main__":
    main()
