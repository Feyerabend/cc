
## Mocking in Python Testing

Imagine you're building a weather app. Your code needs to fetch temperature data
from an external API, but you don't want your tests to:
- Actually call the API thousands of times (expensive and slow)
- Break when you're offline or the API is down
- Fail because the weather changed between test runs

This is where *mocking* comes in. Mocking lets you simulate external dependencies
so you can test your code in isolation, reliably, and fast.


### So What is Mocking?

Mocking is like using a stunt double in a movie. The stunt double (mock) stands in
for the real actor (external dependency) during dangerous scenes (tests). You control
exactly what the stunt double does, so your tests are predictable and safe.

In technical terms: *A mock is a fake object that simulates the
behaviour of real objects in controlled ways.*

### Your First Mock: A Simple Example

Let's start with something relatable--a function that checks if you should bring
an umbrella based on weather data.

```python
import requests

def should_bring_umbrella(city):
    """Check if it will rain today in the given city."""
    response = requests.get(f"https://api.weather.com/v3/forecast/{city}")
    weather_data = response.json()
    return weather_data['precipitation_chance'] > 50

# Usage
if should_bring_umbrella("London"):
    print("Grab an umbrella!")
```

*The Problem with Testing This*

If we test this function without mocking:

```python
# BAD: This actually calls the API!
def test_umbrella_recommendation():
    result = should_bring_umbrella("London")
    # What should we assert? The weather is unpredictable!
```

This test has problems:

1. *Slow* .. network requests take time
2. *Unreliable* .. fails when offline
3. *Unpredictable* .. weather changes
4. *Wasteful* .. costs API quota

*Solution: Mock It!*

```python
import unittest
from unittest.mock import patch
from weather_app import should_bring_umbrella

class TestUmbrella(unittest.TestCase):
    
    @patch('weather_app.requests.get')
    def test_recommends_umbrella_when_rainy(self, mock_get):
        # Arrange: Set up our fake response
        mock_get.return_value.json.return_value = {
            'precipitation_chance': 80  # 80% chance of rain
        }
        
        # Act: Call the function
        result = should_bring_umbrella("London")
        
        # Assert: Check the result
        self.assertTrue(result)
        
        # Verify: Make sure the API was called correctly
        mock_get.assert_called_once_with(
            "https://api.weather.com/v3/forecast/London"
        )
    
    @patch('weather_app.requests.get')
    def test_no_umbrella_when_sunny(self, mock_get):
        # Arrange: Sunny day
        mock_get.return_value.json.return_value = {
            'precipitation_chance': 10  # Only 10% chance
        }
        
        # Act
        result = should_bring_umbrella("London")
        
        # Assert
        self.assertFalse(result)
```

Let's it break down:
1. *`@patch('weather_app.requests.get')`* - This decorator replaces `requests.get` with a mock object during the test
2. *`mock_get`* - This is the mock object, automatically passed as a parameter
3. *`mock_get.return_value.json.return_value`* - This sets what the mock returns when we call `requests.get().json()`
4. *`mock_get.assert_called_once_with(...)`* - This verifies the function called the API correctly

Think of it like this:
```
Real flow:  requests.get() -> actual API → real JSON response
Mock flow:  mock_get()     -> fake object → predetermined JSON
```


### Mock Chains

The notation `mock_get.return_value.json.return_value` might look confusing.

```python
# When you write this in your code:
response = requests.get(url)
data = response.json()

# The mock needs to handle this chain:
# 1. requests.get(url) returns something
# 2. That something has a .json() method
# 3. That .json() method returns data

# So you set it up like:
mock_get.return_value.json.return_value = {'key': 'value'}

# Breaking it down:
mock_get                    # The mocked requests.get function
.return_value               # What it returns when called (the response object)
.json                       # The json method on that response
.return_value               # What json() returns
```

### Database Mocking

```python
import sqlite3

def get_user_by_id(user_id):
    """Fetch a user from the database."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def format_user_greeting(user_id):
    """Get a personalized greeting for a user."""
    user = get_user_by_id(user_id)
    if user:
        return f"Hello, {user[1]}! Your email is {user[2]}"
    return "User not found"
```

*Test*

```python
import unittest
from unittest.mock import patch, MagicMock
from user_service import format_user_greeting

class TestUserGreeting(unittest.TestCase):
    
    @patch('user_service.sqlite3.connect')
    def test_greeting_for_existing_user(self, mock_connect):
        # Create a mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'Alice', 'alice@example.com')
        
        # Make the connection return our mock cursor
        mock_connect.return_value.cursor.return_value = mock_cursor
        
        # Call the function
        greeting = format_user_greeting(1)
        
        # Check the result
        self.assertEqual(greeting, "Hello, Alice! Your email is alice@example.com")
        
        # Verify database interactions
        mock_connect.assert_called_once_with('users.db')
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, name, email FROM users WHERE id=?", (1,)
        )
        mock_cursor.fetchone.assert_called_once()
    
    @patch('user_service.sqlite3.connect')
    def test_greeting_for_missing_user(self, mock_connect):
        # Mock cursor returns None (user not found)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value.cursor.return_value = mock_cursor
        
        # Call the function
        greeting = format_user_greeting(999)
        
        # Check we got the "not found" message
        self.assertEqual(greeting, "User not found")
```

### When To Mock?

*Good times to mock:*

- External APIs and web services
- Databases
- File system operations
- Time-dependent code (clocks, timers)
- Random number generators
- Email/SMS services
- Third-party libraries
- Slow operations

*Bad times to mock:*

- Simple pure functions (just test them directly)
- Your own business logic (you want to test that!)
- Data structures and models
- Simple calculations

*The golden rule:* Mock the boundaries of your system, not the core logic.


### Pitfall 1: Mocking in the Wrong Place

```python
# WRONG: Mocking where it's imported FROM
@patch('requests.get')  # Won't work if you imported it in your module

# RIGHT: Mock where it's USED
@patch('my_module.requests.get')  # Correct
```

*Why?* Python patches the object in the namespace where it's used, not where it's defined.

### Pitfall 2: Over-Mocking

```python
# BAD: Mocking too much
@patch('my_module.user_service')
@patch('my_module.database')
@patch('my_module.cache')
@patch('my_module.logger')
def test_something(self, mock_logger, mock_cache, mock_db, mock_service):
    # If you're mocking everything, what are you actually testing?
    pass
```

If your test has more mocks than code, you might be testing the wrong thing.

### Pitfall 3: Not Verifying Mock Calls

```python
# INCOMPLETE: Sets up mock but doesn't verify it was used correctly
@patch('my_module.send_email')
def test_notification(self, mock_send):
    mock_send.return_value = True
    notify_user(user_id=1)
    # Missing: Did we actually call send_email with the right arguments?
```

```python
# BETTER: Verify the mock was called correctly
@patch('my_module.send_email')
def test_notification(self, mock_send):
    mock_send.return_value = True
    notify_user(user_id=1)
    
    # Verify it was called with the right arguments
    mock_send.assert_called_once_with(
        to='user@example.com',
        subject='Notification',
        body='You have a new message'
    )
```

### Building Your Own Mock

While `unittest.mock` is powerful and should be your go-to in production,
building a simple mock yourself is a great learning exercise.

#### A Minimal Mock Class

```python
class SimpleMock:
    """A basic mock that tracks calls and returns a value."""
    
    def __init__(self):
        self.calls = []
        self.return_value = None
    
    def __call__(self, *args, *kwargs):
        """Called when the mock is invoked like a function."""
        self.calls.append((args, kwargs))
        return self.return_value
    
    def set_return_value(self, value):
        """Set what this mock should return."""
        self.return_value = value
    
    def was_called_with(self, *args, *kwargs):
        """Check if the mock was called with specific arguments."""
        return (args, kwargs) in self.calls
    
    def call_count(self):
        """How many times was this mock called?"""
        return len(self.calls)

# Example usage
def add_user(user, database):
    """Add a user to the database."""
    database.insert('users', user)
    return True

# Test it
mock_db = SimpleMock()
mock_db.set_return_value(True)

result = add_user({'name': 'Bob'}, mock_db)

print(f"Function returned: {result}")
print(f"Database called {mock_db.call_count()} times")
print(f"Called with Bob: {mock_db.was_called_with('users', {'name': 'Bob'})}")
```

#### More Advanced Mock with Attributes

```python
class MockDatabase:
    """A mock database with common operations."""
    
    def __init__(self):
        self.calls = []
        self._data = {}
    
    def insert(self, table, record):
        """Simulate inserting a record."""
        self.calls.append(('insert', table, record))
        if table not in self._data:
            self._data[table] = []
        self._data[table].append(record)
    
    def query(self, table, id):
        """Simulate querying a record."""
        self.calls.append(('query', table, id))
        if table in self._data:
            for record in self._data[table]:
                if record.get('id') == id:
                    return record
        return None
    
    def verify_insert_called(self, table, record):
        """Verify insert was called with specific data."""
        assert ('insert', table, record) in self.calls, \
            f"insert not called with {table}, {record}"

# Example usage
def save_and_retrieve_user(user_data, db):
    """Save a user and then retrieve it."""
    db.insert('users', user_data)
    return db.query('users', user_data['id'])

# Test it
mock_db = MockDatabase()
user = {'id': 1, 'name': 'Charlie'}

result = save_and_retrieve_user(user, mock_db)

print(f"Retrieved user: {result}")
mock_db.verify_insert_called('users', user)
print("Test passed!")
```

### Mock .. Stub .. Fake .. Spy

You might hear these terms used interchangeably, but they're technically different:

*Mock*: Verifies that certain methods were called with expected arguments
```python
mock.send_email.assert_called_with(to='user@example.com')
```

*Stub*: Returns predetermined values without verification
```python
stub.get_user.return_value = {'name': 'Test User'}
```

*Fake*: A simplified working implementation
```python
class FakeDatabase:
    def __init__(self):
        self.data = {}  # Actually stores data, but in memory
```

*Spy*: Wraps a real object and tracks calls while preserving real behavior
```python
spy = Mock(wraps=real_object)  # Calls real methods but tracks them
```

In `unittest.mock`, a `Mock` object can act as any of these depending on how you use it!


### Best Practices Checklist

*Do:*
- Mock external dependencies (APIs, databases, file systems)
- Use descriptive test names that explain what you're testing
- Verify that mocks were called with correct arguments
- Test both success and failure cases
- Keep each test focused on one thing

*Don't:*
- Mock everything (test your actual logic!)
- Forget to verify mock interactions
- Make tests that are harder to read than the code they test
- Use mocks when a simple direct test would work
- Mock your own business logic


### Real-World Example: Email Service

Here's a complete example showing good mocking practices:

```python
# email_service.py
import smtplib
from email.mime.text import MIMEText

class EmailService:
    def __init__(self, smtp_host, smtp_port):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
    
    def send_welcome_email(self, user_email, username):
        """Send a welcome email to a new user."""
        msg = MIMEText(f"Welcome {username}! Thanks for signing up.")
        msg['Subject'] = 'Welcome to Our Service'
        msg['From'] = 'noreply@example.com'
        msg['To'] = user_email
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.send_message(msg)
        
        return True

# test_email_service.py
import unittest
from unittest.mock import patch, MagicMock
from email_service import EmailService

class TestEmailService(unittest.TestCase):
    
    def setUp(self):
        """Run before each test."""
        self.service = EmailService('smtp.example.com', 587)
    
    @patch('email_service.smtplib.SMTP')
    def test_sends_welcome_email_successfully(self, mock_smtp):
        # Arrange
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Act
        result = self.service.send_welcome_email(
            'newuser@example.com',
            'Alice'
        )
        
        # Assert
        self.assertTrue(result)
        mock_smtp.assert_called_once_with('smtp.example.com', 587)
        
        # Verify the email was sent
        self.assertEqual(mock_server.send_message.call_count, 1)
        
        # Check the email content (first argument of send_message)
        sent_message = mock_server.send_message.call_args[0][0]
        self.assertIn('Welcome Alice', sent_message.get_payload())
        self.assertEqual(sent_message['To'], 'newuser@example.com')
        self.assertEqual(sent_message['Subject'], 'Welcome to Our Service')
    
    @patch('email_service.smtplib.SMTP')
    def test_handles_smtp_errors_gracefully(self, mock_smtp):
        # Arrange
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.service.send_welcome_email('user@example.com', 'Bob')
        
        self.assertIn("SMTP connection failed", str(context.exception))

if __name__ == '__main__':
    unittest.main()
```


### Common Mock Patterns

```python
# Set return value
mock.method.return_value = 'result'

# Set return value for chained calls
mock.method.return_value.another_method.return_value = 'result'

# Raise an exception
mock.method.side_effect = ValueError("Error message")

# Return different values on successive calls
mock.method.side_effect = [1, 2, 3]

# Call a custom function
def custom_logic(*args, *kwargs):
    return args[0] * 2
mock.method.side_effect = custom_logic

# Verify called once
mock.method.assert_called_once()

# Verify called with specific arguments
mock.method.assert_called_with(arg1, arg2, key='value')

# Verify called at least once
mock.method.assert_called()

# Verify never called
mock.method.assert_not_called()

# Get all calls
all_calls = mock.method.call_args_list

# Check number of calls
call_count = mock.method.call_count
```


### Conclusion

Mocking lets you:
- *Test in isolation* - Focus on one piece of code at a time
- *Test reliably* - No dependence on external services
- *Test fast* - No waiting for network or disk I/O
- *Test edge cases* - Simulate errors and unusual conditions easily

Remember: *Mock the boundaries, test the logic.*
Use mocks for external dependencies, but test your actual business logic with real code.

