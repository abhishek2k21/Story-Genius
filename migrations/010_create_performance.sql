-- Migration 010: Create Performance Metrics Table

CREATE TABLE video_performance (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    platform VARCHAR(20) DEFAULT 'youtube_shorts',
    title VARCHAR(255),
    views INT DEFAULT 0,
    watch_time_seconds INT DEFAULT 0,
    avg_retention_percent FLOAT,
    retention_at_3s FLOAT,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_perf_views ON video_performance(views DESC);
CREATE INDEX idx_perf_job ON video_performance(job_id);
