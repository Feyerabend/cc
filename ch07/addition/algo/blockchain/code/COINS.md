
## coins.py

A full coin system with ECDSA signatures, Proof of Work mining, and a Flask REST API.
See `README.md` for a full explanation of the design, API endpoints, and how to run it.

Prerequisites:

```bash
pip install flask ecdsa requests waitress
```

Quick start:

```bash
python3 coins.py                        # development node on port 5000
python3 coins.py --production --port 8080   # production mode (requires waitress)
```
