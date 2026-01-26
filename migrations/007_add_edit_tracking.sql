-- Migration 007: Add edit tracking columns
-- Tracks manual overrides by creators

ALTER TABLE story_scenes ADD COLUMN edited_by_user BOOLEAN DEFAULT FALSE;
ALTER TABLE story_scenes ADD COLUMN original_narration TEXT;
ALTER TABLE story_scenes ADD COLUMN edit_timestamp TIMESTAMP;
ALTER TABLE story_scenes ADD COLUMN visual_prompt_edited BOOLEAN DEFAULT FALSE;
