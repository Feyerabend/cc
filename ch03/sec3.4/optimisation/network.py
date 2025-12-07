"""
Network and API Examples
Demonstrates various techniques for optimising network communication
"""

import time
import json
import gzip
import io
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Simulated network delay
def simulate_network_delay(ms=50):
    time.sleep(ms / 1000.0)

# Example 1: Request Batching
def fetch_user_unoptimized(user_id):
    """Simulate individual API call"""
    simulate_network_delay(50)
    return {"id": user_id, "name": f"User{user_id}"}

def fetch_users_sequential(user_ids):
    """UNOPTIMISED: One request per user"""
    start = time.time()
    users = []
    for user_id in user_ids:
        users.append(fetch_user_unoptimized(user_id))
    elapsed = time.time() - start
    return users, elapsed

def fetch_users_batch(user_ids):
    """OPTIMISED: Single batch request"""
    start = time.time()
    simulate_network_delay(50)  # Single request
    users = [{"id": uid, "name": f"User{uid}"} for uid in user_ids]
    elapsed = time.time() - start
    return users, elapsed

def demo_request_batching():
    print("--- Request Batching ---\n")
    user_ids = list(range(1, 11))
    
    users1, time1 = fetch_users_sequential(user_ids)
    print(f"Sequential requests (10 users): {time1:.3f}s")
    
    users2, time2 = fetch_users_batch(user_ids)
    print(f"Batch request (10 users): {time2:.3f}s ({time1/time2:.1f}x faster)")
    print()


# Example 2: Connection Pooling
class ConnectionPool:
    """Simulated connection pool"""
    def __init__(self, size=5):
        self.pool = [f"Connection{i}" for i in range(size)]
        self.available = self.pool.copy()
    
    def acquire(self):
        if self.available:
            return self.available.pop()
        return None
    
    def release(self, conn):
        self.available.append(conn)

def make_request_no_pool():
    """UNOPTIMISED: Create new connection each time"""
    simulate_network_delay(10)  # Connection overhead
    simulate_network_delay(20)  # Request
    return "Response"

def make_request_with_pool(pool):
    """OPTIMISED: Reuse connection from pool"""
    conn = pool.acquire()
    if conn:
        simulate_network_delay(20)  # Just request, no connection overhead
        pool.release(conn)
        return "Response"
    return None

def demo_connection_pooling():
    print("--- Connection Pooling ---\n")
    requests = 20
    
    start = time.time()
    for _ in range(requests):
        make_request_no_pool()
    time1 = time.time() - start
    print(f"Without pooling ({requests} requests): {time1:.3f}s")
    
    start = time.time()
    pool = ConnectionPool(size=5)
    for _ in range(requests):
        make_request_with_pool(pool)
    time2 = time.time() - start
    print(f"With pooling ({requests} requests): {time2:.3f}s ({time1/time2:.1f}x faster)")
    print()


# Example 3: Response Compression
def generate_sample_data(size=1000):
    """Generate sample JSON data"""
    return [{"id": i, "data": "x" * 100, "value": i * 2} for i in range(size)]

def send_uncompressed(data):
    """UNOPTIMISED: Send raw JSON"""
    json_str = json.dumps(data)
    return len(json_str), json_str

def send_compressed(data):
    """OPTIMISED: Send gzip compressed JSON"""
    json_str = json.dumps(data)
    compressed = gzip.compress(json_str.encode('utf-8'))
    return len(compressed), compressed

def demo_compression():
    print("--- Response Compression ---\n")
    data = generate_sample_data(1000)
    
    uncompressed_size, _ = send_uncompressed(data)
    compressed_size, _ = send_compressed(data)
    
    print(f"Uncompressed size: {uncompressed_size:,} bytes")
    print(f"Compressed size: {compressed_size:,} bytes")
    print(f"Compression ratio: {uncompressed_size/compressed_size:.1f}x")
    print(f"Bandwidth saved: {(1 - compressed_size/uncompressed_size)*100:.1f}%")
    print()


# Example 4: Caching with ETags
class ResourceCache:
    def __init__(self):
        self.cache = {}
    
    def get_etag(self, data):
        """Generate ETag from data"""
        return hashlib.md5(json.dumps(data).encode()).hexdigest()
    
    def fetch_with_cache(self, resource_id, if_none_match=None):
        """OPTIMIZED: Return 304 if content unchanged"""
        # Simulate fetching resource
        data = {"id": resource_id, "content": f"Content for {resource_id}"}
        etag = self.get_etag(data)
        
        if if_none_match == etag:
            # Content unchanged, return 304 Not Modified
            return {"status": 304, "etag": etag, "data": None}
        else:
            # Content changed or first request, return full data
            return {"status": 200, "etag": etag, "data": data}

def demo_etag_caching():
    print("--- ETag Caching ---\n")
    cache = ResourceCache()
    
    # First request
    response1 = cache.fetch_with_cache("resource1")
    print(f"First request: Status {response1['status']}, Data size: {len(json.dumps(response1['data']))} bytes")
    
    # Second request with ETag
    response2 = cache.fetch_with_cache("resource1", if_none_match=response1['etag'])
    print(f"Cached request: Status {response2['status']}, No data transfer needed")
    print(f"Bandwidth saved: ~100% for unchanged resources")
    print()


# Example 5: Parallel Requests
def fetch_resource(resource_id):
    """Simulate fetching a resource"""
    simulate_network_delay(100)
    return {"id": resource_id, "data": f"Resource {resource_id}"}

def fetch_all_sequential(resource_ids):
    """UNOPTIMISED: Fetch resources one by one"""
    start = time.time()
    resources = [fetch_resource(rid) for rid in resource_ids]
    elapsed = time.time() - start
    return resources, elapsed

def fetch_all_parallel(resource_ids, max_workers=5):
    """OPTIMISED: Fetch multiple resources in parallel"""
    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        resources = list(executor.map(fetch_resource, resource_ids))
    elapsed = time.time() - start
    return resources, elapsed

def demo_parallel_requests():
    print("--- Parallel Requests ---\n")
    resource_ids = list(range(1, 11))
    
    resources1, time1 = fetch_all_sequential(resource_ids)
    print(f"Sequential fetching (10 resources): {time1:.3f}s")
    
    resources2, time2 = fetch_all_parallel(resource_ids, max_workers=5)
    print(f"Parallel fetching (5 workers): {time2:.3f}s ({time1/time2:.1f}x faster)")
    print()


# Example 6: Payload Optimisation
def send_full_object():
    """UNOPTIMISED: Send full object with unnecessary fields"""
    data = {
        "id": 1,
        "name": "Product",
        "description": "A" * 1000,  # Large field
        "internal_notes": "B" * 500,  # Not needed by client
        "metadata": {"created": "2024-01-01", "modified": "2024-01-02"},
        "price": 99.99,
        "stock": 100
    }
    return len(json.dumps(data))

def send_minimal_object():
    """OPTIMISED: Send only needed fields"""
    data = {
        "id": 1,
        "name": "Product",
        "price": 99.99,
        "stock": 100
    }
    return len(json.dumps(data))

def demo_payload_optimization():
    print("--- Payload Optimisation ---\n")
    
    full_size = send_full_object()
    minimal_size = send_minimal_object()
    
    print(f"Full object size: {full_size:,} bytes")
    print(f"Minimal object size: {minimal_size:,} bytes")
    print(f"Payload reduced by: {(1 - minimal_size/full_size)*100:.1f}%")
    print()


# Example 7: GraphQL vs REST
def rest_api_calls():
    """UNOPTIMISED: Multiple REST endpoints"""
    # Need to make 3 separate requests
    simulate_network_delay(50)  # GET /users/1
    simulate_network_delay(50)  # GET /users/1/posts
    simulate_network_delay(50)  # GET /users/1/comments
    return 150  # Total time in ms

def graphql_query():
    """OPTIMISED: Single GraphQL query"""
    # Single request fetches all needed data
    simulate_network_delay(50)  # POST /graphql with nested query
    return 50  # Total time in ms

def demo_graphql_vs_rest():
    print("--- GraphQL vs REST ---\n")
    
    rest_time = rest_api_calls()
    print(f"REST (3 separate requests): {rest_time}ms")
    
    graphql_time = graphql_query()
    print(f"GraphQL (1 request): {graphql_time}ms ({rest_time/graphql_time:.1f}x faster)")
    print()



def main():
    print("=" * 40)
    print("NETWORK AND API OPTIMISATION BENCHMARKS")
    print("=" * 40 + "\n")
    
    demo_request_batching()
    demo_connection_pooling()
    demo_compression()
    demo_etag_caching()
    demo_parallel_requests()
    demo_payload_optimization()
    demo_graphql_vs_rest()
    
    print("\n--- Key Takeaways ---")
    print("1. Batch multiple requests into single calls")
    print("2. Use connection pooling to avoid overhead")
    print("3. Enable gzip compression for responses")
    print("4. Implement caching with ETags/Last-Modified")
    print("5. Make parallel requests when possible")
    print("6. Send only necessary data in payloads")
    print("7. Consider GraphQL for complex, nested data")
    print("8. Use CDNs for static assets")
    print("9. Implement request throttling/debouncing")
    print("10. Monitor and optimise based on metrics")

if __name__ == "__main__":
    main()
