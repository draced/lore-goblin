# Implementation Plan: Campaign Knowledge Model

**Branch**: `002-campaign-knowledge-model` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-campaign-knowledge-model/spec.md`

## Summary

Introduce the foundational campaign-aware SQLite schema (`source`, `entity`, `claim`, `entity_mention`, `relationship`, `entity_importance`), a versioned migration runner, and APIs that unify session notes and player characters under traceable sources. Migrate existing MVP1/002 data without UX regression. Claims and search indexes are schema-only; population deferred to specs 003–004.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript (web unchanged for this feature)

**Primary Dependencies**: FastAPI, sqlite3 (stdlib), Pydantic

**Storage**: SQLite with versioned migrations (`schema_version` + numbered SQL scripts)

**Testing**: pytest for API contract and migration integration tests

**Target Platform**: Local Docker Compose (Linux containers)

**Performance Goals**: Migration completes in under 60s for 1000 notes; API ingest unchanged latency

**Constraints**: Backward-compatible PC roster API responses; no extraction or hybrid search in this spec

**Scale/Scope**: Typical campaign: 20 PCs, 50 sessions, 200 notes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gates

- [x] **Local-First (I)**: SQLite + local stack only
- [x] **Source-Grounded (II)**: Sources become first-class evidence records
- [x] **Provenance (III)**: Author and session preserved on every source
- [x] **Discord-First (IV)**: PC and session flows unchanged on Discord
- [x] **Campaign Tone (V)**: No answer-generation changes in 002
- [x] **Simplicity (VI)**: Migration runner justified in Complexity Tracking
- [x] **Test-First (VII)**: Migration and API tests before implementation
- [x] **Campaign-Aware Knowledge (VIII)**: Schema establishes source/entity/claim model
- [x] **Spec Format**: Full spec template with P1–P4 stories

### Post-Design Re-Check

All gates pass. Migration layer is the only justified complexity addition.

## Project Structure

### Documentation (this feature)

```text
specs/002-campaign-knowledge-model/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code

```text
apps/api/lore_goblin/
├── schema.sql                    # baseline (retained for fresh installs)
├── migrations/
│   ├── 001_campaign_knowledge.sql
│   └── 002_migrate_legacy_data.sql
├── db.py                         # migration runner
├── repository.py                 # source/entity CRUD; refactored session/PC writes
├── main.py                       # new endpoints
└── models.py                     # Pydantic enums (new)

apps/api/tests/
├── test_migrations.py
├── test_sources.py
├── test_entities.py
└── test_player_characters_compat.py

apps/web/                         # minimal: no UI change for sources/entities in 002
apps/discord-bot/                 # no change (uses existing PC endpoints)
```

**Structure Decision**: Three-app layout preserved. All schema work in `apps/api`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Versioned migration runner | Foundational tables replace append-only `CREATE IF NOT EXISTS` | In-place `ALTER` without versioning risks partial upgrades and duplicate data |
| Dual-write PC (entity+legacy) during transition | Backward-compatible API while migrating | Breaking API would regress Discord/web roster flows |
| Empty claim/relationship tables in 002 | Specs 003–004 depend on stable schema | Adding tables later requires another migration mid-pipeline |

## Data Flow

### Session note ingest (updated)

1. User submits note (web/Discord) → existing session resolution
2. Insert `source` (`SESSION_NOTE`) with body, author, session_id
3. Insert `session_notes` (legacy, transitional) OR deprecate writes after migration period
4. Chunk text → `content_chunks` with `source_id` FK
5. Return session response (unchanged shape)

### PC roster add (updated)

1. User submits name + notes
2. Create `entity` (`PC`, name, summary=notes)
3. Create `source` (`PLAYER_CHARACTER_DESC`, body=notes, linked to entity via metadata or join)
4. Return backward-compatible `{id, campaign_id, name, notes, ...}` mapping from entity+source

## Phase 0 / Phase 1 Artifacts

See [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md), [quickstart.md](./quickstart.md).
