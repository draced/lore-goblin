# Data Model: Hybrid Retrieval

## FTS5 Virtual Tables

### entities_fts

- Indexed: `name`, `aliases_json` (expanded), `summary`
- Content table: `entity`
- Triggers: insert/update/delete sync

### claims_fts

- Indexed: `claim_text`, `predicate`
- Content table: `claim`

### sources_fts

- Indexed: `title`, `body` (title weighted higher in query)
- Content table: `source`

## sqlite-vec

### chunk_vectors

```sql
CREATE VIRTUAL TABLE chunk_vectors USING vec0(
  chunk_id TEXT PRIMARY KEY,
  embedding FLOAT[768]
);
```

Populated from `chunk_embedding` table (003) via sync trigger or index rebuild job.

## Retrieved Context Record (runtime, not persisted)

| Field | Source |
|-------|--------|
| type | `claim`, `entity`, `chunk`, `source` |
| id | row id |
| text | display text for prompt |
| score | merged rank |
| citation_label | source title |
| citation_quote | claim_text or chunk excerpt |

## Citation Shape (API response)

```json
{
  "label": "Session 8 — Chapel",
  "source_type": "SESSION_NOTE",
  "claim_quote": "The party found the silver key in the ruined chapel."
}
```

Replaces session-date-only citations from MVP1.
