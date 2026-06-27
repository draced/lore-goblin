# Quickstart: Knowledge Extraction Pipeline

**Requires**: Spec 002 complete; Ollama running with chat + embedding models.

## Pull Models

```bash
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull nomic-embed-text
```

## Submit Source and Watch Extraction

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "<id>",
    "session_date": "2026-06-27",
    "label": "Chapel",
    "raw_content": "The party found a silver key in the ruined chapel. Father Aldren warned them about the reliquary.",
    "author_display_name": "Player One"
  }'
```

Check job status:

```bash
curl http://localhost:8000/sources/<source_id>/extraction-status
```

Expected: `pending` → `running` → `complete`.

## Verify Extracted Knowledge

```bash
curl http://localhost:8000/campaigns/<id>/entities
curl http://localhost:8000/campaigns/<id>/claims
```

Expected entities: Silver Key (ITEM), Ruined Chapel (LOCATION), Father Aldren (NPC), Party (PC or group).

## Entity Resolution Test

Pre-create entity:

```bash
curl -X POST http://localhost:8000/campaigns/<id>/entities \
  -H "Content-Type: application/json" \
  -d '{"entity_type":"NPC","name":"Father Aldren","aliases":["Aldren"],"summary":"Chapel priest"}'
```

Submit note mentioning "Aldren" only. Verify no duplicate NPC created; alias preserved.

## Run Tests

```bash
cd apps/api && pytest tests/test_entity_resolution.py tests/test_pipeline.py -v
```
