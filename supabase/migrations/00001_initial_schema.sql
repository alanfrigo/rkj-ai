-- ===========================================
-- Meeting Assistant - Initial Schema
-- ===========================================
-- Migration: 00001_initial_schema.sql
-- Description: Creates all tables for the Meeting Assistant application

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -------------------------------------------
-- Users Table (extends Supabase Auth)
-- -------------------------------------------
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    -- Google OAuth tokens (encrypted)
    google_refresh_token TEXT,
    google_token_expires_at TIMESTAMPTZ,
    -- User preferences
    settings JSONB DEFAULT '{
        "auto_record": true,
        "default_language": "pt-BR",
        "notifications_enabled": true,
        "email_notifications": true
    }'::jsonb,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Trigger to auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- -------------------------------------------
-- Connected Calendars
-- -------------------------------------------
CREATE TABLE public.connected_calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    -- Calendar provider
    provider TEXT NOT NULL CHECK (provider IN ('google', 'outlook', 'apple')),
    -- External calendar ID (from provider)
    calendar_id TEXT NOT NULL,
    calendar_name TEXT,
    calendar_color TEXT,
    -- Sync settings
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    -- Google-specific: for incremental sync
    sync_token TEXT,
    -- Tracking
    last_synced_at TIMESTAMPTZ,
    events_count INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    -- Constraints
    UNIQUE(user_id, provider, calendar_id)
);

-- -------------------------------------------
-- Calendar Events
-- -------------------------------------------
CREATE TABLE public.calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    calendar_id UUID REFERENCES public.connected_calendars(id) ON DELETE SET NULL,
    -- External event ID (from Google/Outlook)
    external_event_id TEXT NOT NULL,
    -- Event details
    title TEXT NOT NULL DEFAULT 'Untitled Meeting',
    description TEXT,
    location TEXT,
    -- Timing
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    timezone TEXT DEFAULT 'America/Sao_Paulo',
    is_all_day BOOLEAN DEFAULT false,
    -- Meeting link detection
    meeting_url TEXT,
    meeting_provider TEXT CHECK (meeting_provider IN ('google_meet', 'zoom', 'teams', 'webex', 'other')),
    -- Participants
    organizer_email TEXT,
    attendees JSONB DEFAULT '[]'::jsonb,
    -- Recording settings
    should_record BOOLEAN DEFAULT true,
    recording_requested_by UUID REFERENCES public.users(id),
    -- Event status
    status TEXT DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'tentative', 'cancelled')),
    -- Recurrence
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT,
    recurring_event_id TEXT,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    -- Constraints
    UNIQUE(user_id, external_event_id)
);

-- -------------------------------------------
-- Meetings (Recorded Sessions)
-- -------------------------------------------
CREATE TABLE public.meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    calendar_event_id UUID REFERENCES public.calendar_events(id) ON DELETE SET NULL,
    -- Meeting info
    title TEXT NOT NULL,
    meeting_url TEXT,
    meeting_provider TEXT NOT NULL CHECK (meeting_provider IN ('google_meet', 'zoom', 'teams', 'webex', 'manual')),
    -- Status tracking
    status TEXT DEFAULT 'scheduled' NOT NULL CHECK (status IN (
        'scheduled',      -- Waiting to join
        'joining',        -- Bot is joining
        'waiting',        -- In waiting room
        'recording',      -- Actively recording
        'processing',     -- Post-processing video
        'transcribing',   -- Transcription in progress
        'completed',      -- All done
        'failed',         -- Error occurred
        'cancelled'       -- User cancelled
    )),
    -- Bot session
    bot_session_id TEXT,
    bot_container_id TEXT,
    -- Timing
    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    duration_seconds INTEGER,
    -- Participants
    participant_count INTEGER DEFAULT 0,
    participants JSONB DEFAULT '[]'::jsonb,
    -- Error handling
    error_message TEXT,
    error_code TEXT,
    retry_count INTEGER DEFAULT 0,
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -------------------------------------------
-- Recordings (Media Files)
-- -------------------------------------------
CREATE TABLE public.recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    -- File info
    file_type TEXT NOT NULL CHECK (file_type IN ('video', 'audio', 'screen', 'combined')),
    file_name TEXT NOT NULL,
    -- R2 Storage
    storage_bucket TEXT DEFAULT 'meeting-assistant',
    storage_path TEXT NOT NULL,
    storage_url TEXT,  -- Public/signed URL
    -- File metadata
    file_size_bytes BIGINT,
    duration_seconds INTEGER,
    format TEXT,  -- mp4, webm, mp3, etc.
    codec TEXT,   -- h264, vp9, aac, etc.
    -- Quality
    resolution TEXT,  -- 1920x1080, 1280x720, etc.
    bitrate_kbps INTEGER,
    framerate INTEGER,
    -- Processing
    is_processed BOOLEAN DEFAULT false,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    -- Thumbnail
    thumbnail_path TEXT,
    thumbnail_url TEXT,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -------------------------------------------
-- Transcriptions
-- -------------------------------------------
CREATE TABLE public.transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    recording_id UUID REFERENCES public.recordings(id) ON DELETE SET NULL,
    -- Transcription settings
    language TEXT DEFAULT 'pt-BR',
    -- Status
    status TEXT DEFAULT 'pending' NOT NULL CHECK (status IN (
        'pending',
        'processing',
        'completed',
        'failed'
    )),
    -- Content
    full_text TEXT,
    word_count INTEGER DEFAULT 0,
    -- Model info
    model_used TEXT DEFAULT 'whisper-1',
    model_version TEXT,
    -- Quality metrics
    confidence_score FLOAT,
    -- Processing info
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_duration_seconds INTEGER,
    -- Cost tracking
    audio_duration_seconds INTEGER,
    cost_cents INTEGER,  -- OpenAI cost in cents
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -------------------------------------------
-- Transcription Segments
-- -------------------------------------------
CREATE TABLE public.transcription_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id UUID NOT NULL REFERENCES public.transcriptions(id) ON DELETE CASCADE,
    -- Ordering
    segment_index INTEGER NOT NULL,
    -- Speaker identification
    speaker_id TEXT,      -- e.g., "SPEAKER_01"
    speaker_name TEXT,    -- Resolved name if available
    speaker_email TEXT,   -- If matched to attendee
    -- Timing (milliseconds for precision)
    start_time_ms INTEGER NOT NULL,
    end_time_ms INTEGER NOT NULL,
    -- Content
    text TEXT NOT NULL,
    -- Confidence
    confidence FLOAT,
    -- Word-level timestamps (optional)
    words JSONB,  -- [{word: "hello", start: 0, end: 500}, ...]
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    -- Index for ordering
    UNIQUE(transcription_id, segment_index)
);

-- -------------------------------------------
-- Processing Jobs (Queue Tracking)
-- -------------------------------------------
CREATE TABLE public.processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Reference
    meeting_id UUID REFERENCES public.meetings(id) ON DELETE CASCADE,
    recording_id UUID REFERENCES public.recordings(id) ON DELETE CASCADE,
    transcription_id UUID REFERENCES public.transcriptions(id) ON DELETE CASCADE,
    -- Job info
    job_type TEXT NOT NULL CHECK (job_type IN (
        'calendar_sync',
        'join_meeting',
        'recording',
        'media_processing',
        'audio_extraction',
        'transcription',
        'notification'
    )),
    -- Queue info
    queue_name TEXT NOT NULL,
    job_id TEXT,  -- External queue job ID (BullMQ)
    -- Status
    status TEXT DEFAULT 'queued' NOT NULL CHECK (status IN (
        'queued',
        'running',
        'completed',
        'failed',
        'cancelled',
        'retrying'
    )),
    priority INTEGER DEFAULT 0,
    -- Worker
    worker_id TEXT,
    worker_host TEXT,
    -- Timing
    queued_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    -- Retry handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    -- Error
    error_message TEXT,
    error_stack TEXT,
    -- Data
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB DEFAULT '{}'::jsonb,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -------------------------------------------
-- Indexes for Performance
-- -------------------------------------------

-- Users
CREATE INDEX idx_users_email ON public.users(email);

-- Connected Calendars
CREATE INDEX idx_connected_calendars_user ON public.connected_calendars(user_id);
CREATE INDEX idx_connected_calendars_active ON public.connected_calendars(user_id, is_active) WHERE is_active = true;

-- Calendar Events
CREATE INDEX idx_calendar_events_user ON public.calendar_events(user_id);
CREATE INDEX idx_calendar_events_time ON public.calendar_events(user_id, start_time);
CREATE INDEX idx_calendar_events_upcoming ON public.calendar_events(start_time, should_record) 
    WHERE should_record = true AND status = 'confirmed';
CREATE INDEX idx_calendar_events_meeting_url ON public.calendar_events(meeting_url) 
    WHERE meeting_url IS NOT NULL;

-- Meetings
CREATE INDEX idx_meetings_user ON public.meetings(user_id);
CREATE INDEX idx_meetings_status ON public.meetings(status);
CREATE INDEX idx_meetings_user_status ON public.meetings(user_id, status);
CREATE INDEX idx_meetings_scheduled ON public.meetings(scheduled_start) 
    WHERE status = 'scheduled';
CREATE INDEX idx_meetings_created ON public.meetings(user_id, created_at DESC);

-- Recordings
CREATE INDEX idx_recordings_meeting ON public.recordings(meeting_id);
CREATE INDEX idx_recordings_type ON public.recordings(meeting_id, file_type);

-- Transcriptions
CREATE INDEX idx_transcriptions_meeting ON public.transcriptions(meeting_id);
CREATE INDEX idx_transcriptions_status ON public.transcriptions(status);
CREATE INDEX idx_transcriptions_fulltext ON public.transcriptions USING gin(to_tsvector('portuguese', full_text));

-- Transcription Segments
CREATE INDEX idx_segments_transcription ON public.transcription_segments(transcription_id);
CREATE INDEX idx_segments_time ON public.transcription_segments(transcription_id, start_time_ms);
CREATE INDEX idx_segments_speaker ON public.transcription_segments(transcription_id, speaker_id);
CREATE INDEX idx_segments_fulltext ON public.transcription_segments USING gin(to_tsvector('portuguese', text));

-- Processing Jobs
CREATE INDEX idx_jobs_meeting ON public.processing_jobs(meeting_id);
CREATE INDEX idx_jobs_status ON public.processing_jobs(status);
CREATE INDEX idx_jobs_queue ON public.processing_jobs(queue_name, status);
CREATE INDEX idx_jobs_queued ON public.processing_jobs(queued_at) WHERE status = 'queued';

-- -------------------------------------------
-- Row Level Security (RLS)
-- -------------------------------------------

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.connected_calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcription_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

-- Connected Calendars policies
CREATE POLICY "Users can manage own calendars"
    ON public.connected_calendars FOR ALL
    USING (auth.uid() = user_id);

-- Calendar Events policies
CREATE POLICY "Users can view own events"
    ON public.calendar_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own events"
    ON public.calendar_events FOR ALL
    USING (auth.uid() = user_id);

-- Meetings policies
CREATE POLICY "Users can view own meetings"
    ON public.meetings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own meetings"
    ON public.meetings FOR ALL
    USING (auth.uid() = user_id);

-- Recordings policies (through meetings)
CREATE POLICY "Users can view own recordings"
    ON public.recordings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings
            WHERE meetings.id = recordings.meeting_id
            AND meetings.user_id = auth.uid()
        )
    );

-- Transcriptions policies (through meetings)
CREATE POLICY "Users can view own transcriptions"
    ON public.transcriptions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings
            WHERE meetings.id = transcriptions.meeting_id
            AND meetings.user_id = auth.uid()
        )
    );

-- Transcription Segments policies (through transcriptions)
CREATE POLICY "Users can view own segments"
    ON public.transcription_segments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.transcriptions t
            JOIN public.meetings m ON m.id = t.meeting_id
            WHERE t.id = transcription_segments.transcription_id
            AND m.user_id = auth.uid()
        )
    );

-- Processing Jobs policies (through meetings)
CREATE POLICY "Users can view own jobs"
    ON public.processing_jobs FOR SELECT
    USING (
        meeting_id IS NULL OR
        EXISTS (
            SELECT 1 FROM public.meetings
            WHERE meetings.id = processing_jobs.meeting_id
            AND meetings.user_id = auth.uid()
        )
    );

-- -------------------------------------------
-- Service Role Bypass (for backend services)
-- -------------------------------------------
-- Note: Service role automatically bypasses RLS
-- This is used by the backend API and workers

-- -------------------------------------------
-- Updated At Trigger
-- -------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_calendars_updated_at
    BEFORE UPDATE ON public.connected_calendars
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON public.calendar_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_meetings_updated_at
    BEFORE UPDATE ON public.meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_recordings_updated_at
    BEFORE UPDATE ON public.recordings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_transcriptions_updated_at
    BEFORE UPDATE ON public.transcriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON public.processing_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- -------------------------------------------
-- Helper Functions
-- -------------------------------------------

-- Get upcoming meetings for a user
CREATE OR REPLACE FUNCTION get_upcoming_meetings(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    meeting_url TEXT,
    scheduled_start TIMESTAMPTZ,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.title,
        m.meeting_url,
        m.scheduled_start,
        m.status
    FROM public.meetings m
    WHERE m.user_id = p_user_id
    AND m.scheduled_start > NOW()
    AND m.status IN ('scheduled', 'joining', 'waiting')
    ORDER BY m.scheduled_start ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Search transcriptions
CREATE OR REPLACE FUNCTION search_transcriptions(
    p_user_id UUID,
    p_query TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    meeting_id UUID,
    meeting_title TEXT,
    segment_id UUID,
    segment_text TEXT,
    start_time_ms INTEGER,
    relevance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id AS meeting_id,
        m.title AS meeting_title,
        ts.id AS segment_id,
        ts.text AS segment_text,
        ts.start_time_ms,
        ts_rank(to_tsvector('portuguese', ts.text), plainto_tsquery('portuguese', p_query)) AS relevance
    FROM public.transcription_segments ts
    JOIN public.transcriptions t ON t.id = ts.transcription_id
    JOIN public.meetings m ON m.id = t.meeting_id
    WHERE m.user_id = p_user_id
    AND to_tsvector('portuguese', ts.text) @@ plainto_tsquery('portuguese', p_query)
    ORDER BY relevance DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
