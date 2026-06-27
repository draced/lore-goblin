# Feature Specification: Knowledge Extraction Pipeline

> Feature specs MUST follow the Development Workflow in `.specify/memory/constitution.md`.

**Feature Branch**: `003-knowledge-extraction-pipeline`

**Created**: 2026-06-27

**Status**: Draft

**Depends on**: `002-campaign-knowledge-model`

**Input**: User description: "On source ingest, run background extraction pipeline: chunk, embed, extract entities, resolve against existing entities, extract claims and relationships, score importance, auto-index without human review."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity Extraction (Priority: P1)

When a source is added or updated, Lore Goblin uses Ollama to extract campaign entities as structured JSON: name, type, aliases, short description, importance, and evidence quote from the source text.

**Why this priority**: Entity extraction is the first structured step; without it, claims and relationships have nothing to attach to.

**Independent Test**: Submit a session note mentioning "Father Aldren" and "Ruined Chapel"; confirm extracted entity records appear in pipeline output with types and evidence quotes.

**Acceptance Scenarios**:

1. **Given** a new `SESSION_NOTE` source, **When** extraction runs, **Then** Ollama returns valid JSON listing entities with name, type, aliases, short_description, importance, and evidence_quote.
2. **Given** extraction completes, **When** entities are persisted, **Then** `entity_mention` rows link mention text and offsets to source spans.
3. **Given** Ollama returns malformed JSON, **When** extraction fails, **Then** the source is still stored and extraction is queued for retry with visible error status.
4. **Given** a source with no mentionable entities, **When** extraction runs, **Then** an empty entity list is accepted without error.

---

### User Story 2 - Entity Resolution (Priority: P2)

Extracted entities are matched against existing campaign entities before creating new records. Aliases are merged so "Father Aldren", "Aldren", and "Priest Aldren" resolve to one canonical entity.

**Why this priority**: Entity resolution is the highest-risk quality step; duplicate entities destroy campaign memory.

**Independent Test**: Pre-seed entity "Father Aldren"; submit a note mentioning "Aldren"; confirm no duplicate entity is created and alias is merged.

**Acceptance Scenarios**:

1. **Given** existing entity "Father Aldren" (NPC), **When** a note mentions "Aldren", **Then** resolution matches to the existing entity id with documented confidence.
2. **Given** no matching entity, **When** resolution confidence is below threshold, **Then** a new entity is created with extracted aliases.
3. **Given** resolution matches an entity, **When** new aliases are found, **Then** aliases are merged into `aliases_json` without duplicating names.
4. **Given** ambiguous match (two candidates with similar names), **When** resolution runs, **Then** the lower-confidence match is not auto-merged; a new entity or DISPUTED flag is recorded per policy.

---

### User Story 3 - Claim Extraction (Priority: P3)

After entities are resolved, Lore Goblin extracts atomic claims: one fact per claim, with subject, predicate, object, canon status, importance, and source quote. Theories are not marked confirmed; facts are not invented.

**Why this priority**: Claims enable traceable answers (Principle II and VIII).

**Independent Test**: Submit note "The party found the silver key in the ruined chapel"; confirm claims with `found_at` predicate linking Party → Silver Key → Ruined Chapel.

**Acceptance Scenarios**:

1. **Given** resolved entities, **When** claim extraction runs, **Then** each claim has claim_text, subject_entity_id, predicate, object_entity_id (when applicable), canon_status, and source_id.
2. **Given** uncertain language ("might be", "rumored"), **When** claims are extracted, **Then** canon_status is `RUMOR` or `THEORY`, not `CONFIRMED`.
3. **Given** no supporting text in the source, **When** claim extraction runs, **Then** no claim is invented.
4. **Given** multiple facts in one sentence, **When** extraction runs, **Then** each fact becomes a separate claim.

---

### User Story 4 - Relationship Extraction (Priority: P4)

Durable relationships are extracted and stored as typed edges between entities with source provenance (e.g. `brother_of`, `opens`, `kidnapped`).

**Why this priority**: Relationships support graph traversal and importance scoring beyond flat claims.

**Independent Test**: Submit note "Father Aldren is the brother of Mayor Seraphine"; confirm `relationship` row with type `brother_of` and source_id.

**Acceptance Scenarios**:

1. **Given** resolved entities and extracted claims, **When** relationship extraction runs, **Then** `relationship` rows link source_entity_id, target_entity_id, relationship_type, and source_id.
2. **Given** a relationship already exists from a prior source, **When** the same relationship is extracted again, **Then** a new relationship row is created (provenance preserved) or deduplicated per policy documented in plan.
3. **Given** conflicting relationships, **When** both are stored, **Then** neither is silently merged.

---

### User Story 5 - Importance Scoring (Priority: P5)

Lore Goblin maintains `entity_importance` scores per entity using mention count, session count, relationship count, unresolved claim count, manual pin bonus, and recent mention bonus.

**Why this priority**: Enables automatic surfacing of important NPCs, items, and locations without manual curation.

**Independent Test**: Submit notes across two sessions mentioning the same NPC; confirm importance_score increases and session_count reflects two sessions.

**Acceptance Scenarios**:

1. **Given** entities with mentions and relationships, **When** scoring runs, **Then** `entity_importance` rows are updated with component counts and composite score.
2. **Given** an entity mentioned in the latest session, **When** scoring runs, **Then** `last_seen_session_id` and recency bonus are updated.
3. **Given** claims with `canon_status` of `THEORY` or `DISPUTED`, **When** scoring runs, **Then** `unresolved_claim_count` reflects them.
4. **Given** a manually pinned entity, **When** scoring runs, **Then** pin bonus is applied.

---

### Edge Cases

- What happens when Ollama is unavailable? Extraction is queued; source ingest succeeds; retry with backoff.
- What happens when extraction runs on a very long source? Chunking splits text; extraction runs per chunk with entity resolution across chunks.
- What happens when entity type is unknown? Extract as `UNKNOWN` type; resolution may reclassify on merge.
- What happens on source update? Re-extraction runs; stale claims/mentions from prior extraction are superseded or versioned per plan policy.
- What happens during concurrent note submissions? Pipeline jobs are serialized per campaign or use idempotent job keys.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run extraction asynchronously after source create/update without blocking ingest API responses.
- **FR-002**: System MUST chunk source text before embedding and extraction.
- **FR-003**: System MUST generate embeddings for chunks (stored for spec 004 retrieval).
- **FR-004**: System MUST use Ollama structured JSON for entity extraction per versioned prompt template.
- **FR-005**: System MUST run a second-pass entity resolution prompt against existing campaign entities.
- **FR-006**: Entity resolution MUST NOT create duplicate canonical entities for known alias variants when confidence exceeds threshold.
- **FR-007**: System MUST extract claims using only resolved entity ids where possible.
- **FR-008**: Claim extraction MUST preserve uncertainty (`RUMOR`, `THEORY`, `DISPUTED`) and MUST NOT invent facts.
- **FR-009**: System MUST extract and persist relationships with source provenance.
- **FR-010**: System MUST recompute `entity_importance` after each successful extraction job.
- **FR-011**: System MUST auto-index extracted knowledge immediately (no human review gate).
- **FR-012**: Extraction failures MUST NOT roll back source storage.
- **FR-013**: System MUST expose extraction job status per source (pending, running, complete, failed).
- **FR-014**: System MUST flag significant changes (new major entity, conflicting claim) for logging; review UI deferred to spec 005.
- **FR-015**: Prompt templates MUST be versioned in `apps/api/lore_goblin/prompts/`.

### Key Entities

- **Extraction Job**: Tracks pipeline state per source (status, error, timestamps).
- **Entity** (from 002): Populated and updated by resolution.
- **Claim** (from 002): Populated by claim extraction.
- **Relationship** (from 002): Populated by relationship extraction.
- **Entity Mention** (from 002): Populated during entity extraction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Source ingest API responds in under 2 seconds regardless of extraction completion.
- **SC-002**: Entity resolution test suite: 95% of alias variants in fixture set match correct canonical entity.
- **SC-003**: Claim extraction test suite: zero invented claims in negative-control sources.
- **SC-004**: Extraction completes for a typical session note (500–2000 words) within 5 minutes on local Ollama hardware.
- **SC-005**: Failed extraction retries at least 3 times before marking source as failed.

## Assumptions

- Spec 002 schema and source ingest are complete.
- Human review queue is out of scope (spec 005); extracted knowledge is auto-indexed.
- Hybrid FTS5/vector retrieval consumes embeddings in spec 004.
- Default Ollama chat model is configured per campaign via existing `model_settings`.
- Embedding model choice documented in plan.md (e.g. `nomic-embed-text` via Ollama).
