"""client.py   test client for the distributed microservice system

Sends requests to the gateway with different tokens so you can observe
successful and failed authentication.

Requires:  pip install requests
Run:       python client.py      (gateway + both services must be running)
"""

import requests

GATEWAY = "http://127.0.0.1:5000/api/data"


def call(label: str, token: str) -> None:
    print(f"\n--- {label} ---")
    print(f"Token: {token!r}")
    try:
        r = requests.get(GATEWAY, headers={"Authorization": token}, timeout=3)
        print(f"Status: {r.status_code}")
        print(f"Body:   {r.json()}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to gateway. Is it running?")


call("Valid token (alice)", "abc123")
call("Valid token (bob)",   "def456")
call("Invalid token",       "xxxxxx")
call("Missing token",       "")
