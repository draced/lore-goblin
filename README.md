# Lore Goblin

Lore Goblin is a local-first TTRPG campaign memory bot. Players submit session notes; Lore Goblin extracts entities and claims, indexes them for hybrid retrieval (FTS5 + vector search), and answers questions with source-grounded citations.

**Discord slash commands**

- `/lore campaigns` — list available campaigns
- `/lore switch` — switch the current Discord server to another campaign
- `/lore session` — submit a full session note dump
- `/lore ask` — ask a source-grounded campaign question

The stack also includes a React web UI for campaign setup, a FastAPI backend, SQLite storage, and Ollama for chat and embeddings.

## Repository Layout

```text
apps/
  api/           FastAPI backend, SQLite, hybrid retrieval, extraction pipeline
  discord-bot/   Discord slash command client
  web/           React + TypeScript setup and chat UI
specs/           Feature specs (spec-kit workflow)
```

## Local Development

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Optional: a Discord bot token if you want to run the Discord client (see [docs/discord-testing.md](docs/discord-testing.md))

### 1. Configure environment

Copy the example env file and edit as needed:

```bash
cp .env.example .env
```

Set `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID` only if you plan to run the bot. The API and web UI work without Discord.

### 2. Start the stack

```bash
docker compose up --build
```

This starts:

| Service | URL | Purpose |
|---------|-----|---------|
| Web UI | http://localhost:5173 | Campaign setup, session notes, ask |
| API | http://localhost:8000 | Backend (`GET /health` to verify) |
| Ollama | http://localhost:11434 | Local chat and embedding models |

To include the Discord bot:

```bash
docker compose --profile bot up --build
```

### 3. Pull Ollama models

Model downloads are intentional manual steps so first startup stays fast. **Pull both models** before filing notes or asking questions:

```bash
# Chat model — generates answers for /ask and the web UI
docker compose exec ollama ollama pull llama3.1:8b

# Embedding model — powers vector search and the extraction pipeline
docker compose exec ollama ollama pull nomic-embed-text
```

Override defaults with environment variables (in `.env` or `docker-compose.yml`):

| Variable | Default | Used for |
|----------|---------|----------|
| `OLLAMA_CHAT_MODEL` | `llama3.1:8b` | Answer generation |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Chunk embeddings, semantic search |

Without the chat model, `/ask` returns HTTP 502. Without the embedding model, extraction jobs fail and vector search is skipped (FTS5 lexical search still works as a fallback).

### 4. Use the web UI

1. Open http://localhost:5173
2. Create a campaign and link a Discord guild (optional)
3. File session notes or add player characters
4. Ask a question from the **Ask** panel

After filing notes, the extraction pipeline runs in the background to populate entities, claims, and chunk embeddings. Check API logs if extraction fails — missing `nomic-embed-text` is the most common cause.

### 5. Rebuild search indexes (existing data)

If you upgraded from an older database or indexes look stale, rebuild FTS and vector indexes:

```bash
curl -X POST http://localhost:8000/admin/reindex-search
```

## How Embeddings Fit In

Lore Goblin uses two retrieval legs:

1. **FTS5 (lexical)** — entity names, aliases, claim text, source titles. Works without embeddings.
2. **Vector (semantic)** — sqlite-vec k-NN over chunk embeddings from Ollama. Requires `nomic-embed-text` (or your configured `OLLAMA_EMBED_MODEL`).

Embeddings are created when:

- A session note or player character source is filed and the extraction pipeline runs
- Chunks are embedded via `POST /api/embeddings` on your Ollama instance

Hybrid merge prefers structured **claims** over raw note chunks and cites source titles with optional claim quotes in answers.

## Discord

For bot setup, guild linking, and verification, see [docs/discord-testing.md](docs/discord-testing.md).

## Spec-Driven Development

New features follow the [Lore Goblin constitution](.specify/memory/constitution.md) and spec-kit workflow. Each feature lives under `specs/###-feature-name/` with `spec.md`, `plan.md`, and `tasks.md` artifacts produced by `/speckit-specify`, `/speckit-plan`, and `/speckit-tasks`.
