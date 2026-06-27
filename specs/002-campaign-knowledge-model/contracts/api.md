# API Contracts: Campaign Knowledge Model

## Existing endpoints (behavior preserved)

### GET `/campaigns/{campaign_id}/player-characters`

Returns backward-compatible roster entries.

**Response 200**:
```json
[
  {
    "id": "uuid",
    "campaign_id": "uuid",
    "name": "Nyra",
    "notes": "Half-elf ranger",
    "created_at": "2026-06-27T00:00:00",
    "updated_at": "2026-06-27T00:00:00"
  }
]
```

`id` maps to `entity.id` for PC entities. `notes` maps to `entity.summary`.

### POST `/player-characters`

**Request**:
```json
{
  "campaign_id": "uuid",
  "guild_id": null,
  "name": "Nyra",
  "notes": "Half-elf ranger"
}
```

**Response 201**: Same shape as list item above.

**Errors**: 400 validation, 404 campaign/guild not found.

### POST `/sessions`

Unchanged request/response. Internally also creates `source` row.

## New endpoints

### GET `/campaigns/{campaign_id}/sources`

List sources for campaign, newest first.

**Query params**: `source_type` (optional filter)

**Response 200**:
```json
[
  {
    "id": "uuid",
    "campaign_id": "uuid",
    "source_type": "SESSION_NOTE",
    "title": "Session 8 — Chapel",
    "body": "...",
    "author_user_id": "uuid",
    "session_id": "uuid",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### GET `/campaigns/{campaign_id}/entities`

List entities for campaign.

**Query params**: `entity_type` (optional filter)

**Response 200**:
```json
[
  {
    "id": "uuid",
    "campaign_id": "uuid",
    "entity_type": "PC",
    "name": "Nyra",
    "aliases_json": ["Nyra the Ranger"],
    "summary": "Half-elf ranger",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### POST `/campaigns/{campaign_id}/entities`

**Request**:
```json
{
  "entity_type": "NPC",
  "name": "Father Aldren",
  "aliases": ["Aldren", "Priest Aldren"],
  "summary": "Chapel priest"
}
```

**Response 201**: Entity object.

**Errors**: 400 invalid type or blank name, 404 campaign not found.

## Migration admin

### POST `/admin/migrate`

**Request** (optional):
```json
{ "dry_run": true }
```

**Response 200**:
```json
{
  "dry_run": true,
  "sources_created": 15,
  "entities_created": 5,
  "chunks_linked": 42,
  "errors": []
}
```

Protected: local-only or env-guarded in implementation.
