-- Migration 008: Create Brand Kits Table

CREATE TABLE brand_kits (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL, -- FK to users table assumed
    name VARCHAR(100) NOT NULL,
    visual_style VARCHAR(50),
    voice_preference VARCHAR(50),
    color_palette JSONB,
    intro_template TEXT,
    outro_template TEXT,
    logo_url TEXT,
    watermark_text VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_brand_kits_user ON brand_kits(user_id);
