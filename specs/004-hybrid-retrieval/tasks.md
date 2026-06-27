# Tasks: Hybrid Retrieval

**Input**: Design documents from `/specs/004-hybrid-retrieval/`

**Prerequisites**: 003 implemented; plan.md, spec.md, data-model.md

**Tests**: REQUIRED per Constitution Principle VII.

## Phase 1: Setup

- [X] T001 Add sqlite-vec to API Docker image in `apps/api/Dockerfile`
- [X] T002 [P] Create `apps/api/lore_goblin/retrieval/` package
- [X] T003 Write migration `004_search_indexes.sql` for FTS5 and vec0 tables

---

## Phase 2: Foundational

- [X] T004 Implement FTS5 sync triggers in migration `004_search_indexes.sql`
- [X] T005 Implement vector index sync from chunk_embedding in `apps/api/lore_goblin/retrieval/vectors.py`
- [X] T006 [P] Write failing FTS tests in `apps/api/tests/test_fts_retrieval.py`
- [X] T007 [P] Write failing vector tests in `apps/api/tests/test_vector_retrieval.py`

**Checkpoint**: Indexes queryable in isolation

---

## Phase 3: User Story 1 - FTS5 Lexical Search (P1)

### Tests (write first, verify FAIL)

- [X] T008 [P] [US1] Test entity name match in `apps/api/tests/test_fts_retrieval.py`
- [X] T009 [P] [US1] Test alias match in `apps/api/tests/test_fts_retrieval.py`

### Implementation

- [X] T010 [US1] Implement FTS queries in `apps/api/lore_goblin/retrieval/fts.py`
- [X] T011 [US1] Verify T008–T009 pass

---

## Phase 4: User Story 2 - Vector Semantic Search (P2)

### Tests (write first, verify FAIL)

- [X] T012 [P] [US2] Test k-NN chunk retrieval in `apps/api/tests/test_vector_retrieval.py`

### Implementation

- [X] T013 [US2] Implement vector search in `apps/api/lore_goblin/retrieval/vectors.py`
- [X] T014 [US2] Verify T012 pass

---

## Phase 5: User Story 3 - Hybrid Merge and Rerank (P3)

### Tests (write first, verify FAIL)

- [X] T015 [P] [US3] Test merge dedup in `apps/api/tests/test_hybrid_retrieval.py`
- [X] T016 [P] [US3] Test claim preference over chunk in `apps/api/tests/test_hybrid_retrieval.py`

### Implementation

- [X] T017 [US3] Implement hybrid merge in `apps/api/lore_goblin/retrieval/hybrid.py`
- [X] T018 [US3] Replace retrieve_chunks entry point; deprecate old `apps/api/lore_goblin/retrieval.py`
- [X] T019 [US3] Verify T015–T016 pass

---

## Phase 6: User Story 4 - Traceable Answers (P4)

### Tests (write first, verify FAIL)

- [X] T020 [P] [US4] Test citation shape with source title in `apps/api/tests/test_answering_citations.py`
- [X] T021 [P] [US4] Test admit-unknown when no context in `apps/api/tests/test_answering_citations.py`
- [X] T022 [P] [US4] Test DISPUTED claim surfacing in `apps/api/tests/test_answering_citations.py`

### Implementation

- [X] T023 [US4] Implement context builder in `apps/api/lore_goblin/retrieval/context.py`
- [X] T024 [US4] Refactor answer_question in `apps/api/lore_goblin/answering.py` (remove PC preamble)
- [X] T025 [US4] Update citation builder for source title + claim quote
- [X] T026 [US4] Add POST /admin/reindex-search in `apps/api/lore_goblin/main.py`
- [X] T027 [US4] Verify T020–T022 pass

---

## Phase 7: Polish

- [X] T028 Regression test /lore ask via Discord bot integration
- [X] T029 Run full API test suite `cd apps/api && pytest -v`
- [X] T030 Update `specs/004-hybrid-retrieval/quickstart.md` if needed

## MVP Scope

User Stories 1 + 3 + 4 (FTS + merge + traceable answers); vector leg can follow in same release.

## Dependencies

003 complete → Phase 1–2 → US1, US2 parallel → US3 → US4
