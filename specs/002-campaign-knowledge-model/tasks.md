# Tasks: Campaign Knowledge Model

**Input**: Design documents from `/specs/002-campaign-knowledge-model/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: REQUIRED per Constitution Principle VII (Test-First Development).

**Organization**: Tasks grouped by user story (P1–P4).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: Migration infrastructure and shared types

- [X] T001 Create migrations directory `apps/api/lore_goblin/migrations/`
- [X] T002 [P] Add Pydantic enums for source_type and entity_type in `apps/api/lore_goblin/models.py`
- [X] T003 Add pytest fixtures for in-memory SQLite with legacy schema in `apps/api/tests/conftest.py`

---

## Phase 2: Foundational (Blocking)

**Purpose**: Schema and migration runner — MUST complete before user stories

- [X] T004 Write migration `apps/api/lore_goblin/migrations/001_campaign_knowledge.sql` per data-model.md
- [X] T005 Write migration `apps/api/lore_goblin/migrations/002_migrate_legacy_data.sql` for session_notes and player_characters backfill
- [X] T006 Implement migration runner with schema_version in `apps/api/lore_goblin/db.py`
- [X] T007 [P] Write failing migration tests in `apps/api/tests/test_migrations.py` (dry-run, idempotency, backfill counts)

**Checkpoint**: Migrations apply cleanly on fresh and legacy databases

---

## Phase 3: User Story 1 - Unified Sources (P1) 🎯 MVP

**Goal**: Session notes create traceable `source` records

**Independent Test**: POST session → GET sources returns SESSION_NOTE with author and session_id

### Tests for User Story 1 (write first, verify FAIL)

- [X] T008 [P] [US1] Contract test POST /sessions creates source in `apps/api/tests/test_sources.py`
- [X] T009 [P] [US1] Integration test source list filter by type in `apps/api/tests/test_sources.py`

### Implementation for User Story 1

- [X] T010 [US1] Add create_source and list_sources in `apps/api/lore_goblin/repository.py`
- [X] T011 [US1] Refactor add_session_note to dual-write source + link content_chunks.source_id in `apps/api/lore_goblin/repository.py`
- [X] T012 [US1] Add GET /campaigns/{id}/sources endpoint in `apps/api/lore_goblin/main.py`
- [X] T013 [US1] Verify T008–T009 pass

**Checkpoint**: Session ingest creates unified sources

---

## Phase 4: User Story 2 - Entity Registry (P2)

**Goal**: CRUD/list canonical entities with types and aliases

**Independent Test**: POST entity → GET entities returns PC/NPC with aliases

### Tests for User Story 2 (write first, verify FAIL)

- [X] T014 [P] [US2] Contract test POST /campaigns/{id}/entities in `apps/api/tests/test_entities.py`
- [X] T015 [P] [US2] Validation test invalid entity_type in `apps/api/tests/test_entities.py`

### Implementation for User Story 2

- [X] T016 [US2] Add create_entity and list_entities in `apps/api/lore_goblin/repository.py`
- [X] T017 [US2] Add GET and POST /campaigns/{id}/entities in `apps/api/lore_goblin/main.py`
- [X] T018 [US2] Verify T014–T015 pass

**Checkpoint**: Entity registry API functional

---

## Phase 5: User Story 3 - Data Migration (P3)

**Goal**: Idempotent legacy data migration with dry-run

**Independent Test**: Legacy DB → migrate → counts match; re-run → zero new rows

### Tests for User Story 3 (write first, verify FAIL)

- [X] T019 [P] [US3] Integration test legacy session_notes → sources in `apps/api/tests/test_migrations.py`
- [X] T020 [P] [US3] Integration test legacy player_characters → entities in `apps/api/tests/test_migrations.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement run_migration(dry_run) in `apps/api/lore_goblin/migrations/runner.py`
- [X] T022 [US3] Add POST /admin/migrate endpoint in `apps/api/lore_goblin/main.py`
- [X] T023 [US3] Auto-run pending migrations on startup in `apps/api/lore_goblin/db.py`
- [X] T024 [US3] Verify T019–T020 pass

**Checkpoint**: Existing deployments upgrade safely

---

## Phase 6: User Story 4 - PC Roster Preserved (P4)

**Goal**: Web/Discord PC flows use entity+source; API shape unchanged

**Independent Test**: /lore pc and web roster work; data in entity table

### Tests for User Story 4 (write first, verify FAIL)

- [X] T025 [P] [US4] Compatibility test GET /player-characters response shape in `apps/api/tests/test_player_characters_compat.py`
- [X] T026 [P] [US4] Test POST /player-characters creates entity+source in `apps/api/tests/test_player_characters_compat.py`

### Implementation for User Story 4

- [X] T027 [US4] Refactor create_player_character to write entity+source in `apps/api/lore_goblin/repository.py`
- [X] T028 [US4] Refactor list_player_characters to read from entity+source with legacy fallback in `apps/api/lore_goblin/repository.py`
- [X] T029 [US4] Verify web roster still works in `apps/web/` (no API shape change)
- [X] T030 [US4] Verify T025–T026 pass

**Checkpoint**: PC roster UX preserved on new model

---

## Phase 7: Polish

- [X] T031 [P] Update `specs/002-campaign-knowledge-model/quickstart.md` if endpoint paths differ
- [X] T032 Run full API test suite `cd apps/api && pytest -v`
- [X] T033 Run web build `cd apps/web && npm run build`

---

## Dependencies

```text
Phase 1–2 (foundation) → US1 (sources) → US2 (entities) → US3 (migration) → US4 (PC compat)
US1 and US2 can proceed in parallel after Phase 2
US3 depends on US1 schema paths
US4 depends on US2 entity writes and US3 migration for legacy PCs
```

## Parallel Example

After Phase 2: T010–T013 (US1) and T016–T018 (US2) in parallel.

## MVP Scope

**User Story 1 only** (Phase 3): Unified sources for session notes.
