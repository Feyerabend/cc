# this version has no display of its own,
# it only connects to the SD card setup
import network
import socket
import time
import json
import os
import machine
import sdcard
import uos

# Access Point Configuration
AP_SSID = "PicoDatabase"
AP_PASSWORD = None  # Open network for simplicity

# Global state
log_buffer = []
max_log_lines = 20  # Store more logs since we'll show them in web interface
connection_count = 0
last_request_time = 0

def log(message, level="INFO"):
    global log_buffer, max_log_lines
    timestamp = time.ticks_ms() // 1000
    log_entry = {"timestamp": timestamp, "level": level, "message": message}
    print(f"[{level}] {message}")
    
    log_buffer.append(log_entry)
    if len(log_buffer) > max_log_lines:
        log_buffer.pop(0)

# SD Card Database Class
class MiniDB:
    def __init__(self, base="/sd", flush_every=1):
        self.base = base if base.endswith("/") else base + "/"
        self.flush_every = max(1, flush_every)
        self.buffers = {}

        # Initialize SD card
        try:
            # SD Card SPI setup
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

        # Check base directory
        try:
            os.listdir(self.base)
        except OSError:
            os.mkdir(self.base)
            log(f"Created base directory: {self.base}")

    def _path(self, name):
        return self.base + name + ".csv"

    def create_table(self, name, fields):
        """Create a new table. Overwrites if exists."""
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
        """Insert a row into buffer."""
        if not isinstance(row, (list, tuple)):
            return False
        if name not in self.buffers:
            self.buffers[name] = []
        self.buffers[name].append(row)
        if len(self.buffers[name]) >= self.flush_every:
            return self.commit(name)
        return True

    def commit(self, name):
        """Flush buffer for a table."""
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
        """Get all rows as list of dicts."""
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
        """Select rows matching conditions."""
        results = []
        for row in self.all_rows(name):
            if where:
                if all(row.get(k) == str(v) for k, v in where.items()):
                    results.append(row)
            else:
                results.append(row)
        return results

    def delete_rows(self, name, where=None):
        """Delete rows matching condition."""
        path = self._path(name)
        try:
            with open(path, "r") as f:
                header = f.readline().strip()
                if not header:
                    return False
                header_fields = header.split(",")
                rows = []
                deleted_count = 0
                
                for line in f:
                    values = line.strip().split(",")
                    if len(values) != len(header_fields):
                        continue
                    row = dict(zip(header_fields, values))
                    
                    should_delete = False
                    if where:
                        if all(row.get(k) == str(v) for k, v in where.items()):
                            should_delete = True
                            deleted_count += 1
                    
                    if not should_delete:
                        rows.append(values)

            # Rewrite file
            with open(path, "w") as f:
                f.write(header + "\n")
                for values in rows:
                    f.write(",".join(values) + "\n")
                f.flush()
            
            log(f"Deleted {deleted_count} rows from {name}")
            return deleted_count > 0
            
        except OSError as e:
            log(f"Delete error: {e}", "ERROR")
            return False

    def list_tables(self):
        """List all available tables."""
        tables = []
        try:
            for file in os.listdir(self.base):
                if file.endswith('.csv'):
                    tables.append(file[:-4])  # Remove .csv extension
        except OSError:
            pass
        return tables

    def table_info(self, name):
        """Get table schema and row count."""
        try:
            with open(self._path(name), "r") as f:
                header = f.readline().strip().split(",")
                row_count = sum(1 for line in f if line.strip())
                return {"fields": header, "row_count": row_count}
        except OSError:
            return None

# Initialize database
db = None

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
        log(f"AP starting... {timeout}s")
    
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
        "connection_count": connection_count
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

def handle_rest_request(method, path, params, json_body):
    global db
    
    # GET /api/tables - List all tables
    if method == "GET" and path == "/api/tables":
        tables = db.list_tables()
        return create_response(200, {"tables": tables})
    
    # POST /api/tables/{name} - Create new table
    elif method == "POST" and path.startswith("/api/tables/"):
        table_name = path.split("/")[-1]
        fields = json_body.get("fields", [])
        
        if not fields:
            return create_response(400, message="Fields required")
        
        if db.create_table(table_name, fields):
            return create_response(201, message=f"Table '{table_name}' created")
        else:
            return create_response(500, message="Failed to create table")
    
    # GET /api/tables/{name} - Get table info and data
    elif method == "GET" and path.startswith("/api/tables/"):
        table_name = path.split("/")[-1]
        
        # Get table info
        info = db.table_info(table_name)
        if info is None:
            return create_response(404, message=f"Table '{table_name}' not found")
        
        # Get data with optional filtering
        where = {}
        for key, value in params.items():
            if key.startswith("where_"):
                field = key[6:]  # Remove "where_" prefix
                where[field] = value
        
        rows = db.select(table_name, where if where else None)
        
        return create_response(200, {
            "table": table_name,
            "info": info,
            "rows": rows,
            "count": len(rows)
        })
    
    # POST /api/tables/{name}/rows - Insert new row
    elif method == "POST" and path.startswith("/api/tables/") and path.endswith("/rows"):
        table_name = path.split("/")[-2]
        row_data = json_body.get("row", [])
        
        if not row_data:
            return create_response(400, message="Row data required")
        
        if db.insert(table_name, row_data):
            return create_response(201, message="Row inserted")
        else:
            return create_response(500, message="Failed to insert row")
    
    # DELETE /api/tables/{name}/rows - Delete rows
    elif method == "DELETE" and path.startswith("/api/tables/") and path.endswith("/rows"):
        table_name = path.split("/")[-2]
        
        # Build where conditions from JSON body or params
        where = json_body.get("where", {})
        if not where:
            for key, value in params.items():
                if key.startswith("where_"):
                    field = key[6:]
                    where[field] = value
        
        if db.delete_rows(table_name, where if where else None):
            return create_response(200, message="Rows deleted")
        else:
            return create_response(404, message="No rows deleted")
    
    # POST /api/tables/{name}/commit - Force commit buffered data
    elif method == "POST" and path.startswith("/api/tables/") and path.endswith("/commit"):
        table_name = path.split("/")[-2]
        
        if db.commit(table_name):
            return create_response(200, message="Data committed")
        else:
            return create_response(404, message="Nothing to commit")
    
    # GET /api/logs - Get recent logs with web display
    elif method == "GET" and path == "/api/logs":
        return create_response(200, {
            "logs": log_buffer,
            "count": len(log_buffer),
            "connections": connection_count,
            "uptime": time.ticks_ms() // 1000
        })
    
    # GET /api/status - System status
    elif method == "GET" and path == "/api/status":
        return create_response(200, {
            "uptime": time.ticks_ms(),
            "connections": connection_count,
            "ap_ssid": AP_SSID,
            "tables": len(db.list_tables()),
            "sd_mounted": True
        })
    
    # Simple web interface
    elif method == "GET" and path == "/":
        html = """<!DOCTYPE html>
<html><head><title>Pico Database</title></head><body>
<h2>Pico Database</h2>
<div>
<h3>Status</h3>
<button onclick="refreshStatus()">Refresh</button>
<div id="status"></div>
<textarea id="logs" rows="10" cols="80" readonly></textarea>
</div>
<div>
<h3>Tables</h3>
<input id="tableName" placeholder="table name" value="test">
<button onclick="createTable()">Create</button>
<button onclick="listTables()">List</button>
<button onclick="getTable()">View</button>
<div id="result"></div>
</div>
<div>
<h3>Data</h3>
<input id="insertTable" placeholder="table" value="test">
<input id="insertData" placeholder='["val1","val2"]' value='["test","123"]'>
<button onclick="insertRow()">Insert</button>
<button onclick="commit()">Commit</button>
</div>
<script>
function refreshStatus() {
    fetch('/api/status').then(r=>r.json()).then(d=>{
        document.getElementById('status').innerHTML = 'Up:'+Math.floor(d.data.uptime/1000)+'s Conn:'+d.data.connections+' Tables:'+d.data.tables;
    });
    fetch('/api/logs').then(r=>r.json()).then(d=>{
        document.getElementById('logs').value = d.data.logs.map(l=>l.timestamp+' '+l.level+' '+l.message).join('\\n');
    });
}
function createTable() {
    fetch('/api/tables/'+document.getElementById('tableName').value, {
        method:'POST', headers:{'Content-Type':'application/json'}, 
        body:JSON.stringify({fields:['name','value','time']})
    }).then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d));
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
    fetch('/api/tables/'+document.getElementById('insertTable').value+'/commit', {method:'POST'}).then(r=>r.json()).then(d=>document.getElementById('result').innerHTML=JSON.stringify(d));
}
setInterval(refreshStatus, 5000);
refreshStatus();
</script></body></html>"""
        
        headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
        headers += f"Content-Length: {len(html)}\r\n\r\n"
        return headers + html
    
    else:
        return create_response(404, message=f"Endpoint not found: {method} {path}")

def parse_json_body(request_data):
    try:
        if '\r\n\r\n' in request_data:
            body = request_data.split('\r\n\r\n', 1)[1]
            if body.strip():
                return json.loads(body)
    except Exception as e:
        log(f"JSON parse error: {e}", "ERROR")
    return {}

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
        json_body = parse_json_body(request_data)
    
    return method, path, params, json_body

def main():
    global connection_count, db
    
    log("Starting Pico Database Server")
    
    # Initialize database
    try:
        db = MiniDB("/sd", flush_every=2)
        log("Database initialized")
    except Exception as e:
        log(f"DB init failed: {e}", "ERROR")
        return
    
    # Create access point
    ip = create_access_point()
    if not ip:
        log("Failed to create AP", "ERROR")
        return
    
    # Setup web server
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(3)
        log(f"Server listening on {ip}:80")
    except Exception as e:
        log(f"Server setup failed: {e}", "ERROR")
        return
    
    # Main server loop
    while True:
        client_socket = None
        try:
            client_socket, client_addr = s.accept()
            connection_count += 1
            
            log(f"Connection #{connection_count}")
            
            client_socket.settimeout(15.0)
            request_data = client_socket.recv(4096).decode('utf-8')
            
            if not request_data:
                continue
            
            method, path, params, json_body = parse_request(request_data)
            
            if method and path:
                log(f"{method} {path[:15]}")
                response = handle_rest_request(method, path, params, json_body)
                client_socket.send(response.encode('utf-8'))
            else:
                error_response = create_response(400, message="Invalid request")
                client_socket.send(error_response.encode('utf-8'))
                
        except OSError as e:
            error_code = e.args[0] if e.args else 0
            if error_code in [104, 110]:  # Connection reset/timeout
                log("Client disconnected", "WARN")
            else:
                log(f"Connection error: {error_code}", "ERROR")
                
        except Exception as e:
            log(f"Server error: {str(e)[:15]}", "ERROR")
            
        finally:
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass

if __name__ == "__main__":
    main()