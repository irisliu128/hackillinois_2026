-- =============================================================================
-- FloodGuard: monitoring_sessions schema
-- Run this in your Supabase SQL Editor (or migrations tool).
-- =============================================================================

-- 1. monitoring_sessions
--    Tracks the adaptive polling state for every monitored coordinate.
--    One row per unique (lat, lon) pair — never duplicated; always upserted.
-- =============================================================================

CREATE TABLE IF NOT EXISTS monitoring_sessions (
    id                        UUID         DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Coordinate key (unique constraint enables ON CONFLICT upsert)
    lat                       DOUBLE PRECISION NOT NULL,
    lon                       DOUBLE PRECISION NOT NULL,

    -- Timing
    last_check                TIMESTAMPTZ  NOT NULL DEFAULT now(),
    next_check_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- Current poll frequency in minutes (60 = ALERT, 1440 = NORMAL)
    current_frequency_minutes INTEGER      NOT NULL DEFAULT 1440,

    -- Risk state: 'NORMAL' or 'CRITICAL'
    risk_level                TEXT         NOT NULL DEFAULT 'NORMAL'
                                           CHECK (risk_level IN ('NORMAL', 'CRITICAL')),

    -- Latest model outputs (stored for audit / dashboards)
    final_prob                DOUBLE PRECISION,
    rainfall_mm               DOUBLE PRECISION,

    -- Cool-down counter: consecutive NORMAL readings since last CRITICAL event
    -- When this reaches COOLDOWN_CYCLES (3), frequency can downgrade to 24h
    consecutive_normal_count  INTEGER      NOT NULL DEFAULT 0,

    -- Audit timestamps
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- Enforce single row per coordinate
    CONSTRAINT uq_monitoring_lat_lon UNIQUE (lat, lon)
);

-- Spatial index for bounding-box queries (e.g., "find all critical zones nearby")
CREATE INDEX IF NOT EXISTS idx_monitoring_latlon
    ON monitoring_sessions (lat, lon);

-- Index for background loop: quickly fetch all sessions due for a check
CREATE INDEX IF NOT EXISTS idx_monitoring_next_check
    ON monitoring_sessions (next_check_at);

-- Index for dashboard queries (filter by risk level)
CREATE INDEX IF NOT EXISTS idx_monitoring_risk_level
    ON monitoring_sessions (risk_level);

-- Auto-update updated_at on every row change
CREATE OR REPLACE FUNCTION update_monitoring_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_monitoring_updated_at ON monitoring_sessions;
CREATE TRIGGER trg_monitoring_updated_at
    BEFORE UPDATE ON monitoring_sessions
    FOR EACH ROW EXECUTE FUNCTION update_monitoring_updated_at();


-- =============================================================================
-- 2. ALTER user_settings — add the Auto-Scale toggle
--    Person 3's /v1/settings endpoint should expose this column.
--    (Safe to run even if user_settings already exists)
-- =============================================================================

ALTER TABLE user_settings
    ADD COLUMN IF NOT EXISTS auto_scale BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN user_settings.auto_scale IS
    'When TRUE, the AdaptiveScaler emergency logic overrides any manual polling_interval_minutes.';


-- =============================================================================
-- Example seed row (useful for local dev / smoke tests)
-- =============================================================================
-- INSERT INTO monitoring_sessions (lat, lon, risk_level, current_frequency_minutes)
-- VALUES (40.1164, -88.2434, 'NORMAL', 1440)
-- ON CONFLICT (lat, lon) DO NOTHING;
