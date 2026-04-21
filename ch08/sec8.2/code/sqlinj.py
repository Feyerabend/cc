import sqlite3

# Vulnerable: string concatenation lets a user escape the query
def find_user_bad(conn, username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return conn.execute(query).fetchall()   # username = "' OR '1'='1" dumps every row

# Safe: parameterized query; the driver keeps data and SQL structure separate
def find_user_safe(conn, username):
    return conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchall()
