-- Hybrid retrieval schema (004): FTS5 indexes and sqlite-vec chunk vectors.

CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    entity_id UNINDEXED,
    campaign_id UNINDEXED,
    name,
    aliases_text,
    summary
);

CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
    claim_id UNINDEXED,
    campaign_id UNINDEXED,
    claim_text,
    predicate
);

CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5(
    source_id UNINDEXED,
    campaign_id UNINDEXED,
    title,
    body
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(
    chunk_id TEXT PRIMARY KEY,
    campaign_id TEXT,
    embedding FLOAT[768]
);

CREATE TRIGGER IF NOT EXISTS entities_fts_ai AFTER INSERT ON entity BEGIN
    INSERT INTO entities_fts(entity_id, campaign_id, name, aliases_text, summary)
    VALUES (
        NEW.id,
        NEW.campaign_id,
        NEW.name,
        COALESCE((SELECT group_concat(value, ' ') FROM json_each(NEW.aliases_json)), ''),
        NEW.summary
    );
END;

CREATE TRIGGER IF NOT EXISTS entities_fts_ad AFTER DELETE ON entity BEGIN
    DELETE FROM entities_fts WHERE entity_id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS entities_fts_au AFTER UPDATE ON entity BEGIN
    DELETE FROM entities_fts WHERE entity_id = OLD.id;
    INSERT INTO entities_fts(entity_id, campaign_id, name, aliases_text, summary)
    VALUES (
        NEW.id,
        NEW.campaign_id,
        NEW.name,
        COALESCE((SELECT group_concat(value, ' ') FROM json_each(NEW.aliases_json)), ''),
        NEW.summary
    );
END;

CREATE TRIGGER IF NOT EXISTS claims_fts_ai AFTER INSERT ON claim BEGIN
    INSERT INTO claims_fts(claim_id, campaign_id, claim_text, predicate)
    VALUES (NEW.id, NEW.campaign_id, NEW.claim_text, NEW.predicate);
END;

CREATE TRIGGER IF NOT EXISTS claims_fts_ad AFTER DELETE ON claim BEGIN
    DELETE FROM claims_fts WHERE claim_id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS claims_fts_au AFTER UPDATE ON claim BEGIN
    DELETE FROM claims_fts WHERE claim_id = OLD.id;
    INSERT INTO claims_fts(claim_id, campaign_id, claim_text, predicate)
    VALUES (NEW.id, NEW.campaign_id, NEW.claim_text, NEW.predicate);
END;

CREATE TRIGGER IF NOT EXISTS sources_fts_ai AFTER INSERT ON source BEGIN
    INSERT INTO sources_fts(source_id, campaign_id, title, body)
    VALUES (NEW.id, NEW.campaign_id, NEW.title, NEW.body);
END;

CREATE TRIGGER IF NOT EXISTS sources_fts_ad AFTER DELETE ON source BEGIN
    DELETE FROM sources_fts WHERE source_id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS sources_fts_au AFTER UPDATE ON source BEGIN
    DELETE FROM sources_fts WHERE source_id = OLD.id;
    INSERT INTO sources_fts(source_id, campaign_id, title, body)
    VALUES (NEW.id, NEW.campaign_id, NEW.title, NEW.body);
END;

CREATE TRIGGER IF NOT EXISTS chunk_vectors_ai AFTER INSERT ON chunk_embedding BEGIN
    INSERT INTO chunk_vectors(chunk_id, campaign_id, embedding)
    VALUES (NEW.chunk_id, NEW.campaign_id, NEW.embedding);
END;

CREATE TRIGGER IF NOT EXISTS chunk_vectors_ad AFTER DELETE ON chunk_embedding BEGIN
    DELETE FROM chunk_vectors WHERE chunk_id = OLD.chunk_id;
END;

CREATE TRIGGER IF NOT EXISTS chunk_vectors_au AFTER UPDATE ON chunk_embedding BEGIN
    DELETE FROM chunk_vectors WHERE chunk_id = OLD.chunk_id;
    INSERT INTO chunk_vectors(chunk_id, campaign_id, embedding)
    VALUES (NEW.chunk_id, NEW.campaign_id, NEW.embedding);
END;

INSERT INTO entities_fts(entity_id, campaign_id, name, aliases_text, summary)
SELECT
    e.id,
    e.campaign_id,
    e.name,
    COALESCE((SELECT group_concat(value, ' ') FROM json_each(e.aliases_json)), ''),
    e.summary
FROM entity e
WHERE NOT EXISTS (
    SELECT 1 FROM entities_fts existing WHERE existing.entity_id = e.id
);

INSERT INTO claims_fts(claim_id, campaign_id, claim_text, predicate)
SELECT c.id, c.campaign_id, c.claim_text, c.predicate
FROM claim c
WHERE NOT EXISTS (
    SELECT 1 FROM claims_fts existing WHERE existing.claim_id = c.id
);

INSERT INTO sources_fts(source_id, campaign_id, title, body)
SELECT s.id, s.campaign_id, s.title, s.body
FROM source s
WHERE NOT EXISTS (
    SELECT 1 FROM sources_fts existing WHERE existing.source_id = s.id
);

INSERT INTO chunk_vectors(chunk_id, campaign_id, embedding)
SELECT ce.chunk_id, ce.campaign_id, ce.embedding
FROM chunk_embedding ce
WHERE NOT EXISTS (
    SELECT 1 FROM chunk_vectors existing WHERE existing.chunk_id = ce.chunk_id
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (4, 'Hybrid search indexes');
