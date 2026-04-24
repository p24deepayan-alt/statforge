-- StatForge SQLite schema v1
-- WAL mode is enabled programmatically in store.py

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,          -- UUIDv4
    name          TEXT NOT NULL,
    created_at    TEXT NOT NULL,             -- ISO-8601
    modified_at   TEXT NOT NULL,             -- ISO-8601
    source_filename TEXT,
    row_count     INTEGER,
    col_count     INTEGER,
    app_version   TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    id            TEXT PRIMARY KEY,          -- UUIDv4
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    kind          TEXT NOT NULL,             -- 'column_summary' | 'plot' | 'model' | 'comparison'
    name          TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    spec_json     TEXT NOT NULL,             -- parameters needed to regenerate
    metrics_json  TEXT,                      -- quick-access metrics for UIs
    blob_path     TEXT,                      -- relative path inside session dir
    in_report     INTEGER NOT NULL DEFAULT 0 -- 0 = excluded, 1 = included
);

CREATE TABLE IF NOT EXISTS preprocess_steps (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    step_index    INTEGER NOT NULL,
    op            TEXT NOT NULL,             -- 'impute' | 'standardize' | 'transform' | ...
    params_json   TEXT NOT NULL,
    description   TEXT NOT NULL,             -- human-readable for report
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id              TEXT PRIMARY KEY,        -- UUIDv4
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    layout_json     TEXT NOT NULL,           -- ordered list of artifact IDs + narrative blocks
    last_exported_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);
CREATE INDEX IF NOT EXISTS idx_preprocess_session ON preprocess_steps(session_id);
CREATE INDEX IF NOT EXISTS idx_reports_session ON reports(session_id);
