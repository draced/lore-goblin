# Supersedes: 002-player-characters

**Date**: 2026-06-27

## Prior scope

Feature `002-player-characters` delivered a campaign-scoped player character roster:

- `player_characters` SQLite table
- Web UI roster add/list
- Discord `/lore pc` slash command
- Roster injected as unstructured prompt context during `/ask`

That implementation is **complete** but is being **superseded** by the campaign-aware knowledge model in `002-campaign-knowledge-model`.

## Migration intent

| Legacy | New model |
|--------|-----------|
| `session_notes` | `source` (`SESSION_NOTE`) |
| `player_characters` | `entity` (`PC`) + `source` (`PLAYER_CHARACTER_DESC`) |
| `content_chunks` | Retained with `source_id` FK |

Player character UX (web + Discord) is preserved; internal storage moves to `entity` + `source`.

## Related specs

- `003-knowledge-extraction-pipeline` — Ollama extraction, entity resolution, claims
- `004-hybrid-retrieval` — FTS5 + sqlite-vec, claim-preferring answers
- `005-knowledge-review` — deferred human review workflow
