-- Cyron database schema (PostgreSQL)
-- Mirrors backend/app/models/*.py. Applied automatically by docker-compose
-- on first boot of the db service; run by hand with:
--   psql "$DATABASE_URL" -f db/schema.sql

CREATE TYPE target_type AS ENUM ('domain', 'ip', 'cidr');
CREATE TYPE scan_mode AS ENUM ('active', 'passive');
CREATE TYPE scan_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE severity_level AS ENUM ('info', 'low', 'medium', 'high');
CREATE TYPE report_format AS ENUM ('markdown', 'json');

CREATE TABLE targets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    value       TEXT NOT NULL,
    type        target_type NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (value)
);

CREATE TABLE scan_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id       UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    modes           scan_mode[] NOT NULL,
    status          scan_status NOT NULL DEFAULT 'pending',
    authorized      BOOLEAN NOT NULL DEFAULT false,
    requested_by    TEXT,
    exposure_score  SMALLINT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT authorized_required CHECK (authorized IS TRUE)
);

CREATE INDEX idx_scan_runs_target ON scan_runs(target_id);
CREATE INDEX idx_scan_runs_status ON scan_runs(status);

CREATE TABLE phase_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_run_id     UUID NOT NULL REFERENCES scan_runs(id) ON DELETE CASCADE,
    phase_id        TEXT NOT NULL,       -- slug, matches recon/registry.py PHASES[].id
    phase_name      TEXT NOT NULL,
    mode            scan_mode NOT NULL,
    tools_used      TEXT[] NOT NULL DEFAULT '{}',
    status          scan_status NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    UNIQUE (scan_run_id, phase_id)
);

CREATE INDEX idx_phase_results_scan ON phase_results(scan_run_id);

CREATE TABLE findings (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_result_id   UUID NOT NULL REFERENCES phase_results(id) ON DELETE CASCADE,
    ref               TEXT NOT NULL,      -- e.g. CYR-001, unique within a scan_run
    tool              TEXT NOT NULL,
    title             TEXT NOT NULL,
    description       TEXT NOT NULL,
    severity          severity_level NOT NULL DEFAULT 'info',
    recommendation    TEXT,
    raw_output        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_findings_phase_result ON findings(phase_result_id);
CREATE INDEX idx_findings_severity ON findings(severity);

CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_run_id     UUID NOT NULL REFERENCES scan_runs(id) ON DELETE CASCADE,
    format          report_format NOT NULL DEFAULT 'markdown',
    content         TEXT NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reports_scan ON reports(scan_run_id);
