-- Migration 009: Create Content Calendar Tables

CREATE TABLE content_calendar (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    plan_name VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    frequency INT,
    themes JSONB,
    status VARCHAR(20) DEFAULT 'draft',
    brand_kit_id UUID, -- FK to brand_kits
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE calendar_slots (
    id UUID PRIMARY KEY,
    calendar_id UUID REFERENCES content_calendar(id) ON DELETE CASCADE,
    slot_date DATE NOT NULL,
    slot_time TIME,
    theme VARCHAR(100),
    topic TEXT,
    job_id UUID,  -- FK to jobs table, NULL until generated
    preview_id UUID, -- FK to previews, optional
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_calendar_user ON content_calendar(user_id);
CREATE INDEX idx_slots_calendar ON calendar_slots(calendar_id);
