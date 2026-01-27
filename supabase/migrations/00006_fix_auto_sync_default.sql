-- ===========================================
-- Meeting Assistant - Fix auto_sync_calendar Default
-- ===========================================
-- Migration: 00006_fix_auto_sync_default.sql
-- Description: 
--   Ensures all users have auto_sync_calendar set to true by default.
--   This fixes any users who were created without this setting or 
--   accidentally had it set to false.

-- Update all users who don't have auto_sync_calendar set or have it as false
UPDATE public.users 
SET settings = COALESCE(settings, '{}'::jsonb) || '{"auto_sync_calendar": true}'::jsonb
WHERE 
    settings IS NULL 
    OR NOT (settings ? 'auto_sync_calendar')
    OR (settings->>'auto_sync_calendar')::boolean = false;

-- Log how many users were affected
DO $$
DECLARE
    affected_count INTEGER;
BEGIN
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RAISE NOTICE 'Updated % users to have auto_sync_calendar = true', affected_count;
END $$;
