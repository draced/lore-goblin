# Research: Hybrid Retrieval

## Decision: sqlite-vec with vec0 module

**Decision**: Use `sqlite-vec` vec0 virtual table; 768 dimensions matching nomic-embed-text.

**Rationale**: Constitution permits documented hybrid; single SQLite file; local-first.

**Alternatives considered**:
- ChromaDB: rejected; extra service violates simplicity
- In-memory numpy search: rejected; does not scale to large campaigns in RAM

## Decision: top-k=8 merged results

**Decision**: Retrieve top 5 FTS + top 5 vector, merge to 8 after dedup.

**Rationale**: Fits Ollama context window; improves over MVP1's 4 chunks.

## Decision: Claim bonus +2.0 in rerank

**Decision**: Add 2.0 to score for claim-type results.

**Rationale**: Principle VIII — prefer claims over raw notes.

## Decision: FTS5-only fallback

**Decision**: If embedding model unavailable, skip vector leg; log warning.

**Rationale**: Degraded but functional per FR in spec.

## Decision: Remove format_player_character_context

**Decision**: Delete roster preamble injection; PCs retrieved as entities via hybrid search.

**Rationale**: Single retrieval path; avoids duplicate context.
