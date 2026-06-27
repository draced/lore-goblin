# Feature Specification: MVP1 Session Notes and Ask

## User Story

Players submit unorganized full-session notes, then ask Lore Goblin natural-language questions in Discord or the web UI. Lore Goblin answers from saved session notes, cites the relevant session, and admits when the campaign notes do not contain an answer.

## Scope

MVP1 includes:

- Web UI campaign setup.
- Campaign tone configuration.
- Discord guild linking.
- `/lore session` slash command.
- `/lore ask` slash command.
- Web equivalents for submitting a session and asking a question.
- SQLite persistence.
- Immediate chunk indexing of submitted notes.
- Ollama-compatible local model generation.
- Session citations by date and optional label.

MVP1 excludes:

- Owner/admin note rejection.
- Manual wiki approval workflows.
- User authentication in the web UI.
- Cloud model providers.
- Embedding-based vector search.
- Automatic conflict resolution.

## Functional Requirements

1. A user can create a campaign from the web UI.
2. A user can configure a campaign tone/personality from the web UI.
3. A user can link a Discord guild ID to a campaign from the web UI.
4. A Discord user can submit notes with `/lore session`.
5. A web user can submit notes through the web UI.
6. A session is identified by campaign, date stamp, and optional label.
7. Multiple players can submit notes for the same session.
8. Submitted notes are chunked and searchable immediately.
9. A Discord user can ask a question with `/lore ask`.
10. A web user can ask a question through the web UI.
11. Lore Goblin retrieves relevant chunks from the selected campaign only.
12. Lore Goblin includes session citations in answers.
13. Lore Goblin says it does not know when no relevant source is found.
14. Lore Goblin calls out disagreement if retrieved notes conflict.

## Acceptance Criteria

- Given a campaign exists, when a user submits session notes, then the notes are stored with author and session provenance.
- Given a note was submitted, when the user asks a related question, then the answer uses the note as context and cites the session.
- Given no relevant notes exist, when the user asks a question, then the answer says the notes do not contain the answer.
- Given a Discord guild is linked, when `/lore session` is used in that guild, then notes are stored in the linked campaign.
- Given a Discord guild is linked, when `/lore ask` is used in that guild, then the answer is scoped to the linked campaign.

