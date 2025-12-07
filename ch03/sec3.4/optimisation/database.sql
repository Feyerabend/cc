-- ============================================
-- DATABASE QUERY OPTIMISATION EXAMPLES
-- ============================================

-- Example 1: Index Usage
-- ============================================

-- UNOPTIMISED: Full table scan
SELECT * FROM users WHERE email = 'john@example.com';
-- Without index: O(n) - scans all rows

-- OPTIMISED: Create index
CREATE INDEX idx_users_email ON users(email);
SELECT * FROM users WHERE email = 'john@example.com';
-- With index: O(log n) - fast lookup


-- Example 2: SELECT Optimisation
-- ============================================

-- UNOPTIMISED: Selecting all columns
SELECT * FROM users 
WHERE created_at > '2024-01-01';
-- Retrieves unnecessary data, larger I/O

-- OPTIMISED: Select only needed columns
SELECT id, email, username 
FROM users 
WHERE created_at > '2024-01-01';
-- Reduces data transfer and memory usage


-- Example 3: JOIN Optimisation
-- ============================================

-- UNOPTIMISED: Multiple separate queries (N+1 problem)
-- SELECT * FROM orders WHERE user_id = 1;
-- SELECT * FROM orders WHERE user_id = 2;
-- ... (one query per user)

-- OPTIMISED: Single JOIN query
SELECT u.username, o.order_id, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.active = 1;
-- Single query, efficient join


-- Example 4: Subquery vs JOIN
-- ============================================

-- UNOPTIMISED: Correlated subquery
SELECT u.username,
       (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count
FROM users u;
-- Executes subquery for each row

-- OPTIMISED: JOIN with GROUP BY
SELECT u.username, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username;
-- Single scan, more efficient


-- Example 5: WHERE vs HAVING
-- ============================================

-- UNOPTIMISED: Filtering after aggregation
SELECT user_id, COUNT(*) as order_count
FROM orders
GROUP BY user_id
HAVING user_id > 1000;
-- Groups all rows first, then filters

-- OPTIMISED: Filter before aggregation
SELECT user_id, COUNT(*) as order_count
FROM orders
WHERE user_id > 1000
GROUP BY user_id;
-- Filters first, then groups fewer rows


-- Example 6: LIKE Optimisation
-- ============================================

-- UNOPTIMISED: Leading wildcard
SELECT * FROM products WHERE name LIKE '%phone%';
-- Cannot use index, full table scan

-- OPTIMISED: Prefix search (when possible)
SELECT * FROM products WHERE name LIKE 'phone%';
-- Can use index on 'name'

-- BETTER: Full-text search for complex patterns
CREATE FULLTEXT INDEX idx_products_name ON products(name);
SELECT * FROM products WHERE MATCH(name) AGAINST('phone' IN NATURAL LANGUAGE MODE);


-- Example 7: DISTINCT Optimisation
-- ============================================

-- UNOPTIMISED: DISTINCT on large result set
SELECT DISTINCT user_id 
FROM orders 
WHERE created_at > '2024-01-01';
-- Must sort/hash all results

-- OPTIMISED: GROUP BY (often faster)
SELECT user_id 
FROM orders 
WHERE created_at > '2024-01-01'
GROUP BY user_id;
-- Can use indexes more efficiently


-- Example 8: UNION vs UNION ALL
-- ============================================

-- UNOPTIMISED: UNION (removes duplicates)
SELECT id FROM table1
UNION
SELECT id FROM table2;
-- Adds deduplication overhead

-- OPTIMISED: UNION ALL (when duplicates are OK)
SELECT id FROM table1
UNION ALL
SELECT id FROM table2;
-- No deduplication, faster


-- Example 9: Pagination Optimisation
-- ============================================

-- UNOPTIMISED: OFFSET with large values
SELECT * FROM users 
ORDER BY created_at DESC
LIMIT 20 OFFSET 10000;
-- Must scan 10,020 rows

-- OPTIMISED: Keyset pagination
SELECT * FROM users 
WHERE created_at < '2024-01-01 12:00:00'
ORDER BY created_at DESC
LIMIT 20;
-- Uses index efficiently, constant time


-- Example 10: Batch Operations
-- ============================================

-- UNOPTIMISED: Multiple single inserts
INSERT INTO users (username, email) VALUES ('user1', 'user1@example.com');
INSERT INTO users (username, email) VALUES ('user2', 'user2@example.com');
INSERT INTO users (username, email) VALUES ('user3', 'user3@example.com');
-- Multiple round trips, transaction overhead

-- OPTIMISED: Batch insert
INSERT INTO users (username, email) VALUES 
    ('user1', 'user1@example.com'),
    ('user2', 'user2@example.com'),
    ('user3', 'user3@example.com');
-- Single statement, one transaction


-- Example 11: EXISTS vs IN
-- ============================================

-- UNOPTIMISED: IN with subquery returning many rows
SELECT * FROM users
WHERE id IN (SELECT user_id FROM orders WHERE total > 100);
-- May load entire subquery result

-- OPTIMISED: EXISTS (stops at first match)
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o 
    WHERE o.user_id = u.id AND o.total > 100
);
-- Short-circuits on first match


-- Example 12: Covering Index
-- ============================================

-- UNOPTIMISED: Index doesn't cover query
CREATE INDEX idx_orders_user ON orders(user_id);
SELECT user_id, product_id, total FROM orders WHERE user_id = 100;
-- Must access table after index lookup

-- OPTIMISED: Covering index includes all columns
CREATE INDEX idx_orders_covering ON orders(user_id, product_id, total);
SELECT user_id, product_id, total FROM orders WHERE user_id = 100;
-- All data in index, no table access needed


-- Example 13: Avoiding Functions on Indexed Columns
-- ============================================

-- UNOPTIMISED: Function on indexed column
SELECT * FROM users WHERE YEAR(created_at) = 2024;
-- Cannot use index on created_at

-- OPTIMISED: Range query
SELECT * FROM users 
WHERE created_at >= '2024-01-01' 
  AND created_at < '2025-01-01';
-- Uses index on created_at


-- Example 14: Denormalisation for Read Performance
-- ============================================

-- NORMALISED (slower reads, better writes):
-- users: id, username
-- orders: id, user_id, total
-- Query: JOIN users and orders

-- DENORMALISED (faster reads, slower writes):
-- orders: id, user_id, username, total
-- Query: Direct SELECT from orders
-- Trade-off: Faster queries but more storage and update complexity


-- ============================================
-- INDEX STRATEGY EXAMPLES
-- ============================================

-- Composite index for multi-column queries
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);
-- Efficient for: WHERE user_id = X AND created_at > Y
-- Also works for: WHERE user_id = X (leftmost prefix)

-- Partial index (PostgreSQL)
CREATE INDEX idx_active_users ON users(email) WHERE active = true;
-- Smaller index, faster for active users only

-- Expression index (PostgreSQL)
CREATE INDEX idx_lower_email ON users(LOWER(email));
-- Supports case-insensitive searches efficiently


-- ============================================
-- QUERY ANALYSIS COMMANDS
-- ============================================

-- Analyze query performance
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- More detailed analysis (PostgreSQL)
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- MySQL equivalent
EXPLAIN FORMAT=JSON SELECT * FROM users WHERE email = 'test@example.com';


-- ============================================
-- KEY OPTIMISATION PRINCIPLES
-- ============================================

/*
1. INDEX STRATEGY
   - Create indexes on frequently queried columns
   - Use composite indexes for multi-column queries
   - Consider covering indexes for specific queries
   - Don't over-index (slows writes)

2. QUERY DESIGN
   - Select only needed columns
   - Filter as early as possible (WHERE before HAVING)
   - Use JOINs instead of multiple queries
   - Avoid functions on indexed columns

3. DATA ACCESS PATTERNS
   - Use keyset pagination for large offsets
   - Batch operations when possible
   - Consider denormalization for read-heavy workloads
   - Use EXISTS for existence checks

4. MONITORING
   - Use EXPLAIN to analyse query plans
   - Monitor slow query logs
   - Track query execution times
   - Profile before optimising

5. CACHING
   - Cache frequent queries at application level
   - Use materialied views for complex aggregations
   - Consider query result caching
   - Implement connection pooling
*/
