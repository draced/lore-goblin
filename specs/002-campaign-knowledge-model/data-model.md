# Data Model: Campaign Knowledge Model

## Overview

Campaign knowledge follows: **Source → Entities → Claims → Relationships → Search Index**.

This spec (002) introduces the foundational tables and migrations. Claims, mentions, relationships, and importance scoring are created here but populated in spec 003.

## Entity Relationship Diagram

```text
campaign
  ├── source (1:N)
  │     ├── entity_mention (1:N)
  │     └── claim (1:N)
  ├── entity (1:N)
  │     ├── claim as subject (1:N)
  │     ├── claim as object (1:N)
  │     ├── relationship as source (1:N)
  │     ├── relationship as target (1:N)
  │     └── entity_importance (1:1)
  └── content_chunks (1:N, via source_id)
```

## Tables

### schema_version

Tracks applied migrations.

| Column | Type | Notes |
|--------|------|-------|
| version | INTEGER | PRIMARY KEY |
| applied_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |
| description | TEXT | Migration summary |

### source

Unified evidence records. Every fact traces back here.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | PRIMARY KEY |
| campaign_id | TEXT | NOT NULL, FK → campaigns(id) ON DELETE CASCADE |
| source_type | TEXT | NOT NULL, see enum below |
| title | TEXT | NOT NULL |
| body | TEXT | NOT NULL |
| author_user_id | TEXT | NOT NULL, FK → users(id) |
| session_id | TEXT | NULL, FK → sessions(id) ON DELETE SET NULL |
| entity_id | TEXT | NULL, FK → entity(id) ON DELETE SET NULL; set for PLAYER_CHARACTER_DESC |
| legacy_note_id | TEXT | NULL, unique when set; maps migrated session_notes.id |
| created_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

**source_type enum**: `SESSION_NOTE`, `PLAYER_CHARACTER_DESC`, `ITEM_DESC`, `NPC_DESC`, `LOCATION_DESC`, `MANUAL_EDIT`

**Indexes**: `(campaign_id)`, `(source_type)`, `(session_id)`, `(legacy_note_id)`

### entity

Canonical campaign objects.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | PRIMARY KEY |
| campaign_id | TEXT | NOT NULL, FK → campaigns(id) ON DELETE CASCADE |
| entity_type | TEXT | NOT NULL, see enum below |
| name | TEXT | NOT NULL |
| aliases_json | TEXT | NOT NULL DEFAULT '[]' |
| summary | TEXT | NOT NULL DEFAULT '' |
| legacy_pc_id | TEXT | NULL, unique when set; maps migrated player_characters.id |
| created_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

**entity_type enum**: `PC`, `NPC`, `LOCATION`, `FACTION`, `ITEM`, `QUEST`, `EVENT`, `DEITY`, `MONSTER`, `ORGANIZATION`, `RUMOR`

**Indexes**: `(campaign_id)`, `(entity_type)`, `(campaign_id, name COLLATE NOCASE)`, `(legacy_pc_id)`

### claim

Atomic knowledge statements (schema in 002; populated in 003).

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | PRIMARY KEY |
| campaign_id | TEXT | NOT NULL, FK → campaigns(id) ON DELETE CASCADE |
| claim_text | TEXT | NOT NULL |
| subject_entity_id | TEXT | NOT NULL, FK → entity(id) ON DELETE CASCADE |
| predicate | TEXT | NOT NULL |
| object_entity_id | TEXT | NULL, FK → entity(id) ON DELETE SET NULL |
| canon_status | TEXT | NOT NULL, see enum below |
| source_id | TEXT | NOT NULL, FK → source(id) ON DELETE CASCADE |
| confidence | REAL | NOT NULL DEFAULT 1.0 |
| created_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

**canon_status enum**: `CONFIRMED`, `RUMOR`, `THEORY`, `DISPUTED`

**Indexes**: `(campaign_id)`, `(subject_entity_id)`, `(object_entity_id)`, `(source_id)`

### entity_mention

Links raw text spans to canonical entities.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | PRIMARY KEY |
| source_id | TEXT | NOT NULL, FK → source(id) ON DELETE CASCADE |
| entity_id | TEXT | NOT NULL, FK → entity(id) ON DELETE CASCADE |
| mention_text | TEXT | NOT NULL |
| start_offset | INTEGER | NOT NULL |
| end_offset | INTEGER | NOT NULL |

**Indexes**: `(source_id)`, `(entity_id)`

### relationship

Durable typed edges between entities.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | PRIMARY KEY |
| campaign_id | TEXT | NOT NULL, FK → campaigns(id) ON DELETE CASCADE |
| source_entity_id | TEXT | NOT NULL, FK → entity(id) ON DELETE CASCADE |
| target_entity_id | TEXT | NOT NULL, FK → entity(id) ON DELETE CASCADE |
| relationship_type | TEXT | NOT NULL |
| description | TEXT | NOT NULL DEFAULT '' |
| source_id | TEXT | NOT NULL, FK → source(id) ON DELETE CASCADE |
| created_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

**Indexes**: `(campaign_id)`, `(source_entity_id)`, `(target_entity_id)`, `(source_id)`

### entity_importance

Denormalized importance scores (populated in 003).

| Column | Type | Notes |
|--------|------|-------|
| entity_id | TEXT | PRIMARY KEY, FK → entity(id) ON DELETE CASCADE |
| mention_count | INTEGER | NOT NULL DEFAULT 0 |
| session_count | INTEGER | NOT NULL DEFAULT 0 |
| relationship_count | INTEGER | NOT NULL DEFAULT 0 |
| unresolved_claim_count | INTEGER | NOT NULL DEFAULT 0 |
| last_seen_session_id | TEXT | NULL, FK → sessions(id) ON DELETE SET NULL |
| importance_score | REAL | NOT NULL DEFAULT 0.0 |
| manually_pinned | INTEGER | NOT NULL DEFAULT 0 |
| updated_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

### content_chunks (altered)

Add column:

| Column | Type | Notes |
|--------|------|-------|
| source_id | TEXT | NULL → NOT NULL after migration, FK → source(id) ON DELETE CASCADE |

## Claims vs Relationships

- **claim**: Evidence-backed statement extracted from a specific source. May be `RUMOR` or `THEORY`. Multiple conflicting claims may coexist.
- **relationship**: Durable campaign graph edge, typically derived from `CONFIRMED` claims. Used for traversal and importance scoring.

## Migration Mapping

| Legacy table | New records |
|--------------|-------------|
| `session_notes` | `source` (`SESSION_NOTE`, `body`=raw_content, `legacy_note_id`=id) |
| `player_characters` | `entity` (`PC`, `summary`=notes) + `source` (`PLAYER_CHARACTER_DESC`, `body`=notes) |
| `content_chunks` | `source_id` set from parent note's migrated source |

## Validation Rules

- `source.body` and `entity.name` MUST NOT be blank on create.
- `entity.aliases_json` MUST be valid JSON array of strings.
- `entity_mention.end_offset` MUST be greater than `start_offset`.
- `claim.object_entity_id` MAY be null for unary predicates (e.g. `died`, `exists_at`).

## State Transitions

Not applicable in 002. Canon status transitions deferred to spec 005 review workflow.
