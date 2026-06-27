# Lore Goblin Constitution

## Core Principles

### I. Local-First Campaign Memory

Lore Goblin must run locally through Docker Compose with SQLite persistence and an Ollama-style local model provider. Cloud deployment and API-backed frontier models are allowed later, but they must not become required for core use.

### II. Source-Grounded Answers

Lore Goblin must answer campaign questions only from saved campaign sources. If no source supports an answer, the application must say it does not know. Answers must cite the session date and optional session label used as evidence.

### III. Preserve Player Provenance

Session notes from different players are first-class records. The system must preserve who submitted each note, when it was submitted, and which session it belongs to. Conflicting accounts are not silently merged into a single false canon.

### IV. Discord-First, Web-Setup

The primary player experience is Discord slash commands. The web UI is required for campaign setup, Discord guild linking, tone configuration, and review workflows.

### V. Playful But Useful

Lore Goblin should feel like an in-world notetaking goblin, while remaining clear, readable, and honest about uncertainty. Personality must never override correctness or source-grounding.

## Technical Constraints

- Frontend: React and TypeScript.
- Backend: Python FastAPI.
- Storage: SQLite for MVP1.
- Model runtime: Ollama-compatible local chat API.
- Retrieval: simple chunk retrieval first.
- Deployment: local-first Docker Compose.
- Discord UX: slash commands only.

## Governance

Feature work must begin from a written spec and acceptance criteria. Architectural changes that affect storage, model routing, retrieval strategy, or permissions should be captured as project documentation before implementation.

