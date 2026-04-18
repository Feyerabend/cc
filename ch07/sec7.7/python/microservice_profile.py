"""microservice_profile.py   service-to-service HTTP communication

A "profile service" (port 5002) that calls a "user service" (port 5001)
to enrich its response.  Demonstrates:
  - service independence
  - network-based communication between services
  - failure dependency risk

Requires:  pip install flask requests

Start a stub user service first (in another terminal):
  python -c "
from flask import Flask, jsonify
app = Flask(__name__)

@app.get('/user/<name>')
def user(name): return jsonify({'user': name, 'role': 'reader'})

app.run(port=5001)
"

Then run this service: python microservice_profile.py
Test: curl http://127.0.0.1:5002/profile/alice
"""

import requests
from flask import Flask, jsonify

app = Flask(__name__)

USER_SERVICE = "http://127.0.0.1:5001"


@app.get("/profile/<name>")
def profile(name: str):
    try:
        r = requests.get(f"{USER_SERVICE}/user/{name}", timeout=2)
        r.raise_for_status()
        user_data = r.json()
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "user service unavailable"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "user service timed out"}), 504

    return jsonify({
        "profile": user_data,
        "settings": {"theme": "dark", "notifications": True},
    })


if __name__ == "__main__":
    print("Profile service on http://127.0.0.1:5002")
    print("Test: curl http://127.0.0.1:5002/profile/alice")
    app.run(port=5002)
