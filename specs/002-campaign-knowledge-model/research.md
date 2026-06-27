# Research: Campaign Knowledge Model

## Decision: Versioned SQL migrations

**Decision**: Add `schema_version` table and `apps/api/lore_goblin/migrations/*.sql` applied at startup via `db.py`.

**Rationale**: Constitution v1.1.0 requires versioned migrations for foundational changes. `CREATE IF NOT EXISTS` cannot safely add FK columns or backfill data.

**Alternatives considered**:
- Alembic: rejected for YAGNI; single-file numbered SQL sufficient for SQLite
- One-shot migration script: rejected; no re-run safety

## Decision: Transitional dual-write for session_notes and player_characters

**Decision**: During 002, write to both legacy tables and new model; migration backfills existing rows; reads for PC roster come from entity+source with legacy fallback.

**Rationale**: Zero-downtime upgrade for existing deployments with completed 002-player-characters code.

**Alternatives considered**:
- Big-bang cutover: rejected; risks data loss on failed migration
- Keep legacy tables forever: rejected; technical debt blocks spec 003

## Decision: legacy_*_id columns on source and entity

**Decision**: `source.legacy_note_id` and `entity.legacy_pc_id` for idempotent migration mapping.

**Rationale**: Enables `INSERT OR IGNORE` / upsert by legacy id on re-run.

**Alternatives considered**:
- Separate mapping table: rejected; extra join for no benefit at this scale

## Decision: author_user_id on source (not free-text author)

**Decision**: FK to `users.id` matching existing `session_notes.author_user_id` pattern.

**Rationale**: Consistent provenance with MVP1; supports future Discord user linkage.

**Alternatives considered**:
- Plain-text author field from user spec: adapted to user_id FK for referential integrity

## Decision: No new web UI for sources/entities in 002

**Decision**: API-only for source/entity list/create; web UI changes limited to ensuring roster still works.

**Rationale**: P4 preserves existing PC UX; entity registry API enables 003 pipeline and future UI.

**Alternatives considered**:
- Entity browser UI: deferred to spec 005 or later
