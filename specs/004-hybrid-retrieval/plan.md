# Implementation Plan: Hybrid Retrieval

**Branch**: `004-hybrid-retrieval` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-hybrid-retrieval/spec.md`

**Depends on**: `003-knowledge-extraction-pipeline`

## Summary

Replace lexical-only `retrieve_chunks` with hybrid FTS5 + sqlite-vec search. Merge, rerank, prefer claims over raw chunks. Update `answer_question` for traceable citations (source title + claim quote). Remove unstructured PC roster preamble.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: sqlite-vec extension, FTS5 (SQLite built-in), Ollama chat

**Storage**: FTS5 virtual tables; sqlite-vec virtual table for chunk embeddings

**Testing**: pytest retrieval fixtures; golden-file citation tests

**Target Platform**: Local Docker Compose

**Performance Goals**: Ask p95 < 30s including Ollama

**Constraints**: FTS5-only fallback when embeddings unavailable

**Scale/Scope**: top-k=8 merged results; claims weighted 2x over chunks

## Constitution Check

### Pre-Design Gates

- [x] **Local-First (I)**: sqlite-vec local
- [x] **Source-Grounded (II)**: Citations with source title and claim quote
- [x] **Provenance (III)**: DISPUTED claims surfaced
- [x] **Discord-First (IV)**: /lore ask uses hybrid path
- [x] **Campaign Tone (V)**: Prompt unchanged for tone
- [x] **Simplicity (VI)**: Complexity Tracking documents hybrid need
- [x] **Test-First (VII)**: Retrieval tests before impl
- [x] **Campaign-Aware Knowledge (VIII)**: Claims preferred

### Post-Design Re-Check

Passes. Hybrid retrieval justified below.

## Project Structure

```text
apps/api/lore_goblin/
├── retrieval/
│   ├── __init__.py
│   ├── fts.py           # FTS5 queries
│   ├── vectors.py       # sqlite-vec queries
│   ├── hybrid.py        # merge + rerank
│   └── context.py       # build prompt context
├── answering.py         # refactored
└── migrations/
    └── 004_search_indexes.sql

apps/api/tests/
├── test_fts_retrieval.py
├── test_vector_retrieval.py
├── test_hybrid_retrieval.py
└── test_answering_citations.py
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hybrid FTS5 + sqlite-vec | Campaign memory needs proper nouns AND paraphrase | Lexical-only fails paraphrase; vector-only misses exact names |
| Claim-weighted rerank | Raw chunks duplicate and dilute structured facts | Chunk-only retrieval ignores campaign-aware model |

## Retrieval Strategy

1. Tokenize query; run FTS5 on entities, claims, sources
2. Embed query; run sqlite-vec k-NN on chunk embeddings
3. Merge by id; score = fts_rank * 1.0 + vec_sim * 1.0 + claim_bonus * 2.0 + importance_bonus
4. Take top 8; build context blocks (claims first, then entities, then chunks)
5. Ollama answer with cite-or-admit-unknown prompt

## Phase Artifacts

[research.md](./research.md) | [data-model.md](./data-model.md) | [quickstart.md](./quickstart.md)
