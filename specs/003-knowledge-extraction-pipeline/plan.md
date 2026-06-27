# Implementation Plan: Knowledge Extraction Pipeline

**Branch**: `003-knowledge-extraction-pipeline` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-knowledge-extraction-pipeline/spec.md`

**Depends on**: `002-campaign-knowledge-model`

## Summary

Background pipeline on source create/update: chunk → embed → extract entities (Ollama JSON) → resolve against existing entities → extract claims → extract relationships → score importance → auto-index. Entity resolution is the critical quality gate. Extraction failures do not block source ingest.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Ollama HTTP client, Pydantic, asyncio/thread pool for jobs

**Storage**: SQLite (tables from 002); embedding blobs for sqlite-vec (consumed by 004)

**Testing**: pytest with mocked Ollama; fixture corpus for entity resolution

**Target Platform**: Local Docker Compose with Ollama service

**Performance Goals**: Ingest API < 2s; extraction < 5min per typical note

**Constraints**: Auto-index (no review gate); async jobs

**Scale/Scope**: One job per source; retry 3x on failure

## Constitution Check

### Pre-Design Gates

- [x] **Local-First (I)**: Ollama local only
- [x] **Source-Grounded (II)**: Claims trace to source_id
- [x] **Provenance (III)**: No silent merge of conflicting claims
- [x] **Discord-First (IV)**: Ingest non-blocking for /lore session
- [x] **Campaign Tone (V)**: Extraction prompts factual, not tonal
- [x] **Simplicity (VI)**: Single pipeline module; no job queue service
- [x] **Test-First (VII)**: Resolution fixtures tested before impl
- [x] **Campaign-Aware Knowledge (VIII)**: Core deliverable

### Post-Design Re-Check

Passes. Background job runner justified in Complexity Tracking.

## Project Structure

```text
apps/api/lore_goblin/
├── prompts/
│   ├── entity_extraction_v1.txt
│   ├── entity_resolution_v1.txt
│   └── claim_extraction_v1.txt
├── extraction/
│   ├── pipeline.py
│   ├── entities.py
│   ├── claims.py
│   ├── relationships.py
│   ├── importance.py
│   └── jobs.py
├── embeddings.py          # local embed via Ollama
└── repository.py          # extended writes

apps/api/tests/
├── fixtures/extraction/
├── test_entity_extraction.py
├── test_entity_resolution.py
├── test_claim_extraction.py
└── test_pipeline.py
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Background job runner | Sync extraction blocks Discord ingest | Thread pool + SQLite job table sufficient vs Redis/Celery |
| Two-pass entity resolution | Single-pass creates duplicate entities | Core quality requirement |
| Versioned prompt files | Prompt iteration without code deploy | Inline strings untestable |

## Pipeline Sequence

1. Source stored (002) → enqueue job
2. Chunk source text
3. Generate embeddings per chunk → store for 004
4. Entity extraction (Ollama JSON)
5. Entity resolution (Ollama JSON vs candidates)
6. Persist entities, mentions, merged aliases
7. Claim extraction (Ollama JSON)
8. Relationship extraction
9. Recompute entity_importance
10. Mark job complete; indexes updated (FTS/vec in 004)

## Prompt Templates

See [contracts/prompts.md](./contracts/prompts.md).

## Phase Artifacts

[data-model.md](./data-model.md) | [research.md](./research.md) | [quickstart.md](./quickstart.md)
