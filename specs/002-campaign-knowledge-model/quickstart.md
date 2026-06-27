# Quickstart: Campaign Knowledge Model

## Prerequisites

- Docker Compose stack from MVP1
- Existing database optional (migration validates both fresh and legacy DBs)

## Start Local Stack

```bash
cp .env.example .env
docker compose up --build
```

## Validate Migration (legacy database)

```bash
curl -X POST http://localhost:8000/admin/migrate \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```

Expected: JSON report with counts, empty `errors`.

```bash
curl -X POST http://localhost:8000/admin/migrate \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```

Re-run dry-run; expected: zero new records.

## Validate Unified Sources

Submit a session note (web or API):

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "<id>",
    "session_date": "2026-06-27",
    "label": "Chapel",
    "raw_content": "The party found a silver key in the ruined chapel.",
    "author_display_name": "Player One"
  }'
```

List sources:

```bash
curl http://localhost:8000/campaigns/<id>/sources?source_type=SESSION_NOTE
```

Expected: new source with matching body and `SESSION_NOTE` type.

## Validate PC Roster (unchanged UX)

Web: `http://localhost:5173` → add PC → confirm roster display.

Discord (with bot profile):

```text
/lore pc name:Nyra notes:Half-elf ranger searching for the ash crown.
```

List entities:

```bash
curl http://localhost:8000/campaigns/<id>/entities?entity_type=PC
```

Expected: PC entity with matching name and summary.

## Regression

- `/lore session` and `/lore ask` still function (retrieval unchanged until spec 004)
- `GET /campaigns/{id}/player-characters` returns same shape as before migration

## Run Tests

```bash
cd apps/api && pytest tests/test_migrations.py tests/test_sources.py tests/test_entities.py tests/test_player_characters_compat.py -v
```

All tests should pass after implementation.
