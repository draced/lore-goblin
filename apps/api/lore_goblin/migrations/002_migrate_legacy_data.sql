-- Backfill unified sources and entities from legacy MVP1 tables.

INSERT OR IGNORE INTO source (
    id,
    campaign_id,
    source_type,
    title,
    body,
    author_user_id,
    session_id,
    legacy_note_id
)
SELECT
    'src_' || sn.id,
    sn.campaign_id,
    'SESSION_NOTE',
    COALESCE(NULLIF(TRIM(s.label), ''), s.session_date),
    sn.raw_content,
    sn.author_user_id,
    sn.session_id,
    sn.id
FROM session_notes sn
JOIN sessions s ON s.id = sn.session_id
WHERE NOT EXISTS (
    SELECT 1 FROM source existing WHERE existing.legacy_note_id = sn.id
);

INSERT OR IGNORE INTO entity (
    id,
    campaign_id,
    entity_type,
    name,
    aliases_json,
    summary,
    legacy_pc_id
)
SELECT
    pc.id,
    pc.campaign_id,
    'PC',
    pc.name,
    '[]',
    pc.notes,
    pc.id
FROM player_characters pc
WHERE NOT EXISTS (
    SELECT 1 FROM entity existing WHERE existing.legacy_pc_id = pc.id
);

INSERT OR IGNORE INTO source (
    id,
    campaign_id,
    source_type,
    title,
    body,
    author_user_id,
    entity_id,
    legacy_note_id
)
SELECT
    'src_pc_' || pc.id,
    pc.campaign_id,
    'PLAYER_CHARACTER_DESC',
    pc.name,
    pc.notes,
    (
        SELECT cm.user_id
        FROM campaign_members cm
        WHERE cm.campaign_id = pc.campaign_id
          AND cm.role = 'owner'
        LIMIT 1
    ),
    pc.id,
    NULL
FROM player_characters pc
WHERE NOT EXISTS (
    SELECT 1 FROM source existing
    WHERE existing.entity_id = pc.id
      AND existing.source_type = 'PLAYER_CHARACTER_DESC'
);

UPDATE content_chunks
SET source_id = (
    SELECT src.id
    FROM source src
    WHERE src.legacy_note_id = content_chunks.source_id
)
WHERE content_chunks.source_type = 'session_note'
  AND EXISTS (
      SELECT 1
      FROM source src
      WHERE src.legacy_note_id = content_chunks.source_id
  );

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (2, 'Migrate legacy session notes and player characters');
