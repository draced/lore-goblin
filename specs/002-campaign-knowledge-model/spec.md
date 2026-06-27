# Feature Specification: Campaign Knowledge Model

> Feature specs MUST follow the Development Workflow in `.specify/memory/constitution.md`.

**Feature Branch**: `002-campaign-knowledge-model`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Foundational campaign-aware data model: Source → Extracted Claims → Entities → Relationships → Search Index. Unifies session notes and player characters under a traceable source/entity schema with versioned migrations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unified Sources (Priority: P1)

A campaign owner or player submits session notes or player character descriptions. Lore Goblin stores each submission as a `source` record with campaign scope, source type, author provenance, and optional session linkage so every fact can trace back to evidence.

**Why this priority**: Sources are the root of campaign-aware knowledge. Without a unified source model, entities and claims cannot be attributed.

**Independent Test**: Submit a session note and a player character description; confirm each appears as a distinct `source` with correct type, author, and campaign without using extraction or hybrid search.

**Acceptance Scenarios**:

1. **Given** a campaign exists, **When** a user submits session notes via web or Discord, **Then** a `source` row is created with `source_type=SESSION_NOTE`, body text, author, and `session_id`.
2. **Given** a campaign exists, **When** a user adds a player character with name and notes, **Then** a `source` row is created with `source_type=PLAYER_CHARACTER_DESC` and the notes as body.
3. **Given** a source is created, **When** the record is retrieved, **Then** campaign_id, title, author, created_at, and source_type are present.
4. **Given** a user submits to a missing campaign, **When** the request is processed, **Then** the system rejects it with a clear error.

---

### User Story 2 - Entity Registry (Priority: P2)

A campaign owner or player registers canonical campaign objects (player characters, NPCs, locations, items, etc.) as `entity` records with type, name, aliases, and summary. The registry is campaign-scoped and supports listing and creation.

**Why this priority**: Entities are the canonical "who, what, where" objects that claims and relationships attach to.

**Independent Test**: Create entities of types `PC` and `LOCATION` with aliases; list all entities for a campaign and confirm names, types, and aliases are returned.

**Acceptance Scenarios**:

1. **Given** a campaign exists, **When** a user creates an entity with name, type, and summary, **Then** the entity is stored and returned with a unique id.
2. **Given** a campaign has multiple entities, **When** the user lists entities for that campaign, **Then** all entities are returned scoped to that campaign only.
3. **Given** a user provides aliases for an entity, **When** the entity is stored, **Then** aliases are preserved and retrievable.
4. **Given** an invalid entity type is submitted, **When** creation is attempted, **Then** the system rejects with a validation error.

---

### User Story 3 - Data Migration (Priority: P3)

An existing Lore Goblin installation with MVP1 session notes and player characters is upgraded without data loss. Legacy tables are migrated to the new model via an idempotent, versioned migration runner.

**Why this priority**: The feature replaces foundational storage; existing campaigns must survive the upgrade.

**Independent Test**: Run migration against a database with existing `session_notes` and `player_characters`; verify equivalent `source` and `entity` rows exist and legacy API flows still work.

**Acceptance Scenarios**:

1. **Given** a database with existing session notes, **When** migration runs, **Then** each note becomes a `SESSION_NOTE` source with preserved author and session linkage.
2. **Given** a database with existing player characters, **When** migration runs, **Then** each character becomes a `PC` entity plus a `PLAYER_CHARACTER_DESC` source.
3. **Given** migration has already run, **When** migration runs again, **Then** no duplicate sources or entities are created.
4. **Given** a dry-run mode is requested, **When** migration executes, **Then** a report of planned changes is produced without modifying data.

---

### User Story 4 - PC Roster Preserved (Priority: P4)

Players continue to add and view player characters through the existing web UI and Discord `/lore pc` command. API response shapes remain compatible; internally, data is written to `entity` + `source` instead of `player_characters`.

**Why this priority**: Discord-first UX must not regress while the data model changes underneath.

**Independent Test**: Add a PC via web and Discord; list roster via web; confirm same UX as before with data stored in the new model.

**Acceptance Scenarios**:

1. **Given** a linked Discord guild, **When** `/lore pc` is used with valid name and notes, **Then** a PC entity and source are created and confirmation is returned.
2. **Given** a campaign with PCs, **When** the web roster is loaded, **Then** all player characters display with name and notes.
3. **Given** blank name or notes, **When** PC creation is attempted, **Then** validation fails on web and Discord.
4. **Given** migration completed, **When** roster is listed, **Then** migrated legacy PCs appear alongside newly added PCs.

---

### Edge Cases

- What happens when two entities share the same name? Both are allowed; entity resolution in spec 003 handles deduplication during extraction, not at manual create time.
- What happens when a campaign is deleted? All sources, entities, claims, mentions, relationships, and importance rows for that campaign are removed.
- What happens when `content_chunks` exist without a migrated source? Migration links chunks to the corresponding `source_id` or reports orphans in dry-run.
- What happens when session notes and PC descriptions conflict? Both sources are preserved; no silent merge (Principle III).
- What happens during migration if the API is running? Migration is an offline/admin operation; documentation specifies stopping services or running at startup before serving traffic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store every session note submission as a `source` with `source_type=SESSION_NOTE`.
- **FR-002**: System MUST store every player character description as a `source` with `source_type=PLAYER_CHARACTER_DESC` and a linked `entity` with `entity_type=PC`.
- **FR-003**: Each `source` MUST belong to exactly one campaign and record author provenance.
- **FR-004**: System MUST support `source_type` values: `SESSION_NOTE`, `PLAYER_CHARACTER_DESC`, `ITEM_DESC`, `NPC_DESC`, `LOCATION_DESC`, `MANUAL_EDIT`.
- **FR-005**: System MUST support `entity_type` values: `PC`, `NPC`, `LOCATION`, `FACTION`, `ITEM`, `QUEST`, `EVENT`, `DEITY`, `MONSTER`, `ORGANIZATION`, `RUMOR`.
- **FR-006**: System MUST provide create and list operations for entities scoped to a campaign.
- **FR-007**: System MUST provide create and list operations for sources scoped to a campaign.
- **FR-008**: System MUST run versioned schema migrations via a `schema_version` table and numbered SQL scripts.
- **FR-009**: Migration MUST be idempotent and support dry-run reporting.
- **FR-010**: Migration MUST convert existing `session_notes` and `player_characters` without data loss.
- **FR-011**: `content_chunks` MUST gain a `source_id` foreign key linking chunks to unified sources.
- **FR-012**: Web and Discord PC roster flows MUST remain functional with backward-compatible API responses.
- **FR-013**: System MUST create empty `claim`, `entity_mention`, `relationship`, and `entity_importance` tables for use by specs 003–004.
- **FR-014**: System MUST NOT populate claims or run extraction (deferred to spec 003).
- **FR-015**: System MUST NOT implement hybrid search (deferred to spec 004).

### Key Entities

- **Source**: Evidence record (session note, PC description, manual edit). Attributes: campaign, type, title, body, author, optional session, timestamps.
- **Entity**: Canonical campaign object (PC, NPC, location, item, etc.). Attributes: campaign, type, name, aliases, summary, timestamps.
- **Claim**: Atomic attributed statement (schema only in 002; populated in 003). Links subject entity, predicate, object entity, canon status, source.
- **Entity Mention**: Text span linking source text to an entity (schema only in 002).
- **Relationship**: Durable typed edge between entities with source provenance (schema only in 002).
- **Entity Importance**: Denormalized scoring row per entity (schema only in 002; populated in 003).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of new session note submissions create a traceable `source` row with author and session linkage.
- **SC-002**: Migration of a test database with 10 session notes and 5 player characters produces 15 sources and 5 PC entities with zero data loss.
- **SC-003**: Re-running migration produces zero duplicate records.
- **SC-004**: Web and Discord PC add/list flows pass existing acceptance scenarios without UX change.
- **SC-005**: `/lore session` and `/lore ask` regression tests pass after migration (answers may still use legacy retrieval until spec 004).

## Assumptions

- MVP1 campaign setup, guild linking, and ask flows remain; this feature changes storage and adds APIs, not player-facing ask behavior (until spec 004).
- Ollama extraction, entity resolution, hybrid search, and review queue are out of scope (specs 003–005).
- `sessions`, `campaigns`, and `users` tables are unchanged except via foreign keys from new tables.
- `player_characters` table is deprecated after migration; reads/writes route through entity+source, then table is dropped in a later migration.
- No permission model restricts who may add sources or entities beyond existing campaign access patterns.
