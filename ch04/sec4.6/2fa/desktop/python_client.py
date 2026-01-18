# python_client.py - Client for 2FA authentication system
# This runs on your PC/Mac and connects to Device B

import requests
import json
import time
from typing import Optional, Dict

# Configuration Constants
DEFAULT_PORT = 9090
REQUEST_TIMEOUT = 10  # Increased timeout
MAX_RETRIES = 2  # Retry failed requests

class AuthClient:
    def __init__(self, server_ip: str, server_port: int = DEFAULT_PORT):
        self.server_url = f"http://{server_ip}:{server_port}"
        self.session_id: Optional[str] = None
        self.username: Optional[str] = None
        
    def _make_request(self, endpoint: str, data: dict, method: str = "POST") -> dict:
        for attempt in range(MAX_RETRIES):
            try:
                if method == "POST":
                    response = requests.post(
                        f"{self.server_url}{endpoint}",
                        json=data,
                        timeout=REQUEST_TIMEOUT
                    )
                else:
                    response = requests.get(
                        f"{self.server_url}{endpoint}",
                        timeout=REQUEST_TIMEOUT
                    )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.ConnectionError as e:
                print(f"    Connection failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
            except requests.exceptions.Timeout as e:
                print(f"    Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"    Request error: {e}")
                return {"status": "error", "message": str(e)}
        
        return {"status": "error", "message": "All connection attempts failed"}
    
    def login(self, username: str, password: str) -> dict:
        # Input validation
        if not username or not password:
            print("    Error: Username and password required")
            return {"status": "error", "message": "Username and password required"}
        
        username = username.strip()
        
        print(f"\n[Step 1] Logging in as '{username}'...")
        
        data = self._make_request("/login", {
            "username": username,
            "password": password
        })
        
        if data.get("status") == "pending":
            self.session_id = data["session_id"]
            self.username = username
            print(f"      Password accepted!")
            print(f"    Session ID: {self.session_id}")
            print(f"    {data['message']}")
        elif data.get("status") == "error":
            print(f"      Login failed: {data.get('message', 'Unknown error')}")
        
        return data
    
    def verify_token(self, token: str) -> dict:
        if not self.session_id:
            print("      No active session. Login first.")
            return {"status": "error", "message": "No session"}
        
        # Validate token format
        token = token.strip()
        if len(token) != 6:
            print("      Token must be exactly 6 digits")
            return {"status": "error", "message": "Token must be 6 digits"}
        
        if not token.isdigit():
            print("      Token must contain only digits")
            return {"status": "error", "message": "Token must be numeric"}
        
        print(f"\n[Step 2] Verifying token '{token}'...")
        
        data = self._make_request("/verify", {
            "session_id": self.session_id,
            "token": token
        })
        
        if data.get("status") == "success":
            print(f"      Authentication successful!")
            print(f"    Welcome, {data.get('username', self.username)}!")
        elif data.get("status") == "error":
            print(f"      Verification failed: {data.get('message', 'Unknown error')}")
        
        return data
    
    def check_status(self) -> dict:
        """Check authentication status (IMPROVED)"""
        if not self.session_id:
            print("      No active session")
            return {"status": "error", "message": "No session"}
        
        data = self._make_request("/status", {
            "session_id": self.session_id
        })
        
        if data.get("status") == "ok":
            auth_status = "  Authenticated" if data.get("authenticated") else "  Pending 2FA"
            print(f"> Session Status")
            print(f"> User:   {data.get('username', 'Unknown')}")
            print(f"> Status: {auth_status}")
            if "created" in data:
                age = int(time.time() - data["created"])
                print(f"> Age:    {age}s")
        elif data.get("status") == "error":
            print(f"      Status check failed: {data.get('message', 'Unknown error')}")
        
        return data
    
    def check_health(self) -> dict:
        try:
            response = requests.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}


def print_banner():
    print("  2FA Authentication Client".center(60))


def validate_ip(ip: str) -> bool:
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def interactive_mode(server_ip: str):
    print_banner()
    
    client = AuthClient(server_ip)
    
    print(f"\nConnecting to server at {server_ip}:{DEFAULT_PORT}")
    
    # Check server health
    health = client.check_health()
    if health.get("status") == "ok":
        print("  Server is online")
        if "sessions" in health:
            print(f"  Active sessions: {health['sessions']}")
    else:
        print("! Warning: Could not reach server")
    
    print("\nAvailable test users:")
    print("  - alice / password123")
    print("  - bob   / secret456")
    
    while True:
        print("\n" + "─" * 60)
        print("Commands:")
        print("  1. Login (username + password)")
        print("  2. Verify token (from Device A)")
        print("  3. Check status")
        print("  4. Check server health")
        print("  5. Exit")
        print("─" * 60)
        
        choice = input("\nChoice [1-5]: ").strip()
        
        if choice == "1":
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            if not username or not password:
                print("  Username and password required")
                continue
            
            result = client.login(username, password)
            
            if result.get("status") == "pending":
                print("\n" + "─" * 60)
                print("NEXT STEPS:")
                print("1. Go to Device A (Token Service)")
                print("2. Enter PIN: 1234 using buttons (A=1, B=2, X=3, Y=4)")
                print("3. Read the 6-digit token from the display")
                print("4. Return here and choose option 2 to verify")
                print("─" * 60)
            
        elif choice == "2":
            if not client.session_id:
                print("  Please login first (option 1)")
                continue
            
            token = input("Enter 6-digit token from Device A: ").strip()
            result = client.verify_token(token)
            
            if result.get("status") == "success":
                print("\n" + "=" * 60)
                print("    YOU ARE NOW FULLY AUTHENTICATED!  ".center(60))
                print("=" * 60)
            
        elif choice == "3":
            client.check_status()
            
        elif choice == "4":
            print("\nChecking server health..")
            health = client.check_health()
            if health.get("status") == "ok":
                print("  Server is healthy")
                if "sessions" in health:
                    print(f"  Active sessions: {health['sessions']}")
                if "authenticated" in health:
                    print(f"  Authenticated users: {health['authenticated']}")
            else:
                print(f"  Health check failed: {health.get('message', 'Unknown error')}")
            
        elif choice == "5":
            print("\nBye!")
            break
            
        else:
            print("  Invalid choice. Please enter 1-5.")


def demo_mode(server_ip: str):
    print_banner()
    print("\n> Running automated demo..\n")
    
    client = AuthClient(server_ip)
    
    # Check server health first
    print("Checking server connectivity..")
    health = client.check_health()
    if health.get("status") != "ok":
        print("  Cannot reach server. Is Device B running?")
        return
    print("  Server is online\n")
    
    # Step 1: Login
    print("─" * 60)
    result = client.login("alice", "password123")
    
    if result.get("status") != "pending":
        print("  Demo failed at login step")
        return
    
    time.sleep(2)
    
    # Step 2: Get token from user
    print("\n" + "─" * 60)
    print("\n⏸  PAUSED - Manual step required:")
    print("   ┌──────────────────────────────────────────┐")
    print("   │ 1. Go to Device A (Token Service)        │")
    print("   │ 2. Enter PIN: 1234                       │")
    print("   │    (Use buttons: A=1, B=2, X=3, Y=4)     │")
    print("   │ 3. Read the 6-digit token from display   │")
    print("   │ 4. Enter it below                        │")
    print("   └──────────────────────────────────────────┘")
    
    while True:
        token = input("\n> Enter token: ").strip()
        
        if len(token) != 6:
            print("  Token must be exactly 6 digits. Try again.")
            continue
        
        if not token.isdigit():
            print("  Token must contain only numbers. Try again.")
            continue
        
        break
    
    # Step 3: Verify
    print("\n" + "─" * 60)
    result = client.verify_token(token)
    
    if result.get("status") == "success":
        time.sleep(1)
        
        print("\n" + "─" * 60)
        client.check_status()
        
        print("\n" + "=" * 60)
        print("    DEMO COMPLETE!".center(60))
        print("=" * 60)
        print("\nThis demonstrated two-factor authentication:")
        print("    Something you know: password")
        print("    Something you have: Device A with correct PIN")
        print("\nBoth factors were required for successful authentication.")
    else:
        print("\n  Demo failed at verification step")
        print(f"  Reason: {result.get('message', 'Unknown error')}")


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("  SETUP INSTRUCTIONS".center(60))
    print("=" * 60)
    print("\n1. Device A (Token Service):")
    print("   • Upload and run: token_service.py")
    print("   • Creates WiFi AP: '2FA_Token_Service'")
    print("   • Password: 'SecureToken2024'")
    print("   • IP will be: 192.168.4.1")
    print("\n2. Device B (Auth Server):")
    print("   • Upload and run: auth_server.py")
    print("   • Connects to Device A's WiFi")
    print("   • Check its display for IP address")
    print("\n3. This Client:")
    print("   • Needs Device B's IP address")
    print("   • Run: python python_client.py <DEVICE_B_IP>")
    print("=" * 60)
    
    # Get server IP
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = input("\nEnter Device B's IP address: ").strip()
        if not server_ip:
            print("  Error: IP address required")
            sys.exit(1)
    
    # Validate IP format
    if not validate_ip(server_ip):
        print(f"  Error: '{server_ip}' is not a valid IP address")
        print("  Expected format: xxx.xxx.xxx.xxx (e.g., 192.168.4.2)")
        sys.exit(1)
    
    print(f"\n▶ Connecting to: {server_ip}")
    print("\nSelect mode:")
    print("  1. Interactive mode (recommended)")
    print("  2. Demo mode")
    
    mode = input("\nChoice [1/2]: ").strip()
    
    if mode == "1":
        interactive_mode(server_ip)
    elif mode == "2":
        demo_mode(server_ip)
    else:
        print("  Invalid mode. Please run again and choose 1 or 2.")
        sys.exit(1)


