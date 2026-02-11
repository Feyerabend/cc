class CustomDatabaseMock:
    def __init__(self):
        self._calls = []
        self._return_value = None
    
    def return_value(self, value):
        self._return_value = value
    
    def cursor(self):
        return self  # in reality, this would return a cursor object
    
    def execute(self, query, params):
        self._calls.append(('execute', query, params))  # track query executed
    
    def fetchone(self):
        self._calls.append(('fetchone',))  # track fetchone call
        return self._return_value  # simulate behavior of fetchone
    
    def assert_called(self):
        assert len(self._calls) > 0, "No method was called"
    
    def assert_called_with(self, method, *args):
        assert any(call[0] == method and call[1:] == args for call in self._calls), f"Method {method} was not called with {args}"


# Define the function that queries the database
def get_user_details(user_id, db_connection):
    # Simulating querying a database to get user details
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    return user


# Test code
mock_db = CustomDatabaseMock()
mock_db.return_value((1, 'John Doe', 'john.doe@example.com'))

# Use the mock in the test
user_details = get_user_details(1, mock_db)

# Test the result
print(user_details)  # Output: (1, 'John Doe', 'john.doe@example.com')

# Verify the mock methods were called with expected arguments
mock_db.assert_called_with('execute', "SELECT * FROM users WHERE id=?", (1,))
mock_db.assert_called_with('fetchone')
