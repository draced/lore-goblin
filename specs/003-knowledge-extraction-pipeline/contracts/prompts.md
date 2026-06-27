# Prompt Contracts: Knowledge Extraction Pipeline

Version: v1

## entity_extraction_v1.txt

```
Extract campaign entities from the source.

Return only JSON.

Entity types:
PC, NPC, LOCATION, FACTION, ITEM, QUEST, EVENT, DEITY, MONSTER, ORGANIZATION, UNKNOWN.

For each entity include:
- name
- type
- aliases
- short_description
- importance: major, minor, incidental
- evidence_quote

Source:
{source_text}
```

**Expected response**: JSON array of entity objects.

## entity_resolution_v1.txt

```
Match these extracted entities to existing campaign entities.

Existing entities:
{candidate_entities}

New extracted entities:
{new_entities}

Return JSON array:
- extracted_name
- matched_entity_id (or null)
- confidence (0.0 to 1.0)
- reason
```

## claim_extraction_v1.txt

```
Extract atomic campaign claims from the source.

Rules:
- One claim per fact.
- Preserve uncertainty.
- Do not mark theories as confirmed.
- Do not invent facts.
- Include the source quote.
- Use only known entity ids where possible.

Known entities:
{resolved_entities}

Return JSON array:
[
  {
    "claim_text": "...",
    "subject_entity_name": "...",
    "predicate": "...",
    "object_entity_name": "...",
    "canon_status": "CONFIRMED | RUMOR | THEORY | DISPUTED",
    "importance": "major | minor | incidental",
    "source_quote": "..."
  }
]

Source:
{source_text}
```

## Validation

All responses parsed with Pydantic models in `apps/api/lore_goblin/extraction/schemas.py`. Malformed JSON triggers job retry.
