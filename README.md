# Lore Goblin

Lore Goblin is a local-first TTRPG campaign memory bot. MVP1 focuses on Discord slash commands for campaign memory:

- `/lore campaigns`: list available campaigns.
- `/lore switch`: switch the current Discord server to another campaign.
- `/lore session`: submit a full session note dump.
- `/lore ask`: ask a source-grounded campaign question.

The app also includes a React setup UI, a FastAPI backend, SQLite storage, simple chunk retrieval, and an Ollama-style local model adapter.

## MVP1 Principles

- Players can submit messy full-session notes immediately.
- All submitted notes are searchable right away.
- Answers cite the session date and optional label used as source material.
- Lore Goblin answers only from saved campaign information.
- Conflicting player notes are preserved as provenance instead of overwritten.
- Web UI is required for campaign setup.

## Repository Layout

```text
apps/
  api/          FastAPI backend, SQLite schema, retrieval, Ollama adapter
  discord-bot/ Discord slash command client
  web/          React + TypeScript setup and chat UI
specs/
  001-mvp1-session-ask/
```

## Local Development

Copy `.env.example` to `.env`, add a Discord token if you want to run the bot, then start the stack:

```bash
docker compose up --build
```

Open the web UI at `http://localhost:5173`.

The API is available at `http://localhost:8000`.

## Notes

The Docker Compose file includes Ollama, but model downloads are intentionally manual. Pull a model before asking questions:

```bash
docker compose exec ollama ollama pull llama3.1:8b
```

For Discord setup and verification, see [docs/discord-testing.md](docs/discord-testing.md).

## Spec-Driven Development

New features follow the [Lore Goblin constitution](.specify/memory/constitution.md) and spec-kit workflow. Each feature lives under `specs/###-feature-name/` with `spec.md`, `plan.md`, and `tasks.md` artifacts produced by `/speckit-specify`, `/speckit-plan`, and `/speckit-tasks`.
