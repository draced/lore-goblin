# Quickstart: Hybrid Retrieval

**Requires**: Specs 002–003 complete; embeddings indexed.

## Rebuild Search Indexes

```bash
curl -X POST http://localhost:8000/admin/reindex-search
```

Expected: FTS and vector indexes populated.

## Ask with Proper Noun (FTS-heavy)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "<id>",
    "question": "Where did the party find the silver key?"
  }'
```

Expected: Answer cites source title; claim quote about ruined chapel.

## Ask with Paraphrase (Vector-heavy)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "<id>",
    "question": "What happened at the broken church?"
  }'
```

Expected: Semantic match to Ruined Chapel content.

## Verify No Roster Preamble

Remove all session notes; keep only PC entities. Ask "Who is in the party?" — answer uses retrieved PC entity context with entity citation, not `[PC roster]` synthetic citation.

## Discord

```text
/lore ask question:Who is Father Aldren?
```

## Run Tests

```bash
cd apps/api && pytest tests/test_hybrid_retrieval.py tests/test_answering_citations.py -v
```
