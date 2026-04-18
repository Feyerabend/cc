"""auth_service.py   Auth microservice (port 5001)

Part of the three-service distributed system:
  auth_service.py  (this file)
  data_service.py
  gateway.py
  client.py

Validates a bearer token supplied via the Authorization header.
Tokens are hardcoded for simplicity   real systems use JWT or OAuth.

Requires:  pip install flask
Run:       python auth_service.py
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# token -> username mapping (stand-in for a real identity store)
VALID_TOKENS: dict[str, str] = {
    "abc123": "alice",
    "def456": "bob",
}


@app.get("/validate")
def validate():
    token = request.headers.get("Authorization", "").strip()

    if not token:
        return jsonify({"valid": False, "reason": "missing token"}), 401

    user = VALID_TOKENS.get(token)
    if not user:
        return jsonify({"valid": False, "reason": "unknown token"}), 403

    return jsonify({"valid": True, "user": user})


if __name__ == "__main__":
    print("Auth service on http://127.0.0.1:5001")
    print("Test: curl -H 'Authorization: abc123' http://127.0.0.1:5001/validate")
    app.run(port=5001)
