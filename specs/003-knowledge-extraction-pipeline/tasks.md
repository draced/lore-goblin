# Tasks: Knowledge Extraction Pipeline

**Input**: Design documents from `/specs/003-knowledge-extraction-pipeline/`

**Prerequisites**: 002 implemented; plan.md, spec.md, data-model.md, contracts/prompts.md

**Tests**: REQUIRED per Constitution Principle VII.

## Phase 1: Setup

- [X] T001 Create `apps/api/lore_goblin/extraction/` package with `__init__.py`
- [X] T002 [P] Add prompt templates in `apps/api/lore_goblin/prompts/` per contracts/prompts.md
- [X] T003 [P] Add Pydantic schemas in `apps/api/lore_goblin/extraction/schemas.py`
- [X] T004 [P] Add extraction fixtures in `apps/api/tests/fixtures/extraction/`

---

## Phase 2: Foundational

- [X] T005 Write migration `003_extraction_jobs.sql` for extraction_job and chunk_embedding tables
- [X] T006 Implement Ollama JSON chat helper in `apps/api/lore_goblin/extraction/ollama_json.py`
- [X] T007 Implement embedding client in `apps/api/lore_goblin/embeddings.py` (nomic-embed-text)
- [X] T008 Implement job enqueue/status in `apps/api/lore_goblin/extraction/jobs.py`
- [X] T009 [P] Write failing job lifecycle tests in `apps/api/tests/test_pipeline.py`

**Checkpoint**: Jobs can be enqueued and tracked

---

## Phase 3: User Story 1 - Entity Extraction (P1) 🎯 MVP

**Goal**: Ollama extracts entities with mentions from source text

**Independent Test**: Submit source → entities and entity_mention rows created

### Tests (write first, verify FAIL)

- [X] T010 [P] [US1] Unit test entity JSON parsing in `apps/api/tests/test_entity_extraction.py`
- [X] T011 [P] [US1] Integration test mention offsets in `apps/api/tests/test_entity_extraction.py`

### Implementation

- [X] T012 [US1] Implement entity extraction in `apps/api/lore_goblin/extraction/entities.py`
- [X] T013 [US1] Persist entity_mention rows in `apps/api/lore_goblin/repository.py`
- [X] T014 [US1] Wire entity extraction step in `apps/api/lore_goblin/extraction/pipeline.py`
- [X] T015 [US1] Verify T010–T011 pass

---

## Phase 4: User Story 2 - Entity Resolution (P2)

**Goal**: Alias variants resolve to single canonical entity

**Independent Test**: Pre-seed Aldren → note says "Father Aldren" → one entity

### Tests (write first, verify FAIL)

- [X] T016 [P] [US2] Fixture test 95% alias resolution in `apps/api/tests/test_entity_resolution.py`
- [X] T017 [P] [US2] Test no false merge below confidence threshold in `apps/api/tests/test_entity_resolution.py`

### Implementation

- [X] T018 [US2] Implement resolution pass in `apps/api/lore_goblin/extraction/entities.py`
- [X] T019 [US2] Implement alias merge logic in `apps/api/lore_goblin/repository.py`
- [X] T020 [US2] Wire resolution into pipeline in `apps/api/lore_goblin/extraction/pipeline.py`
- [X] T021 [US2] Verify T016–T017 pass

---

## Phase 5: User Story 3 - Claim Extraction (P3)

**Goal**: Atomic claims with canon_status and source quotes

### Tests (write first, verify FAIL)

- [X] T022 [P] [US3] Test claim persistence in `apps/api/tests/test_claim_extraction.py`
- [X] T023 [P] [US3] Negative test no invented claims in `apps/api/tests/test_claim_extraction.py`

### Implementation

- [X] T024 [US3] Implement claim extraction in `apps/api/lore_goblin/extraction/claims.py`
- [X] T025 [US3] Wire claims into pipeline in `apps/api/lore_goblin/extraction/pipeline.py`
- [X] T026 [US3] Verify T022–T023 pass

---

## Phase 6: User Story 4 - Relationship Extraction (P4)

### Tests (write first, verify FAIL)

- [X] T027 [P] [US4] Test relationship persistence in `apps/api/tests/test_claim_extraction.py`

### Implementation

- [X] T028 [US4] Implement relationship extraction in `apps/api/lore_goblin/extraction/relationships.py`
- [X] T029 [US4] Wire relationships into pipeline
- [X] T030 [US4] Verify T027 pass

---

## Phase 7: User Story 5 - Importance Scoring (P5)

### Tests (write first, verify FAIL)

- [X] T031 [P] [US5] Test importance formula in `apps/api/tests/test_pipeline.py`

### Implementation

- [X] T032 [US5] Implement scoring in `apps/api/lore_goblin/extraction/importance.py`
- [X] T033 [US5] Hook scoring after pipeline complete
- [X] T034 [US5] Add GET /sources/{id}/extraction-status in `apps/api/lore_goblin/main.py`
- [X] T035 [US5] Enqueue job on source create in `apps/api/lore_goblin/repository.py`
- [X] T036 [US5] Verify T031 pass

---

## Phase 8: Polish

- [X] T037 [P] Add retry logic (3 attempts) in `apps/api/lore_goblin/extraction/jobs.py`
- [X] T038 Run full extraction test suite `cd apps/api && pytest tests/test_entity*.py tests/test_claim*.py tests/test_pipeline.py -v`

## MVP Scope

User Stories 1–2: Entity extraction + resolution.

## Dependencies

002 complete → Phase 1–2 → US1 → US2 → US3 → US4 → US5
