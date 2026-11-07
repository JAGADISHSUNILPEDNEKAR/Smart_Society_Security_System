-- Smart Society Security System SQLite Database Schema
-- Enforces referential integrity, foreign key cascading, and audit logging.

PRAGMA foreign_keys = ON;

-- 1. Residents Table
CREATE TABLE IF NOT EXISTS residents (
    resident_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    apartment_number TEXT NOT NULL,
    contact_number TEXT,
    registration_date TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    consent_given INTEGER NOT NULL DEFAULT 1 CHECK (consent_given IN (0, 1)),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_residents_apartment ON residents(apartment_number);
CREATE INDEX IF NOT EXISTS idx_residents_active ON residents(is_active);

-- 2. Face Embeddings Table (Biometric Templates)
-- Stored as binary float32 blobs (128 dimensions * 4 bytes = 512 bytes per template)
CREATE TABLE IF NOT EXISTS face_embeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id TEXT NOT NULL,
    embedding_blob BLOB NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'sface_2021dec',
    sample_tag TEXT DEFAULT 'frontal',
    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (resident_id) REFERENCES residents(resident_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embeddings_resident ON face_embeddings(resident_id);

-- 3. Access Control Audit Logs
CREATE TABLE IF NOT EXISTS access_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id TEXT,
    detected_name TEXT NOT NULL,
    apartment_number TEXT,
    similarity_score REAL,
    decision TEXT NOT NULL CHECK (decision IN ('ENTRY ALLOWED', 'ENTRY REJECTED', 'VERIFICATION REQUIRED')),
    verification_status TEXT NOT NULL DEFAULT 'AUTOMATIC' CHECK (
        verification_status IN ('AUTOMATIC', 'MANUALLY_APPROVED', 'MANUALLY_REJECTED', 'PENDING_REVIEW')
    ),
    timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    reason TEXT,
    FOREIGN KEY (resident_id) REFERENCES residents(resident_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON access_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_decision ON access_logs(decision);

-- 4. System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Initial System Settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, description) VALUES
    ('recognition_threshold_high', '0.363', 'SFace cosine similarity threshold for automatic ALLOWED decision'),
    ('recognition_threshold_low', '0.280', 'Cosine similarity threshold below which faces are strictly REJECTED'),
    ('cooldown_seconds', '8.0', 'Deduplication window in seconds to prevent duplicate log spam for the same resident'),
    ('society_name', 'Greenfield Heights Residential Society', 'Display name of residential society'),
    ('manual_override_enabled', 'true', 'Enable on-duty security guard manual decision override');
