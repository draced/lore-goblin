# Data Model: Knowledge Extraction Pipeline

Extends [002 data-model](../002-campaign-knowledge-model/data-model.md).

## extraction_job

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | PRIMARY KEY |
| source_id | TEXT | NOT NULL, FK → source(id) ON DELETE CASCADE |
| campaign_id | TEXT | NOT NULL, FK → campaigns(id) ON DELETE CASCADE |
| status | TEXT | `pending`, `running`, `complete`, `failed` |
| error_message | TEXT | NULL |
| attempt_count | INTEGER | NOT NULL DEFAULT 0 |
| created_at | TEXT | NOT NULL |
| updated_at | TEXT | NOT NULL |

**Indexes**: `(source_id)`, `(status)`, `(campaign_id)`

## chunk_embedding

Stores vectors for sqlite-vec (004). Created in 003.

| Column | Type | Notes |
|--------|------|-------|
| chunk_id | TEXT | PRIMARY KEY, FK → content_chunks(id) |
| campaign_id | TEXT | NOT NULL |
| embedding | BLOB | NOT NULL |
| model_name | TEXT | NOT NULL |
| created_at | TEXT | NOT NULL |

## source.entity_id (optional FK addition)

For `PLAYER_CHARACTER_DESC` and entity-linked sources, optional `entity_id` FK on `source` table (may be added in 002 migration 003 or here).

## Ollama Response Schemas (logical)

### ExtractedEntity

- name, type, aliases[], short_description, importance (major|minor|incidental), evidence_quote

### ResolutionResult

- extracted_name, matched_entity_id (nullable), confidence, reason

### ExtractedClaim

- claim_text, subject_entity_name, predicate, object_entity_name, canon_status, importance, source_quote

## Importance Formula

```
importance_score =
  mention_count
  + session_count
  + relationship_count
  + unresolved_claim_count
  + (manually_pinned ? 10 : 0)
  + (recent_session_bonus: 5 if last_seen within 2 sessions else 0)
```

Recomputed after each successful extraction job per affected entities.
