# protocol.py - TDOS Core Protocol Implementation
"""
Enhanced protocol with full error handling, compression, and versioning.
Compatible with MicroPython on Raspberry Pi Pico W.
"""

import ujson as json
import time
try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

# Protocol constants
PROTOCOL_VERSION = 1
MAX_MESSAGE_SIZE = 1024
HEARTBEAT_INTERVAL = 5  # seconds
SERVICE_TIMEOUT = 15    # seconds
MAX_RETRIES = 3
ACK_TIMEOUT = 2.0       # seconds

class MessageType:
    """Message type constants"""
    SERVICE_ANNOUNCE = 1
    SERVICE_QUERY = 2
    RPC_REQUEST = 3
    RPC_RESPONSE = 4
    HEARTBEAT = 5
    ERROR = 6
    ACK = 7
    SERVICE_GOODBYE = 8

class TDOSMessage:
    """Protocol message with serialization and validation"""
    
    def __init__(self, msg_type, payload, msg_id=None, reply_to=None):
        self.version = PROTOCOL_VERSION
        self.msg_type = msg_type
        self.msg_id = msg_id or self._generate_id()
        self.reply_to = reply_to
        self.timestamp = time.time()
        self.payload = payload
    
    @staticmethod
    def _generate_id():
        """Generate unique message ID"""
        t = str(time.ticks_us()) if hasattr(time, 'ticks_us') else str(time.time())
        h = hashlib.sha256(t.encode())
        return h.hexdigest()[:8] if hasattr(h, 'hexdigest') else str(hash(t))[:8]
    
    def serialize(self):
        """Convert message to JSON bytes"""
        data = {
            "v": self.version,
            "t": self.msg_type,
            "id": self.msg_id,
            "ts": int(self.timestamp),
            "p": self.payload
        }
        if self.reply_to:
            data["r"] = self.reply_to
            
        json_str = json.dumps(data)
        return json_str.encode('utf-8')
    
    @classmethod
    def deserialize(cls, data):
        """Parse message from JSON bytes"""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            msg_dict = json.loads(data)
            
            # Version compatibility check
            if msg_dict.get("v", 0) > PROTOCOL_VERSION:
                raise ValueError(f"Unsupported protocol version: {msg_dict.get('v')}")
            
            msg = cls(
                msg_type=msg_dict["t"],
                payload=msg_dict["p"],
                msg_id=msg_dict["id"],
                reply_to=msg_dict.get("r")
            )
            msg.timestamp = msg_dict.get("ts", time.time())
            return msg
            
        except Exception as e:
            raise ValueError(f"Failed to deserialize message: {e}")
    
    def __repr__(self):
        return f"TDOSMessage(type={self.msg_type}, id={self.msg_id}, payload={self.payload})"


class ServiceInfo:
    """Information about a registered service"""
    
    def __init__(self, name, ip, port, metadata=None):
        self.name = name
        self.ip = ip
        self.port = port
        self.metadata = metadata or {}
        self.last_seen = time.time()
        self.failures = 0
        self.state = "active"  # active, degraded, failed
    
    def update_heartbeat(self):
        """Update last seen timestamp and reset failures"""
        self.last_seen = time.time()
        self.failures = 0
        if self.state == "degraded":
            self.state = "active"
    
    def mark_failure(self):
        """Increment failure counter and update state"""
        self.failures += 1
        if self.failures >= MAX_RETRIES:
            self.state = "failed"
        elif self.failures > 0:
            self.state = "degraded"
    
    def is_alive(self):
        """Check if service is still considered alive"""
        return (time.time() - self.last_seen) < SERVICE_TIMEOUT
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "metadata": self.metadata,
            "last_seen": self.last_seen,
            "failures": self.failures,
            "state": self.state
        }


class ServiceRegistry:
    """Registry for managing discovered services"""
    
    def __init__(self):
        self.services = {}  # service_name -> ServiceInfo
        self.pending_requests = {}  # msg_id -> (callback, timeout, retries)
    
    def register_service(self, name, ip, port, metadata=None):
        """Register or update a service"""
        if name in self.services:
            service = self.services[name]
            service.ip = ip
            service.port = port
            service.metadata = metadata or {}
            service.update_heartbeat()
            print(f"[Registry] Updated service: {name} at {ip}:{port}")
        else:
            self.services[name] = ServiceInfo(name, ip, port, metadata)
            print(f"[Registry] Registered new service: {name} at {ip}:{port}")
    
    def update_heartbeat(self, name, ip):
        """Update service heartbeat"""
        if name in self.services:
            service = self.services[name]
            if service.ip == ip:
                service.update_heartbeat()
                return True
        return False
    
    def get_service(self, name):
        """Get service info if alive"""
        if name in self.services:
            service = self.services[name]
            if service.is_alive():
                return service
            else:
                print(f"[Registry] Service {name} timed out")
                self.remove_service(name)
        return None
    
    def remove_service(self, name):
        """Remove a service from registry"""
        if name in self.services:
            print(f"[Registry] Removing service: {name}")
            del self.services[name]
    
    def mark_service_failure(self, name):
        """Mark a service failure"""
        if name in self.services:
            service = self.services[name]
            service.mark_failure()
            print(f"[Registry] Service {name} failure #{service.failures}")
            
            if service.state == "failed":
                self.remove_service(name)
    
    def cleanup_stale_services(self):
        """Remove services that have timed out"""
        stale = [name for name, service in self.services.items() 
                 if not service.is_alive()]
        
        for name in stale:
            self.remove_service(name)
        
        return len(stale)
    
    def list_services(self):
        """Get list of active service names"""
        return [name for name, service in self.services.items() 
                if service.is_alive()]
    
    def get_all_services(self):
        """Get all service info objects"""
        return {name: service for name, service in self.services.items() 
                if service.is_alive()}
    
    def add_pending_request(self, msg_id, callback, timeout=ACK_TIMEOUT):
        """Register a pending request awaiting response"""
        self.pending_requests[msg_id] = {
            'callback': callback,
            'timeout': time.time() + timeout,
            'retries': 0
        }
    
    def handle_response(self, msg_id, response):
        """Handle response to pending request"""
        if msg_id in self.pending_requests:
            req = self.pending_requests[msg_id]
            callback = req['callback']
            del self.pending_requests[msg_id]
            
            if callback:
                callback(response)
            return True
        return False
    
    def cleanup_pending_requests(self):
        """Remove timed out pending requests"""
        now = time.time()
        expired = [msg_id for msg_id, req in self.pending_requests.items()
                   if now > req['timeout']]
        
        for msg_id in expired:
            print(f"[Registry] Request {msg_id} timed out")
            req = self.pending_requests[msg_id]
            if req['callback']:
                req['callback'](None)  # Notify callback of timeout
            del self.pending_requests[msg_id]
        
        return len(expired)


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(self, failure_threshold=3, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def record_success(self):
        """Record successful operation"""
        self.failures = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed operation"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"
            print(f"[CircuitBreaker] Circuit opened after {self.failures} failures")
    
    def can_attempt(self):
        """Check if operation can be attempted"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            # Check if timeout has passed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                print("[CircuitBreaker] Circuit half-open, trying recovery")
                return True
            return False
        
        if self.state == "half-open":
            return True
        
        return False
    
    def reset(self):
        """Reset circuit breaker"""
        self.failures = 0
        self.state = "closed"
