# Implementation Plan: MVP1 Session Notes and Ask

## Architecture

Lore Goblin uses a three-app layout:

- `apps/api`: FastAPI backend, SQLite schema, retrieval, and model orchestration.
- `apps/web`: React and TypeScript setup and chat UI.
- `apps/discord-bot`: Discord slash command client.

The backend is the source of truth. Discord and web clients call HTTP endpoints rather than duplicating campaign logic.

## Data Flow

Session ingestion:

1. Client submits campaign or guild, session date, optional label, author, and raw note content.
2. API resolves the campaign.
3. API creates or reuses the session.
4. API stores the raw note with author provenance.
5. API chunks the note and stores searchable chunks.

Ask:

1. Client submits campaign or guild and question.
2. API retrieves relevant chunks from the campaign.
3. If no chunks match, API returns an uncertainty answer without model generation.
4. If chunks match, API sends the question and source context to Ollama.
5. API returns the answer with unique session citations.

## Initial Retrieval

MVP1 uses lexical chunk scoring. This is intentionally simple so the app can be understood and extended before embeddings are introduced.

## Model Provider

MVP1 uses Ollama's `/api/chat` shape. Campaign-specific model settings are stored in SQLite, with environment defaults.

