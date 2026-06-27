# Feature Specification: Hybrid Retrieval

> Feature specs MUST follow the Development Workflow in `.specify/memory/constitution.md`.

**Feature Branch**: `004-hybrid-retrieval`

**Created**: 2026-06-27

**Status**: Draft

**Depends on**: `003-knowledge-extraction-pipeline`

**Input**: User description: "Replace lexical-only chunk retrieval with hybrid FTS5 + sqlite-vec search. Merge and rerank results; prefer claims over raw notes; cite sources and claim quotes in answers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - FTS5 Lexical Search (Priority: P1)

When a user asks a campaign question, Lore Goblin searches SQLite FTS5 indexes over entity names, aliases, claim text, and source titles for exact and near-exact term matches.

**Why this priority**: Name and term lookup is critical for TTRPG campaigns with distinctive proper nouns.

**Independent Test**: Index entities "Silver Key" and "Ruined Chapel"; ask "Where is the silver key?"; confirm FTS5 returns relevant entity and claim matches.

**Acceptance Scenarios**:

1. **Given** indexed entities and claims, **When** a query contains an entity name, **Then** FTS5 returns matching records ranked by relevance.
2. **Given** an entity alias in `aliases_json`, **When** the query uses the alias, **Then** FTS5 matches the canonical entity.
3. **Given** no FTS5 matches, **When** retrieval continues, **Then** vector search is still attempted (hybrid fallback).
4. **Given** campaign scope, **When** FTS5 runs, **Then** only records for the selected campaign are returned.

---

### User Story 2 - Vector Semantic Search (Priority: P2)

Lore Goblin searches chunk embeddings via sqlite-vec for semantic matches when lexical search alone is insufficient.

**Why this priority**: Players ask natural-language questions that do not repeat exact note wording.

**Independent Test**: Ask a paraphrased question about a session event; confirm vector search returns the semantically related chunk.

**Acceptance Scenarios**:

1. **Given** embedded content chunks, **When** a semantic query is submitted, **Then** sqlite-vec returns top-k similar chunks by cosine distance.
2. **Given** embeddings from spec 003 pipeline, **When** a new source is indexed, **Then** vectors are searchable within one extraction job completion.
3. **Given** local embedding model unavailable, **When** ask is requested, **Then** FTS5-only fallback runs with degraded-but-functional behavior.

---

### User Story 3 - Hybrid Merge and Rerank (Priority: P3)

FTS5 and vector results are merged, deduplicated, and reranked into a unified context set for answer generation.

**Why this priority**: Neither lexical nor semantic search alone covers all query types.

**Independent Test**: Run queries that favor lexical (proper noun) and semantic (paraphrase) cases; confirm merged results include best of both.

**Acceptance Scenarios**:

1. **Given** results from FTS5 and vector search, **When** merge runs, **Then** duplicates are collapsed and a combined ranking is produced.
2. **Given** a claim and a raw chunk about the same fact, **When** reranking runs, **Then** the claim ranks higher than the raw chunk.
3. **Given** broad recap queries ("what happened last session"), **When** retrieval runs, **Then** recent session sources are boosted per policy.

---

### User Story 4 - Traceable Answers (Priority: P4)

Lore Goblin answers using retrieved context only, preferring claims over raw notes, and cites source title/type with optional claim quote. Player characters are retrieved as entities, not injected as unstructured preamble.

**Why this priority**: Delivers the campaign-aware answer experience promised by Principles II and VIII.

**Independent Test**: Ask about a confirmed claim; confirm answer cites source and includes claim text; ask about unknown fact; confirm admit-unknown response.

**Acceptance Scenarios**:

1. **Given** retrieved claims and sources, **When** Ollama generates an answer, **Then** the answer uses only retrieved context.
2. **Given** a CONFIRMED claim supports the answer, **When** citations are built, **Then** citation includes source title and claim quote.
3. **Given** conflicting claims (DISPUTED), **When** an answer is generated, **Then** disagreement is surfaced without silent merge.
4. **Given** no relevant retrieved context, **When** ask is processed, **Then** Lore Goblin admits it does not know.
5. **Given** PC entities exist, **When** a party-related question is asked, **Then** PC entities are retrieved via hybrid search, not static roster injection.

---

### Edge Cases

- What happens when extraction has not run for a campaign? Fallback to chunk lexical/vector search on raw sources; no claims available.
- What happens when FTS5 and vector disagree? Merge policy weights both; claims always preferred when present.
- What happens with very large campaigns? Top-k limits prevent context overflow; importance scores boost high-value entities.
- What happens when Ollama is down? Return error message; do not fabricate answers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain FTS5 virtual tables for entity names, aliases, claims, and source titles.
- **FR-002**: System MUST store chunk embeddings in sqlite-vec with campaign scope.
- **FR-003**: System MUST use a local embedding model (Ollama-compatible or dedicated endpoint).
- **FR-004**: Retrieval MUST merge FTS5 and vector results with documented rerank policy.
- **FR-005**: Retrieval MUST prefer claims over raw note chunks when both match.
- **FR-006**: Answers MUST cite source title and type; include claim quote when claim evidence is used.
- **FR-007**: Answers MUST NOT use information outside retrieved context.
- **FR-008**: System MUST replace legacy lexical-only `retrieve_chunks` as primary retrieval path.
- **FR-009**: System MUST remove unstructured PC roster preamble injection; PCs retrieved as entities.
- **FR-010**: `/lore ask` and web ask MUST use hybrid retrieval when indexes are available.
- **FR-011**: Complexity Tracking in plan.md MUST justify hybrid retrieval per Constitution VI.

### Key Entities

- **FTS Index**: Virtual table syncing entity, claim, and source searchable text.
- **Vector Index**: sqlite-vec table keyed by chunk id with embedding vector.
- **Retrieved Context**: Merged ranked set of claims, entities, chunks, and sources for prompt assembly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Proper-noun queries return relevant entity or claim in top-3 results for 90% of fixture queries.
- **SC-002**: Paraphrased queries return relevant chunk or claim in top-5 results for 80% of fixture queries.
- **SC-003**: 100% of answers with claim evidence include source citation with title.
- **SC-004**: Ask endpoint p95 latency under 30 seconds including Ollama generation on local hardware.
- **SC-005**: Regression: admit-unknown behavior preserved when no context matches.

## Assumptions

- Spec 003 provides embeddings and populated claims/entities.
- sqlite-vec extension is bundled or installed in API Docker image.
- Default embedding model documented in plan.md and Docker Compose.
- Legacy `content_chunks` retrieval remains as fallback until indexes are built.
