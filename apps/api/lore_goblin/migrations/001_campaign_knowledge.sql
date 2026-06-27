-- Campaign knowledge schema (002): sources, entities, claims, and related tables.

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE TABLE IF NOT EXISTS entity (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL DEFAULT '',
    legacy_pc_id TEXT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    author_user_id TEXT NOT NULL REFERENCES users(id),
    session_id TEXT NULL REFERENCES sessions(id) ON DELETE SET NULL,
    entity_id TEXT NULL REFERENCES entity(id) ON DELETE SET NULL,
    legacy_note_id TEXT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claim (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    subject_entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
    predicate TEXT NOT NULL,
    object_entity_id TEXT NULL REFERENCES entity(id) ON DELETE SET NULL,
    canon_status TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entity_mention (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
    mention_text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS relationship (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    source_entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
    target_entity_id TEXT NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    source_id TEXT NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entity_importance (
    entity_id TEXT PRIMARY KEY REFERENCES entity(id) ON DELETE CASCADE,
    mention_count INTEGER NOT NULL DEFAULT 0,
    session_count INTEGER NOT NULL DEFAULT 0,
    relationship_count INTEGER NOT NULL DEFAULT 0,
    unresolved_claim_count INTEGER NOT NULL DEFAULT 0,
    last_seen_session_id TEXT NULL REFERENCES sessions(id) ON DELETE SET NULL,
    importance_score REAL NOT NULL DEFAULT 0.0,
    manually_pinned INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_campaign_id ON source(campaign_id);
CREATE INDEX IF NOT EXISTS idx_source_source_type ON source(source_type);
CREATE INDEX IF NOT EXISTS idx_source_session_id ON source(session_id);
CREATE INDEX IF NOT EXISTS idx_source_legacy_note_id ON source(legacy_note_id);

CREATE INDEX IF NOT EXISTS idx_entity_campaign_id ON entity(campaign_id);
CREATE INDEX IF NOT EXISTS idx_entity_entity_type ON entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_campaign_name ON entity(campaign_id, name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_entity_legacy_pc_id ON entity(legacy_pc_id);

CREATE INDEX IF NOT EXISTS idx_claim_campaign_id ON claim(campaign_id);
CREATE INDEX IF NOT EXISTS idx_claim_subject_entity_id ON claim(subject_entity_id);
CREATE INDEX IF NOT EXISTS idx_claim_object_entity_id ON claim(object_entity_id);
CREATE INDEX IF NOT EXISTS idx_claim_source_id ON claim(source_id);

CREATE INDEX IF NOT EXISTS idx_entity_mention_source_id ON entity_mention(source_id);
CREATE INDEX IF NOT EXISTS idx_entity_mention_entity_id ON entity_mention(entity_id);

CREATE INDEX IF NOT EXISTS idx_relationship_campaign_id ON relationship(campaign_id);
CREATE INDEX IF NOT EXISTS idx_relationship_source_entity_id ON relationship(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_target_entity_id ON relationship(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_source_id ON relationship(source_id);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Campaign knowledge schema');
