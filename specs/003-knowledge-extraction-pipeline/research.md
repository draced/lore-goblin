# Research: Knowledge Extraction Pipeline

## Decision: In-process thread pool job runner

**Decision**: SQLite `extraction_job` table + background threads in FastAPI lifespan; no Celery/Redis.

**Rationale**: Constitution VI YAGNI; local-first single-node deployment.

**Alternatives considered**:
- APScheduler: acceptable fallback if thread pool insufficient
- Sync extraction: rejected; blocks ingest

## Decision: Entity resolution confidence threshold 0.75

**Decision**: Match existing entity when resolution confidence ≥ 0.75; otherwise create new entity.

**Rationale**: Balance duplicate prevention vs false merges. Tunable via config.

**Alternatives considered**:
- Always create new: rejected; destroys campaign memory
- Always merge on fuzzy name: rejected; false merges worse than duplicates

## Decision: Default embedding model nomic-embed-text via Ollama

**Decision**: `nomic-embed-text` pulled in Docker Compose; 768-dim vectors.

**Rationale**: Common Ollama embedding model; local-first.

**Alternatives considered**:
- all-minilm: smaller but less accurate for proper nouns

## Decision: Re-extraction supersedes prior extraction artifacts

**Decision**: On source update, delete claims/mentions/relationships from prior job for that source_id before re-extract.

**Rationale**: Avoid duplicate claims; source is authoritative.

**Alternatives considered**:
- Versioned claims: deferred; adds complexity without review UI (005)

## Decision: Relationship deduplication within same source

**Decision**: Dedupe identical (source_entity, target_entity, relationship_type) within one extraction job; allow duplicates across sources.

**Rationale**: Provenance per source; cross-source duplicates are evidence of repeated fact.
