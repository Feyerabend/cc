import network
import socket
import utime
import ujson
import gc

# Try to import display, but make it optional
try:
    from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
    DISPLAY_AVAILABLE = True
    print("Display library loaded")
except ImportError as e:
    print(f"Display not available: {e}")
    DISPLAY_AVAILABLE = False


class RLECompressor:    
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


class FileDisplay:
    def __init__(self):
        if not DISPLAY_AVAILABLE:
            self.display = None
            print("Display disabled - console only mode")
            return
            
        try:
            self.display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
            self.width = self.display.get_bounds()[0]
            self.height = self.display.get_bounds()[1]
            print(f"Display initialised: {self.width}x{self.height}")
        except Exception as e:
            print(f"Display init failed: {e}")
            self.display = None
        
    def clear(self, color=(0, 0, 0)):
        if not self.display:
            return
        try:
            pen = self.display.create_pen(*color)
            self.display.set_pen(pen)
            self.display.clear()
            self.display.update()
        except Exception as e:
            print(f"Clear failed: {e}")
        
    def show_text(self, text, x=10, y=10, scale=2, color=(255, 255, 255)):
        print(f"Display: {text}")
        if not self.display:
            return
        try:
            self.display.set_pen(self.display.create_pen(*color))
            self.display.text(text, x, y, scale=scale)
            self.display.update()
        except Exception as e:
            print(f"Show text failed: {e}")
    
    def show_text_multiline(self, lines, start_y=10, line_height=20, scale=2):
        if not self.display:
            for line in lines:
                print(f"  {line}")
            return
        
        try:
            self.clear()
            y = start_y
            for line in lines:
                if y + line_height > self.height:
                    break
                self.display.set_pen(self.display.create_pen(255, 255, 255))
                self.display.text(line, 10, y, scale=scale)
                y += line_height
            self.display.update()
        except Exception as e:
            print(f"Multiline text failed: {e}")
        
    def display_image(self, image_data):
        if not self.display:
            print(f"Would display {len(image_data)} bytes")
            return
            
        expected_size = self.width * self.height * 2
        if len(image_data) != expected_size:
            print(f"Warning: Image size mismatch!")
            print(f"Expected: {expected_size}, Got: {len(image_data)}")
        
        try:
            pixels_to_draw = min(self.height, len(image_data) // (self.width * 2))
            for y in range(pixels_to_draw):
                for x in range(self.width):
                    idx = (y * self.width + x) * 2
                    if idx + 1 < len(image_data):
                        pixel = (image_data[idx] << 8) | image_data[idx + 1]
                        r = ((pixel >> 11) & 0x1F) << 3
                        g = ((pixel >> 5) & 0x3F) << 2
                        b = (pixel & 0x1F) << 3
                        
                        pen = self.display.create_pen(r, g, b)
                        self.display.set_pen(pen)
                        self.display.pixel(x, y)
            
            self.display.update()
            print("Image displayed")
        except Exception as e:
            print(f"Display image failed: {e}")


class FileClient:
    def __init__(self, server_ssid, server_ip, server_port=8080):
        self.server_ssid = server_ssid
        self.server_ip = server_ip
        self.server_port = server_port
        self.wlan = None
        self.led = None
        
        # Buffer settings
        self.RECV_BUFFER = 2048
        self.SEND_BUFFER = 256
        
        # Try init LED
        try:
            from machine import Pin
            self.led = Pin(25, Pin.OUT)
            print("DEBUG: LED initialized")
        except Exception as e:
            print(f"DEBUG: LED not available: {e}")
        
    def connect_to_network(self):
        print("\n" + "="*50)
        print("INIT WIFI CLIENT")
        print("="*50)
        
        # First, make sure AP interface is OFF
        print("\nDEBUG: Checking AP interface..")
        try:
            ap = network.WLAN(network.AP_IF)
            if ap.active():
                print("DEBUG: AP interface is active, deactivating..")
                ap.active(False)
                utime.sleep(2)
                print("DEBUG: AP interface deactivated")
            else:
                print("DEBUG: AP interface already inactive")
        except Exception as e:
            print(f"DEBUG: AP interface check error: {e}")
        
        # Make sure STA WiFi is off first
        print("\nDEBUG: Resetting STA interface..")
        try:
            self.wlan = network.WLAN(network.STA_IF)
            if self.wlan.active():
                print("DEBUG: STA was active, deactivating..")
                self.wlan.active(False)
                utime.sleep(2)
                print("DEBUG: STA deactivated")
        except Exception as e:
            print(f"DEBUG: Error during reset: {e}")
        
        # Now activate it fresh
        print("\nDEBUG: Activating STA interface..")
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        # Wait for WiFi to actually become active
        print("DEBUG: Waiting for interface to become active..")
        max_wait = 15
        wait_count = 0
        while wait_count < max_wait and not self.wlan.active():
            print(".", end="")
            utime.sleep(0.5)
            wait_count += 1
        
        if not self.wlan.active():
            print("\nERROR: Failed to activate WiFi interface!")
            return False
        
        print(f"\nSUCCESS: WiFi interface active (took {wait_count * 0.5:.1f}s)")
        
        # Extra stabilization time
        print("DEBUG: Allowing interface to stabilise..")
        utime.sleep(3)
        
        # Try to get interface info
        try:
            mac = self.wlan.config('mac')
            mac_str = ':'.join(['%02X' % b for b in mac])
            print(f"DEBUG: MAC Address: {mac_str}")
        except Exception as e:
            print(f"DEBUG: Could not get MAC: {e}")
        
        # Scan for networks
        print(f"\nDEBUG: Scanning for networks (this may take 5-10 seconds)..")
        utime.sleep(2)
        
        try:
            networks = self.wlan.scan()
            print(f"\nDEBUG: Scan complete, found {len(networks)} networks")
            
            if networks and len(networks) > 0:
                print("\nAvailable networks:")
                found_target = False
                for net in networks:
                    try:
                        ssid = net[0].decode('utf-8') if isinstance(net[0], bytes) else net[0]
                        rssi = net[3]
                        channel = net[2] if len(net) > 2 else '?'
                        security = net[4] if len(net) > 4 else '?'
                        
                        marker = " <-- TARGET" if ssid == self.server_ssid else ""
                        print(f"  - '{ssid}' (RSSI: {rssi}dBm, Ch: {channel}, Sec: {security}){marker}")
                        
                        if ssid == self.server_ssid:
                            found_target = True
                    except Exception as e:
                        print(f"  - <parsing error: {e}>")
                
                if found_target:
                    print(f"\nSUCCESS: Target network '{self.server_ssid}' found in scan!")
                else:
                    print(f"\nWARNING: Target network '{self.server_ssid}' NOT found in scan!")
                    print("This might be OK - will try connecting anyway..")
            else:
                print("WARNING: Scan returned empty results")
                
        except Exception as e:
            print(f"DEBUG: Scan failed: {e}")
            print("This is OK on some boards - will try connecting anyway..")
            import sys
            sys.print_exception(e)
        
        # Disconnect if already connected
        print(f"\nDEBUG: Checking current connection status..")
        if self.wlan.isconnected():
            print("DEBUG: Already connected to a network, disconnecting..")
            self.wlan.disconnect()
            utime.sleep(2)
            print("DEBUG: Disconnected")
        
        # Try to connect
        print(f"\n" + "="*50)
        print(f"CONNECTING TO: '{self.server_ssid}'")
        print("="*50)
        
        connection_success = False
        
        # Try Method 1: Empty string password (most compatible for open networks)
        try:
            print("\nDEBUG: Method 1 - Trying connect(ssid, '')..")
            self.wlan.connect(self.server_ssid, '')
            connection_success = True
            print("DEBUG: Connection request accepted")
        except Exception as e1:
            print(f"DEBUG: Method 1 failed: {e1}")
            
            # Try Method 2: SSID only
            try:
                print("\nDEBUG: Method 2 - Trying connect(ssid)..")
                self.wlan.connect(self.server_ssid)
                connection_success = True
                print("DEBUG: Connection request accepted")
            except Exception as e2:
                print(f"DEBUG: Method 2 failed: {e2}")
                
                # Try Method 3: None as password
                try:
                    print("\nDEBUG: Method 3 - Trying connect(ssid, None)..")
                    self.wlan.connect(self.server_ssid, None)
                    connection_success = True
                    print("DEBUG: Connection request accepted")
                except Exception as e3:
                    print(f"DEBUG: Method 3 failed: {e3}")
        
        if not connection_success:
            print("\nERROR: All connection methods failed!")
            return False
        
        # Wait for connection with detailed status updates
        print("\nDEBUG: Waiting for connection..")
        max_wait = 40
        wait_count = 0
        last_status = None
        
        status_names = {
            0: "STAT_IDLE",
            1: "STAT_CONNECTING", 
            2: "STAT_WRONG_PASSWORD",
            3: "STAT_NO_AP_FOUND",
            -1: "STAT_CONNECT_FAIL",
            -2: "STAT_CONNECT_FAIL",
            -3: "STAT_GOT_IP"
        }
        
        while wait_count < max_wait:
            status = self.wlan.status()
            
            if status != last_status:
                status_str = status_names.get(status, f"UNKNOWN({status})")
                print(f"\nDEBUG: Status changed to: {status_str}")
                last_status = status
            
            if self.wlan.isconnected():
                print(f"\n{'-'*50}")
                print("CONNECTION SUCCESSFUL!")
                print("-"*50)
                
                try:
                    config = self.wlan.ifconfig()
                    print(f"\nNetwork Configuration:")
                    print(f"  IP Address: {config[0]}")
                    print(f"  Netmask: {config[1]}")
                    print(f"  Gateway: {config[2]}")
                    print(f"  DNS Server: {config[3]}")
                    print(f"\nConnection time: {wait_count}s")
                except Exception as e:
                    print(f"DEBUG: Could not get config: {e}")
                
                if self.led:
                    self.led.value(1)
                    print("DEBUG: LED turned on")
                
                return True
            
            if status in [2, 3, -1, -2]:
                status_str = status_names.get(status, f"UNKNOWN({status})")
                print(f"\nERROR: Connection failed with status: {status_str}")
                return False
            
            if wait_count % 2 == 0:
                print(".", end="")
            
            utime.sleep(1)
            wait_count += 1
        
        final_status = self.wlan.status()
        final_status_str = status_names.get(final_status, f"UNKNOWN({final_status})")
        print(f"\n\nERROR: Connection timeout after {max_wait}s")
        print(f"Final status: {final_status_str}")
        
        return False
    
    def recv_with_buffer(self, sock, expected_size, show_progress=True):
        """Receive data in chunks with proper buffering"""
        data = bytearray()
        last_print = 0
        
        while len(data) < expected_size:
            remaining = expected_size - len(data)
            to_recv = min(self.RECV_BUFFER, remaining)
            
            try:
                chunk = sock.recv(to_recv)
                if not chunk:
                    print(f"\nWARNING: Connection closed, received {len(data)}/{expected_size}")
                    break
                data.extend(chunk)
                
                # Progress indicator
                if show_progress and (len(data) - last_print >= 10240 or len(data) == expected_size):
                    progress = len(data) / expected_size * 100
                    print(f"  Progress: {len(data)}/{expected_size} bytes ({progress:.1f}%)")
                    last_print = len(data)
                    
            except OSError as e:
                print(f"\nERROR: Receive failed at {len(data)}/{expected_size} bytes: {e}")
                raise
        
        return bytes(data)
        
    def list_files(self):
        print("\n" + "-"*50)
        print("LISTING FILES")
        print("-"*50)
        sock = None
        try:
            print(f"\nDEBUG: Creating socket..")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            print(f"DEBUG: Connecting to {self.server_ip}:{self.server_port}...")
            sock.connect((self.server_ip, self.server_port))
            print("SUCCESS: Socket connected")
            
            # Send LIST request
            print("DEBUG: Sending 'LIST' command..")
            sock.send(b"LIST\n")
            
            # Receive response header
            print("DEBUG: Waiting for response header..")
            header = b""
            timeout_count = 0
            while b"\n" not in header and timeout_count < 100:
                try:
                    chunk = sock.recv(1)
                    if not chunk:
                        break
                    header += chunk
                except:
                    timeout_count += 1
                    utime.sleep(0.1)
            
            if not header:
                print("ERROR: No response from server")
                return []
            
            header = header.decode().strip()
            print(f"DEBUG: Received header: '{header}'")
            
            if not header.startswith("OK|"):
                print(f"ERROR: Server returned: {header}")
                return []
            
            # Parse header
            parts = header.split("|")
            if len(parts) < 2:
                print("ERROR: Invalid header format")
                return []
            
            data_size = int(parts[1])
            print(f"DEBUG: Expecting {data_size} bytes of JSON data")
            
            # Receive JSON data with buffering
            print("DEBUG: Receiving data..")
            data = self.recv_with_buffer(sock, data_size, show_progress=False)
            
            print(f"DEBUG: Received {len(data)} bytes total")
            files = ujson.loads(data.decode())
            print(f"\nSUCCESS: Parsed {len(files)} file(s)")
            return files
            
        except Exception as e:
            print(f"ERROR: List failed: {e}")
            import sys
            sys.print_exception(e)
            return []
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

    # metadata request
    def get_file_info(self, filename):
        print(f"\n" + "-"*50)
        print(f"GETTING INFO: {filename}")
        print("-"*50)
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            print(f"DEBUG: Connecting to {self.server_ip}:{self.server_port}...")
            sock.connect((self.server_ip, self.server_port))
            
            # Send INFO request
            request = f"INFO|{filename}\n"
            print(f"DEBUG: Sending request: {request.strip()}")
            sock.send(request.encode())
            
            # Receive header
            header = b""
            while b"\n" not in header:
                chunk = sock.recv(1)
                if not chunk:
                    return None
                header += chunk
            
            header = header.decode().strip()
            
            if not header.startswith("OK|"):
                print(f"ERROR: {header}")
                return None
            
            # Parse and receive data
            parts = header.split("|")
            data_size = int(parts[1])
            
            data = self.recv_with_buffer(sock, data_size, show_progress=False)
            info = ujson.loads(data.decode())
            
            print(f"SUCCESS: Got file info")
            return info
            
        except Exception as e:
            print(f"ERROR: Info request failed: {e}")
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def get_file(self, filename, raw=False):
        print(f"\n" + "-"*50)
        print(f"DOWNLOADING: {filename}")
        print("-"*50)
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30.0)
            
            print(f"DEBUG: Connecting to {self.server_ip}:{self.server_port}...")
            sock.connect((self.server_ip, self.server_port))
            print("SUCCESS: Connected")
            
            # Send GET request
            request = f"GET|{filename}|{'raw' if raw else 'compress'}\n"
            print(f"DEBUG: Sending request: {request.strip()}")
            sock.send(request.encode())
            
            # Receive header
            print("DEBUG: Waiting for response header..")
            header = b""
            while b"\n" not in header:
                chunk = sock.recv(1)
                if not chunk:
                    print("ERROR: Connection closed while reading header")
                    return None, None
                header += chunk
            
            header = header.decode().strip()
            print(f"DEBUG: Received header: '{header}'")
            
            if not header.startswith("OK|"):
                print(f"ERROR: Server responded: {header}")
                return None, None
            
            # Parse header: OK|original_size|compressed_size|file_type|
            parts = header.split("|")
            if len(parts) < 4:
                print("ERROR: Invalid header format")
                return None, None
                
            original_size = int(parts[1])
            data_size = int(parts[2])
            file_type = parts[3]
            
            is_compressed = data_size != original_size
            
            print(f"\nFile Info:")
            print(f"  Type: {file_type}")
            print(f"  Original size: {original_size} bytes")
            if is_compressed:
                print(f"  Compressed size: {data_size} bytes")
                print(f"  Compression ratio: {data_size/original_size*100:.1f}%")
            
            # Receive data with buffering
            print(f"\nDEBUG: Downloading {data_size} bytes...")
            file_data = self.recv_with_buffer(sock, data_size)
            
            if len(file_data) != data_size:
                print(f"\nWARNING: Size mismatch! Expected {data_size}, got {len(file_data)}")
            else:
                print(f"\nSUCCESS: Download complete")
            
            # Decompress if needed
            if is_compressed:
                print("\nDEBUG: Decompressing..")
                file_data = RLECompressor.decompress(file_data)
                print(f"DEBUG: Decompressed to {len(file_data)} bytes")
                
                if len(file_data) != original_size:
                    print(f"WARNING: Decompressed size mismatch!")
            
            gc.collect()
            print(f"DEBUG: Free memory: {gc.mem_free()}")
            
            return file_data, file_type
            
        except Exception as e:
            print(f"\nERROR: Download failed: {e}")
            import sys
            sys.print_exception(e)
            return None, None
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def cleanup(self):
        print("\nDEBUG: Cleaning up client..")
        if self.led:
            self.led.value(0)
        print("Client cleanup completed")


def main():
    print("\n" + "-"*70)
    print(" "*22 + "FILE CLIENT STARTING")
    print("-"*70)
    
    # System info
    try:
        import sys
        print(f"\nSystem Information:")
        print(f"  Platform: {sys.platform}")
        print(f"  Version: {sys.version}")
        print(f"  Free memory: {gc.mem_free()} bytes")
    except Exception as e:
        print(f"Could not get system info: {e}")
    
    # Configuration - default values
    SERVER_SSID = "PicoFiles"
    SERVER_IP = "192.168.4.1"
    SERVER_PORT = 8080
    
    print(f"\nConfiguration:")
    print(f"  Server SSID: '{SERVER_SSID}'")
    print(f"  Server IP: {SERVER_IP}")
    print(f"  Server Port: {SERVER_PORT}")
    
    # Initialize display (optional)
    print("\n" + "-"*50)
    display = None
    try:
        display = FileDisplay()
    except Exception as e:
        print(f"Display init error: {e}")
    
    # Create client
    print("-"*50)
    client = FileClient(
        server_ssid=SERVER_SSID,
        server_ip=SERVER_IP,
        server_port=SERVER_PORT
    )
    
    try:
        if display:
            display.show_text("Connecting..", 10, 100)
        
        # Connect to WiFi
        if not client.connect_to_network():
            print("\n" + "-"*50)
            print("WIFI CONNECTION FAILED")
            print("-"*50)
            if display:
                display.show_text("WiFi Failed", 10, 100)
            return
        
        if display:
            display.show_text("Connected!", 10, 100)
        
        print("\nDEBUG: Waiting 2 seconds before requesting data..")
        utime.sleep(2)
        
        # List available files
        if display:
            display.show_text("Listing..", 10, 100)
        
        files = client.list_files()
        
        if files:
            print(f"\n" + "-"*50)
            print(f"Available Files: {len(files)}")
            print("-"*50)
            
            # Display file list
            if display:
                lines = ["Files:"]
                for i, f in enumerate(files[:5]):  # Show first 5
                    lines.append(f"{i+1}. {f['name']}")
                    lines.append(f"   {f['size']}b {f['type']}")
                display.show_text_multiline(lines, start_y=10, line_height=18, scale=1)
                utime.sleep(3)
            
            for f in files:
                print(f"  - {f['name']} ({f['size']} bytes, type: {f['type']})")
            
            # Process first file based on type
            if files:
                file = files[0]
                filename = file['name']
                file_type = file['type']
                
                print(f"\n" + "-"*50)
                print(f"Processing: {filename} (type: {file_type})")
                print("-"*50)
                
                if display:
                    display.clear()
                    display.show_text(f"Loading..", 10, 100)
                
                file_data, ftype = client.get_file(filename)
                
                if file_data:
                    print("\n" + "-"*50)
                    print("SUCCESS - FILE DOWNLOADED")
                    print("-"*50)
                    
                    # Handle based on file type
                    if ftype == 'text':
                        print("\nText file content:")
                        print("-" * 40)
                        try:
                            text = file_data.decode('utf-8')
                            print(text)
                            
                            if display:
                                display.clear()
                                lines = text.split('\n')[:10]  # First 10 lines
                                display.show_text_multiline(lines, start_y=10, line_height=20, scale=1)
                        except Exception as e:
                            print(f"Could not decode text: {e}")
                        print("-" * 40)
                    
                    elif ftype == 'image':
                        print("\nImage file received")
                        if display:
                            display.clear()
                            display.display_image(file_data)
                            print("Image displayed on screen!")
                    
                    else:
                        print(f"\nFile downloaded ({len(file_data)} bytes)")
                        print(f"First 32 bytes: {file_data[:32]}")
                        if display:
                            display.show_text(f"Downloaded\n{len(file_data)}b", 10, 100)
                else:
                    print("\n" + "-"*50)
                    print("DOWNLOAD FAILED")
                    print("-"*50)
                    if display:
                        display.show_text("Failed", 10, 100)
        else:
            print("\n" + "-"*50)
            print("NO FILES FOUND")
            print("-"*50)
            if display:
                display.show_text("No files", 10, 100)
        
        print("\n" + "-"*70)
        print(" "*24 + "CLIENT FINISHED")
        print("-"*70)
        
        gc.collect()
        print(f"\nFinal free memory: {gc.mem_free()} bytes")
            
    except Exception as e:
        print(f"\n" + "-"*50)
        print("FATAL ERROR")
        print("-"*50)
        print(f"Error: {e}")
        import sys
        sys.print_exception(e)
        if display:
            display.clear()
            display.show_text("Error!", 10, 100)
    finally:
        client.cleanup()

if __name__ == "__main__":
    main()
