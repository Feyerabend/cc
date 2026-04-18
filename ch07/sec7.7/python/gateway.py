"""gateway.py   API Gateway (port 5000)

Part of the three-service distributed system:
  auth_service.py
  data_service.py
  gateway.py       (this file)
  client.py

Single entry point for clients.  Responsibilities:
  1. Validate bearer token via the auth service
  2. Forward authenticated request to the data service
  3. Compose and return the response

Requires:  pip install flask requests
Run:       python gateway.py
"""

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

AUTH_SERVICE = "http://127.0.0.1:5001"
DATA_SERVICE = "http://127.0.0.1:5002"


def validate_token(token: str) -> tuple[bool, dict]:
    """Call the auth service; return (ok, response_json)."""
    try:
        r = requests.get(
            f"{AUTH_SERVICE}/validate",
            headers={"Authorization": token},
            timeout=2,
        )
        return r.status_code == 200, r.json()
    except requests.exceptions.RequestException as exc:
        return False, {"error": str(exc)}


@app.get("/api/data")
def api_data():
    token = request.headers.get("Authorization", "").strip()

    if not token:
        return jsonify({"error": "missing Authorization header"}), 401

    ok, auth_resp = validate_token(token)
    if not ok:
        return jsonify({"error": "unauthorized", "detail": auth_resp}), 403

    user = auth_resp["user"]

    try:
        r = requests.get(f"{DATA_SERVICE}/data/{user}", timeout=2)
        r.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return jsonify({"error": "data service unavailable", "detail": str(exc)}), 503

    return jsonify({
        "gateway": "ok",
        "auth_user": user,
        "payload": r.json(),
    })


if __name__ == "__main__":
    print("Gateway on http://127.0.0.1:5000")
    print("Test: curl -H 'Authorization: abc123' http://127.0.0.1:5000/api/data")
    app.run(port=5000)
