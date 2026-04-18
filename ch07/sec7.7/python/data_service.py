"""data_service.py   Data microservice (port 5002)

Part of the three-service distributed system:
  auth_service.py
  data_service.py  (this file)
  gateway.py
  client.py

Returns protected data for a named user.
Assumes the caller (the gateway) has already authenticated.

Requires:  pip install flask
Run:       python data_service.py
"""

from flask import Flask, jsonify

app = Flask(__name__)

# In a real system this would be a database query.
DATA: dict[str, list[str]] = {
    "alice": ["alice_doc_1", "alice_doc_2", "alice_report_q1"],
    "bob":   ["bob_report",  "bob_notes",   "bob_draft"],
}


@app.get("/data/<user>")
def get_data(user: str):
    return jsonify({
        "user": user,
        "data": DATA.get(user, []),
    })


if __name__ == "__main__":
    print("Data service on http://127.0.0.1:5002")
    print("Test: curl http://127.0.0.1:5002/data/alice")
    app.run(port=5002)
