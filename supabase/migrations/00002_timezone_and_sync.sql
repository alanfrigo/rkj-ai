-- ===========================================
-- Meeting Assistant - Timezone and Sync Features
-- ===========================================
-- Migration: 00002_timezone_and_sync.sql
-- Description: 
--   1. Sets database timezone to America/Sao_Paulo
--   2. Updates calendar_events timezone default
--   3. Adds is_excluded column for soft delete
--   4. Adds index for excluded events filtering

-- -------------------------------------------
-- Set Database Timezone
-- -------------------------------------------
-- Note: This affects the default timezone for new connections
ALTER DATABASE postgres SET timezone TO 'America/Sao_Paulo';

-- -------------------------------------------
-- Update calendar_events Table
-- -------------------------------------------

-- Change timezone column default from UTC to America/Sao_Paulo
ALTER TABLE public.calendar_events 
ALTER COLUMN timezone SET DEFAULT 'America/Sao_Paulo';

-- Add is_excluded column for soft delete (exclude event from system without deleting from real calendar)
ALTER TABLE public.calendar_events 
ADD COLUMN IF NOT EXISTS is_excluded BOOLEAN DEFAULT false NOT NULL;

-- Update existing events with UTC timezone to use the new default
-- Note: TIMESTAMPTZ values are stored as UTC internally, this only updates the display timezone preference
UPDATE public.calendar_events 
SET timezone = 'America/Sao_Paulo' 
WHERE timezone = 'UTC';

-- -------------------------------------------
-- Add Index for Excluded Events
-- -------------------------------------------
-- Optimizes queries that filter out excluded events
CREATE INDEX IF NOT EXISTS idx_calendar_events_not_excluded 
ON public.calendar_events(user_id, start_time) 
WHERE is_excluded = false;

-- -------------------------------------------
-- Update Users Settings Default
-- -------------------------------------------
-- Add auto_sync_calendar to the default settings JSONB
-- This will add the field to the default for new users
ALTER TABLE public.users
ALTER COLUMN settings SET DEFAULT '{
    "auto_record": true,
    "default_language": "pt-BR",
    "notifications_enabled": true,
    "email_notifications": true,
    "auto_sync_calendar": true
}'::jsonb;
