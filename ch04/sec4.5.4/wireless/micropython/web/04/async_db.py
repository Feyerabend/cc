# Async version of REST database server
import network
import socket
import time
import json
import os
import machine
import sdcard
import uos
import uselect
import gc

# Access Point Config
AP_SSID = "PicoDatabase"
AP_PASSWORD = None

# Global state
log_buffer = []
max_log_lines = 50
connection_count = 0
active_connections = []

# LED for database access indication
led = machine.Pin(25, machine.Pin.OUT)  # Onboard LED (regular RPI Pico)

def blink_led():
    led.on()
    time.sleep_ms(100)
    led.off()

def log(message, level="INFO"):
    global log_buffer, max_log_lines
    timestamp = time.ticks_ms() // 1000
    log_entry = {"timestamp": timestamp, "level": level, "message": message}
    print(f"[{level}] {message}")
    
    log_buffer.append(log_entry)
    if len(log_buffer) > max_log_lines:
        log_buffer.pop(0)

class AsyncMiniDB: # non-blocking
    def __init__(self, base="/sd", flush_every=5, auto_commit_ms=30000):
        self.base = base if base.endswith("/") else base + "/"
        self.flush_every = max(1, flush_every)
        self.buffers = {}
        self.last_commit = time.ticks_ms()
        self.auto_commit_interval = auto_commit_ms
        
        # Init SD card
        try:
            cs = machine.Pin(1, machine.Pin.OUT)
            spi = machine.SPI(0,
                            baudrate=1000000,
                            polarity=0,
                            phase=0,
                            bits=8,
                            firstbit=machine.SPI.MSB,
                            sck=machine.Pin(2),
                            mosi=machine.Pin(3),
                            miso=machine.Pin(4))
            
            sd = sdcard.SDCard(spi, cs)
            vfs = uos.VfsFat(sd)
            uos.mount(vfs, "/sd")
            log("SD card mounted successfully")
        except Exception as e:
            raise RuntimeError(f"SD card init failed: {e}")

        try:
            os.listdir(self.base)
        except OSError:
            os.mkdir(self.base)

    def _path(self, name):
        return self.base + name + ".csv"

    def needs_auto_commit(self):
        if time.ticks_diff(time.ticks_ms(), self.last_commit) > self.auto_commit_interval:
            return any(len(buffer) > 0 for buffer in self.buffers.values())
        return False

    def auto_commit_all(self):
        committed_tables = []
        for table_name, buffer in self.buffers.items():
            if buffer:
                if self.commit(table_name):
                    committed_tables.append(table_name)
        
        if committed_tables:
            log(f"Auto-committed: {', '.join(committed_tables)}")
            blink_led()
        
        self.last_commit = time.ticks_ms()
        return len(committed_tables)

    # Rest of the database methods remain the same..
    def create_table(self, name, fields):
        blink_led()
        try:
            with open(self._path(name), "w") as f:
                f.write(",".join(fields) + "\n")
                f.flush()
            self.buffers[name] = []
            log(f"Table '{name}' created")
            return True
        except OSError as e:
            log(f"Create table error: {e}", "ERROR")
            return False

    def insert(self, name, row):
        blink_led()
        if not isinstance(row, (list, tuple)):
            return False
        if name not in self.buffers:
            self.buffers[name] = []
        
        self.buffers[name].append(row)
        
        # Auto-flush if buffer gets large
        if len(self.buffers[name]) >= self.flush_every:
            return self.commit(name)
        return True

    def commit(self, name):
        blink_led()
        if name not in self.buffers or not self.buffers[name]:
            return False
        try:
            with open(self._path(name), "a") as f:
                for row in self.buffers[name]:
                    f.write(",".join(str(x) for x in row) + "\n")
                f.flush()
            count = len(self.buffers[name])
            self.buffers[name] = []
            log(f"Committed {count} rows to {name}")
            return True
        except OSError as e:
            log(f"Commit error: {e}", "ERROR")
            return False

    def all_rows(self, name):
        blink_led()
        rows = []
        try:
            with open(self._path(name), "r") as f:
                header = f.readline().strip().split(",")
                if not header or header == ['']:
                    return rows
                for line in f:
                    values = line.strip().split(",")
                    if values == [''] or len(values) != len(header):
                        continue
                    rows.append(dict(zip(header, values)))
        except OSError:
            pass
        return rows

    def select(self, name, where=None):
        blink_led()
        results = []
        for row in self.all_rows(name):
            if where:
                if all(row.get(k) == str(v) for k, v in where.items()):
                    results.append(row)
            else:
                results.append(row)
        return results

    def list_tables(self):
        blink_led()
        tables = []
        try:
            for file in os.listdir(self.base):
                if file.endswith('.csv'):
                    tables.append(file[:-4])
        except OSError:
            pass
        return tables

    def table_info(self, name):
        blink_led()
        try:
            with open(self._path(name), "r") as f:
                header = f.readline().strip().split(",")
                row_count = sum(1 for line in f if line.strip())
                return {"fields": header, "row_count": row_count}
        except OSError:
            return None


class AsyncConnection:
    def __init__(self, client_socket, client_addr, connection_id):
        self.socket = client_socket
        self.addr = client_addr
        self.id = connection_id
        self.buffer = b""
        self.response_sent = False
        
        # Set socket to non-blocking
        self.socket.setblocking(False)
        
    def receive_data(self):
        try:
            data = self.socket.recv(1024)
            if data:
                self.buffer += data
                return True
            else:
                # Client closed connection
                return False
        except OSError as e:
            if e.args[0] == 11:  # EAGAIN - no data available
                return True
            else:
                # Real error
                return False
    
    def has_complete_request(self):
        return b"\r\n\r\n" in self.buffer
    
    def process_request(self, db):
        if not self.has_complete_request():
            return False
            
        try:
            request_data = self.buffer.decode('utf-8')
            method, path, params, json_body = parse_request(request_data)
            
            if method and path:
                log(f"#{self.id} {method} {path[:20]}")
                response = handle_rest_request(method, path, params, json_body, db)
                self.socket.send(response.encode('utf-8'))
                self.response_sent = True
                return True
        except Exception as e:
            log(f"Request processing error: {e}", "ERROR")
            
        return False
    
    def close(self):
        try:
            self.socket.close()
        except:
            pass

def create_access_point():
    log("Setting up Access Point")
    
    sta = network.WLAN(network.STA_IF)
    sta.active(False)
    
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(1)
    
    ap.active(True)
    time.sleep(2)
    
    ap.config(essid=AP_SSID)
    
    timeout = 10
    while not ap.active() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        log(f"AP starting .. {timeout}s")
    
    if not ap.active():
        log("AP activation FAILED", "ERROR")
        return None
    
    config = ap.ifconfig()
    ip = config[0]
    
    log(f"AP Ready: {ip}")
    return ip

def create_response(status_code, data=None, message=None):
    response_data = {
        "status": status_code,
        "timestamp": time.ticks_ms(),
        "connection_count": connection_count,
        "active_connections": len(active_connections)
    }
    
    if data is not None:
        response_data["data"] = data
    if message:
        response_data["message"] = message
    
    json_response = json.dumps(response_data)
    
    status_text = {
        200: "OK", 201: "Created", 400: "Bad Request", 
        404: "Not Found", 405: "Method Not Allowed", 500: "Internal Server Error"
    }.get(status_code, "Unknown")
    
    headers = f"HTTP/1.1 {status_code} {status_text}\r\n"
    headers += "Content-Type: application/json\r\n"
    headers += "Access-Control-Allow-Origin: *\r\n"
    headers += f"Content-Length: {len(json_response)}\r\n"
    headers += "Connection: close\r\n\r\n"
    
    return headers + json_response

def handle_rest_request(method, path, params, json_body, db):
    # GET /api/tables
    if method == "GET" and path == "/api/tables":
        tables = db.list_tables()
        return create_response(200, {"tables": tables})
    
    # POST /api/tables/{name}
    elif method == "POST" and path.startswith("/api/tables/"):
        table_name = path.split("/")[-1]
        fields = json_body.get("fields", [])
        
        if not fields:
            return create_response(400, message="Fields required")
        
        if db.create_table(table_name, fields):
            return create_response(201, message=f"Table '{table_name}' created")
        else:
            return create_response(500, message="Failed to create table")
    
    # GET /api/tables/{name}
    elif method == "GET" and path.startswith("/api/tables/"):
        table_name = path.split("/")[-1]
        
        info = db.table_info(table_name)
        if info is None:
            return create_response(404, message=f"Table '{table_name}' not found")
        
        where = {}
        for key, value in params.items():
            if key.startswith("where_"):
                field = key[6:]
                where[field] = value
        
        rows = db.select(table_name, where if where else None)
        
        return create_response(200, {
            "table": table_name,
            "info": info,
            "rows": rows,
            "count": len(rows)
        })
    
    # POST /api/tables/{name}/rows
    elif method == "POST" and path.startswith("/api/tables/") and path.endswith("/rows"):
        table_name = path.split("/")[-2]
        row_data = json_body.get("row", [])
        
        if not row_data:
            return create_response(400, message="Row data required")
        
        if db.insert(table_name, row_data):
            return create_response(201, message="Row inserted")
        else:
            return create_response(500, message="Failed to insert row")
    
    # POST /api/tables/{name}/commit
    elif method == "POST" and path.startswith("/api/tables/") and path.endswith("/commit"):
        table_name = path.split("/")[-2]
        
        if db.commit(table_name):
            return create_response(200, message="Data committed")
        else:
            return create_response(404, message="Nothing to commit")
    
    # GET /api/logs
    elif method == "GET" and path == "/api/logs":
        return create_response(200, {
            "logs": log_buffer,
            "count": len(log_buffer),
            "connections": connection_count,
            "uptime": time.ticks_ms() // 1000,
            "active": len(active_connections),
            "memory_free": gc.mem_free()
        })
    
    # GET /api/status
    elif method == "GET" and path == "/api/status":
        return create_response(200, {
            "uptime": time.ticks_ms(),
            "connections": connection_count,
            "active": len(active_connections),
            "ap_ssid": AP_SSID,
            "tables": len(db.list_tables()),
            "sd_mounted": True,
            "memory_free": gc.mem_free(),
            "buffered_rows": sum(len(buf) for buf in db.buffers.values())
        })
    
    # Simple web interface
    elif method == "GET" and path == "/":
        html = """<!DOCTYPE html>
<html><head><title>Pico Async Database</title></head><body>
<h2>Pico Async Database</h2>
<div>
<h3>Status</h3>
<button onclick="refreshStatus()">Refresh</button>
<div id="status"></div>
<textarea id="logs" rows="12" cols="90" readonly></textarea>
</div>
<div>
<h3>Tables</h3>
<input id="tableName" placeholder="table name" value="sensors">
<button onclick="createTable()">Create</button>
<button onclick="listTables()">List</button>
<button onclick="getTable()">View</button>
<div id="result"></div>
</div>
<div>
<h3>Data Operations</h3>
<input id="insertTable" placeholder="table" value="sensors">
<input id="insertData" placeholder='["temp","22.5","1234567890"]' value='["humidity","65.2","1234567891"]' size="40">
<button onclick="insertRow()">Insert</button>
<button onclick="commit()">Commit</button>
<button onclick="bulkInsert()">Bulk Test</button>
</div>
<script>
function refreshStatus() {
    fetch('/api/status').then(r=>r.json()).then(d=>{
        const uptime = Math.floor(d.data.uptime/1000);
        document.getElementById('status').innerHTML = 
            'Uptime: '+uptime+'s | Active: '+d.data.active+' | Total: '+d.data.connections+
            ' | Tables: '+d.data.tables+' | Memory: '+(d.data.memory_free/1024).toFixed(1)+'KB'+
            ' | Buffered: '+d.data.buffered_rows+' rows';
    });
    fetch('/api/logs').then(r=>r.json()).then(d=>{
        document.getElementById('logs').value = d.data.logs.slice(-20).map(l=>
            new Date(l.timestamp*1000).toLocaleTimeString()+' '+l.level+' '+l.message
        ).join('\\n');
        document.getElementById('logs').scrollTop = document.getElementById('logs').scrollHeight;
    });
}
function createTable() {
    fetch('/api/tables/'+document.getElementById('tableName').value, {
        method:'POST', headers:{'Content-Type':'application/json'}, 
        body:JSON.stringify({fields:['sensor','value','timestamp']})
    }).then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d,null,2));
}
function listTables() {
    fetch('/api/tables').then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d,null,2));
}
function getTable() {
    fetch('/api/tables/'+document.getElementById('tableName').value).then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d,null,2));
}
function insertRow() {
    const table = document.getElementById('insertTable').value;
    const data = JSON.parse(document.getElementById('insertData').value);
    fetch('/api/tables/'+table+'/rows', {
        method:'POST', headers:{'Content-Type':'application/json'}, 
        body:JSON.stringify({row:data})
    }).then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d));
}
function commit() {
    fetch('/api/tables/'+document.getElementById('insertTable').value+'/commit', {method:'POST'})
    .then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d));
}
function bulkInsert() {
    const table = document.getElementById('insertTable').value;
    for(let i=0; i<10; i++) {
        const data = ['bulk_test', Math.random().toFixed(3), Date.now().toString()];
        fetch('/api/tables/'+table+'/rows', {
            method:'POST', headers:{'Content-Type':'application/json'}, 
            body:JSON.stringify({row:data})
        });
    }
    setTimeout(() => document.getElementById('result').innerHTML = 'Bulk insert completed', 1000);
}
setInterval(refreshStatus, 3000);
refreshStatus();
</script></body></html>"""
        
        headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
        headers += f"Content-Length: {len(html)}\r\n\r\n"
        return headers + html
    
    else:
        return create_response(404, message=f"Endpoint not found: {method} {path}")

def parse_request(request_data):
    lines = request_data.split('\n')
    if not lines:
        return None, None, {}, {}
    
    request_line = lines[0].strip()
    parts = request_line.split(' ')
    
    if len(parts) < 2:
        return None, None, {}, {}
    
    method = parts[0]
    full_path = parts[1]
    
    if '?' in full_path:
        path, query_string = full_path.split('?', 1)
        params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value.replace('%20', ' ').replace('+', ' ')
    else:
        path = full_path
        params = {}
    
    json_body = {}
    if method in ['POST', 'PUT', 'DELETE']:
        try:
            if '\r\n\r\n' in request_data:
                body = request_data.split('\r\n\r\n', 1)[1]
                if body.strip():
                    json_body = json.loads(body)
        except Exception as e:
            log(f"JSON parse error: {e}", "ERROR")
    
    return method, path, params, json_body


def main():
    global connection_count, active_connections
    
    log("Starting Async Pico Database Server")
    
    # Init db
    try:
        db = AsyncMiniDB("/sd", flush_every=3, auto_commit_ms=20000)
        log("Async Database initialized")
    except Exception as e:
        log(f"DB init failed: {e}", "ERROR")
        return
    
    # Create access point
    ip = create_access_point()
    if not ip:
        log("Failed to create AP", "ERROR")
        return
    
    # Setup server socket
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(addr)
        server_socket.listen(5)  # Allow more pending connections
        server_socket.setblocking(False)  # Non-blocking server socket
        log(f"Async Server listening on {ip}:80")
    except Exception as e:
        log(f"Server setup failed: {e}", "ERROR")
        return
    
    # Main async event loop
    last_gc = time.ticks_ms()
    last_status = time.ticks_ms()
    
    while True:
        current_time = time.ticks_ms()
        
        try:
            # Accept new connections (non-blocking)
            try:
                client_socket, client_addr = server_socket.accept()
                connection_count += 1
                conn = AsyncConnection(client_socket, client_addr, connection_count)
                active_connections.append(conn)
                log(f"New connection #{connection_count} (active: {len(active_connections)})")
            except OSError as e:
                if e.args[0] != 11:  # Not EAGAIN (no pending connections)
                    log(f"Accept error: {e.args[0]}", "ERROR")
            
            # Process active connections
            completed_connections = []
            
            for conn in active_connections[:]:  # Copy list to avoid modification during iteration
                try:
                    if conn.response_sent:
                        # Connection finished, mark for removal
                        completed_connections.append(conn)
                        continue
                    
                    # Try to receive more data
                    if not conn.receive_data():
                        # Client disconnected
                        completed_connections.append(conn)
                        continue
                    
                    # Try to process request if complete
                    if conn.process_request(db):
                        # Request processed, connection will be closed
                        completed_connections.append(conn)
                        
                except Exception as e:
                    log(f"Connection #{conn.id} error: {e}", "ERROR")
                    completed_connections.append(conn)
            
            # Clean up completed connections
            for conn in completed_connections:
                if conn in active_connections:
                    active_connections.remove(conn)
                conn.close()
            
            # Auto-commit check
            if db.needs_auto_commit():
                committed = db.auto_commit_all()
                if committed > 0:
                    log(f"Auto-committed {committed} tables")
            
            # Periodic garbage collection
            if time.ticks_diff(current_time, last_gc) > 10000:  # Every 10 seconds
                gc.collect()
                last_gc = current_time
            
            # Status log
            if time.ticks_diff(current_time, last_status) > 30000:  # Every 30 seconds
                log(f"Active: {len(active_connections)}, Total: {connection_count}, Memory: {gc.mem_free()}")
                last_status = current_time
            
            # Small delay to prevent busy loop
            time.sleep_ms(10)
            
        except KeyboardInterrupt:
            log("Server shutting down ..")
            break
        except Exception as e:
            log(f"Main loop error: {e}", "ERROR")
    
    # Cleanup
    for conn in active_connections:
        conn.close()
    server_socket.close()
    log("Server stopped")

if __name__ == "__main__":
    main()


