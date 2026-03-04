import json
from urllib import request, parse
from typing import Dict, Optional, Any


class HttpRequest:
    def __init__(self):
        self.method: str = "GET"
        self.url: str = ""
        self.headers: Dict[str, str] = {}
        self.query_params: Dict[str, Any] = {}
        self.body: Optional[Any] = None
        self.timeout: Optional[float] = None

    def __str__(self):
        parts = [f"{self.method} {self.url}"]
        if self.query_params:
            parts.append(f"?{parse.urlencode(self.query_params)}")
        if self.headers:
            parts.append(f"Headers: {self.headers}")
        if self.body is not None:
            parts.append(f"Body: {json.dumps(self.body, indent=2) if isinstance(self.body, dict) else str(self.body)}")
        if self.timeout:
            parts.append(f"Timeout: {self.timeout}s")
        return "\n".join(parts)


class HttpRequestBuilder:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.request = HttpRequest()
        self.base_url = base_url.rstrip("/")

    def get(self) -> 'HttpRequestBuilder':
        self.request.method = "GET"
        return self

    def post(self) -> 'HttpRequestBuilder':
        self.request.method = "POST"
        return self

    def path(self, path: str) -> 'HttpRequestBuilder':
        self.request.url = f"{self.base_url}/{path.lstrip('/')}"
        return self

    def header(self, key: str, value: str) -> 'HttpRequestBuilder':
        self.request.headers[key] = value
        return self

    def query(self, key: str, value: Any) -> 'HttpRequestBuilder':
        self.request.query_params[key] = value
        return self

    def json_body(self, data: dict) -> 'HttpRequestBuilder':
        self.request.body = data
        self.header("Content-Type", "application/json")
        return self

    def timeout(self, seconds: float) -> 'HttpRequestBuilder':
        self.request.timeout = seconds
        return self

    def build(self) -> HttpRequest:
        if not self.request.url:
            raise ValueError("URL must be set")
        return self.request

    def send(self) -> dict:
        req = self.build()

        # Prepare urllib request
        full_url = req.url
        if req.query_params:
            full_url += "?" + parse.urlencode(req.query_params)

        body_bytes = None
        if req.body is not None:
            body_bytes = json.dumps(req.body).encode("utf-8")

        opener = request.build_opener()
        ureq = request.Request(
            full_url,
            data=body_bytes,
            method=req.method,
            headers=req.headers
        )

        timeout = req.timeout or 10.0

        try:
            with opener.open(ureq, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if response.getheader("Content-Type", "").startswith("application/json") else {"text": raw}
        except Exception as e:
            return {"error": str(e)}


# Examples

if __name__ == "__main__":
    # GET /users?role=admin&limit=5
    users = (HttpRequestBuilder()
             .get()
             .path("/users")
             .query("role", "admin")
             .query("limit", 5)
             .timeout(8.0)
             .send())

    print("GET users response:")
    print(json.dumps(users, indent=2))

    # POST /orders
    order = (HttpRequestBuilder()
             .post()
             .path("/orders")
             .json_body({
                 "items": ["laptop", "mouse"],
                 "total": 1299.99,
                 "customer_id": 42
             })
             .send())

    print("\nPOST order response:")
    print(json.dumps(order, indent=2))

