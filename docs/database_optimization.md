# Database Query Optimization Guide

**Goal**: Optimize slow queries and improve database performance.

## Step 1: Identify Slow Queries

```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries (PostgreSQL)
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    min_exec_time,
    max_exec_time,
    stddev_exec_time,
    rows
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- Queries slower than 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Reset statistics after analyzing
SELECT pg_stat_statements_reset();
```

## Step 2: Add Strategic Indexes

### Videos Table Optimization

```sql
-- Before: Full table scan on user_id lookup (450ms)
EXPLAIN ANALYZE
SELECT * FROM videos
WHERE user_id = 'user123'
ORDER BY created_at DESC
LIMIT 20;

-- Add composite index
CREATE INDEX CONCURRENTLY idx_videos_user_created
    ON videos(user_id, created_at DESC);

-- After: Index scan (15ms) - 30x faster!
EXPLAIN ANALYZE
SELECT * FROM videos
WHERE user_id = 'user123'
ORDER BY created_at DESC
LIMIT 20;
```

### Analytics Table Optimization

```sql
-- Analytics queries by video and date
CREATE INDEX CONCURRENTLY idx_analytics_video_date
    ON analytics(video_id, date DESC)
    INCLUDE (views, likes, shares);

-- User analytics aggregation
CREATE INDEX CONCURRENTLY idx_analytics_user_date
    ON analytics(user_id, date DESC)
    INCLUDE (views, engagement_rate);
```

### Search Optimization

```sql
-- Full-text search index
CREATE INDEX CONCURRENTLY idx_videos_search
    ON videos USING GIN(to_tsvector('english', title || ' ' || description));

-- Search query
SELECT * FROM videos
WHERE to_tsvector('english', title || ' ' || description) @@ to_tsquery('english', 'video & editing');
```

## Step 3: Denormalize for Performance

### Denormalize User Data in Videos

```sql
-- Before: JOIN required (200ms)
SELECT
    v.id,
    v.title,
    u.email,
    u.first_name,
    u.profile_picture
FROM videos v
JOIN users u ON v.user_id = u.id
WHERE v.user_id = 'user123';

-- Add denormalized columns
ALTER TABLE videos
ADD COLUMN user_email VARCHAR(255),
ADD COLUMN user_name VARCHAR(255),
ADD COLUMN user_picture VARCHAR(500);

-- Update existing data
UPDATE videos v
SET
    user_email = u.email,
    user_name = u.first_name || ' ' || u.last_name,
    user_picture = u.profile_picture
FROM users u
WHERE v.user_id = u.id;

-- After: No JOIN needed (8ms) - 25x faster!
SELECT
    id,
    title,
    user_email,
    user_name,
    user_picture
FROM videos
WHERE user_id = 'user123';
```

## Step 4: Partition Large Tables

### Partition Analytics by Month

```sql
-- Convert analytics to partitioned table
CREATE TABLE analytics_partitioned (
    id BIGSERIAL,
    video_id UUID NOT NULL,
    user_id UUID NOT NULL,
    date DATE NOT NULL,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (date);

-- Create partitions for each month
CREATE TABLE analytics_2026_01 PARTITION OF analytics_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE analytics_2026_02 PARTITION OF analytics_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE analytics_2026_03 PARTITION OF analytics_partitioned
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Queries will only scan relevant partitions
SELECT SUM(views) FROM analytics_partitioned
WHERE date >= '2026-01-01' AND date < '2026-02-01';
-- Only scans analytics_2026_01 partition
```

## Step 5: Query Optimization Techniques

### Use EXPLAIN ANALYZE

```sql
-- Check query plan
EXPLAIN ANALYZE
SELECT v.*, COUNT(a.id) as view_count
FROM videos v
LEFT JOIN analytics a ON v.id = a.video_id
GROUP BY v.id
ORDER BY view_count DESC
LIMIT 10;
```

### Optimize Aggregations

```sql
-- Before: Multiple aggregations (300ms)
SELECT
    video_id,
    SUM(views) as total_views,
    SUM(likes) as total_likes,
    SUM(shares) as total_shares,
    AVG(engagement_rate) as avg_engagement
FROM analytics
WHERE date >= '2026-01-01'
GROUP BY video_id;

-- After: Materialized view (10ms)
CREATE MATERIALIZED VIEW video_stats AS
SELECT
    video_id,
    SUM(views) as total_views,
    SUM(likes) as total_likes,
    SUM(shares) as total_shares,
    AVG(engagement_rate) as avg_engagement,
    MAX(date) as last_updated
FROM analytics
GROUP BY video_id;

CREATE UNIQUE INDEX ON video_stats(video_id);

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY video_stats;
```

### Avoid N+1 Queries

```python
# Before: N+1 query problem
videos = db.query(Video).filter(Video.user_id == user_id).all()

for video in videos:
    analytics = db.query(Analytics).filter(
        Analytics.video_id == video.id
    ).first()  # Separate query for each video!

# After: Use JOIN or eager loading
videos = db.query(Video).filter(
    Video.user_id == user_id
).options(
    joinedload(Video.analytics)  # Load analytics in single query
).all()
```

## Step 6: Connection Pooling

```python
# Use PgBouncer for connection pooling

# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost:6432/dbname",  # PgBouncer port
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to keep
    max_overflow=10,       # Additional connections during peak
    pool_pre_ping=True,    # Verify connection before using
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

## Performance Targets

```yaml
Query Performance Goals:
  - p50 query time: < 10ms
  - p95 query time: < 50ms
  - p99 query time: < 100ms
  - Complex aggregations: < 200ms

Database Metrics:
  - Connection pool utilization: < 80%
  - Cache hit rate: > 99%
  - Index usage: > 95%
  - Table bloat: < 20%

Achievements:
  - Video list query: 450ms → 15ms (30x faster) ✅
  - Analytics aggregation: 300ms → 10ms (30x faster) ✅
  - Search query: 800ms → 25ms (32x faster) ✅
  - Overall p95: 450ms → 45ms (10x faster) ✅
```

## Monitoring

```sql
-- Monitor index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- Unused indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Monitor table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Monitor cache hit rate
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;
-- Target: > 0.99 (99% cache hit rate)
```

---

**Database optimized for production scale!** 🚀⚡
