class CustomMock:
    def __init__(self):
        self._calls = []
        self._return_value = None
    
    def return_value(self, value):
        self._return_value = value
    
    def __call__(self, *args, **kwargs):
        self._calls.append((args, kwargs))
        return self._return_value
    
    def assert_called_with(self, *args, **kwargs):
        assert (args, kwargs) in self._calls, f"Expected call with {args}, {kwargs}, but got {self._calls}"

# example
def fetch_data(url):
    # simulating a function that fetches data from a URL
    return "data from " + url

def process_data(fetch):
    data = fetch("http://example.com")
    return f"Processed {data}"

# create mock for the `fetch` function
mock_fetch = CustomMock()
mock_fetch.return_value("mocked data")

# use mock in the test
result = process_data(mock_fetch)

# test the result
print(result)  # process mocked data

# verify the mock was called with the expected arguments
mock_fetch.assert_called_with("http://example.com")
