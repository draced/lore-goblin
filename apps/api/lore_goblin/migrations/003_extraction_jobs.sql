-- Extraction pipeline schema (003): jobs and chunk embeddings.

CREATE TABLE IF NOT EXISTS extraction_job (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'complete', 'failed')),
    error_message TEXT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunk_embedding (
    chunk_id TEXT PRIMARY KEY REFERENCES content_chunks(id) ON DELETE CASCADE,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    embedding BLOB NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_extraction_job_source_id ON extraction_job(source_id);
CREATE INDEX IF NOT EXISTS idx_extraction_job_status ON extraction_job(status);
CREATE INDEX IF NOT EXISTS idx_extraction_job_campaign_id ON extraction_job(campaign_id);
CREATE INDEX IF NOT EXISTS idx_chunk_embedding_campaign_id ON chunk_embedding(campaign_id);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (3, 'Extraction jobs and chunk embeddings');
