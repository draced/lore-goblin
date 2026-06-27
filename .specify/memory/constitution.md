<!-- SYNC IMPACT REPORT
Version: 1.0.0 → 1.1.0
Ratified: 2026-06-27 | Last Amended: 2026-06-27
Added: Principle VIII (Campaign-Aware Knowledge)
Modified: Principle II — citations include source title/type and claim quote; Principle VI — hybrid retrieval permitted when documented
Technical Constraints: FTS5, sqlite-vec, local embeddings, versioned schema migrations
Templates: plan-template.md ✅ | specify-rules.mdc ✅ | spec-template.md ✅ | tasks-template.md ✅ | README.md ⚠ (reference only)
Follow-ups: implement specs 002–005 per campaign knowledge model series
-->

# Lore Goblin Constitution

## Core Principles

### I. Local-First Campaign Memory

Lore Goblin MUST run locally through Docker Compose with SQLite persistence and an
Ollama-style local model provider. Cloud deployment and API-backed frontier models
are allowed later, but they MUST NOT become required for core use.

### II. Source-Grounded Answers

Lore Goblin MUST answer campaign questions only from saved campaign sources. If no
source supports an answer, the application MUST say it does not know. Answers MUST
cite the source title and type used as evidence, with an optional claim text quote or
session date/label when applicable. When resolved claims exist, answers SHOULD
prefer claims over raw note chunks.

### III. Preserve Player Provenance

Session notes from different players are first-class records. The system MUST
preserve who submitted each note, when it was submitted, and which source it belongs
to. Conflicting accounts MUST NOT be silently merged into a single false canon.

### IV. Discord-First, Web-Setup

The primary player experience is Discord slash commands. The web UI is required for
campaign setup, Discord guild linking, tone configuration, and review workflows.

### V. Playful But Useful

Campaign tone is configurable per campaign via the web UI (see Principle IV). Lore
Goblin is not locked to a single in-world goblin persona. Lore Goblin MUST maintain
the specified **Campaign Tone** for each campaign. Personality MUST NOT override
correctness or source-grounding. Responses MUST remain clear, readable, and honest
about uncertainty regardless of tone.

### VI. Simplicity and YAGNI

Lore Goblin MUST prefer the simplest design that satisfies the spec (SQLite before
Postgres, etc.). The three-app layout (`apps/api`, `apps/web`, `apps/discord-bot`)
MUST be preserved unless Complexity Tracking in plan.md justifies a fourth surface.
New abstraction layers MUST NOT be added without a documented need in plan.md.
Retrieval SHOULD start simple per feature; documented hybrid retrieval (SQLite FTS5
plus local embeddings via sqlite-vec) is permitted when plan.md Complexity Tracking
justifies it for campaign-aware search.

### VII. Test-First Development (NON-NEGOTIABLE)

All implementation MUST follow strict Test-Driven Development. Tests MUST be written
before implementation code for every feature. Tests MUST fail (Red) before
implementation begins (Green). At minimum, API contract or integration tests MUST
cover new HTTP endpoints and critical user journeys.

### VIII. Campaign-Aware Knowledge

Campaign facts MUST trace to a `source` record so the system can answer who, what,
where, when, and how we know. Canonical world objects live in `entity`; atomic
statements live in `claim`. Conflicting claims MUST NOT be silently merged (extends
Principle III). Answers SHOULD prefer resolved claims over raw note chunks when both
exist.

## Technical Constraints

- Frontend: React and TypeScript.
- Backend: Python FastAPI.
- Storage: SQLite with versioned schema migrations for foundational changes.
- Model runtime: Ollama-compatible local chat API.
- Retrieval: simple chunk retrieval for MVP1; hybrid FTS5 plus sqlite-vec permitted
  when documented in plan.md Complexity Tracking.
- Embeddings: local embedding model (Ollama-compatible or dedicated embed endpoint).
- Deployment: local-first Docker Compose.
- Discord UX: slash commands only.

## Development Workflow

Feature work MUST begin with `/speckit-specify` output using the full
`.specify/templates/spec-template.md` format (prioritized user stories P1/P2/…,
Edge Cases, Success Criteria SC-001+).

Plans MUST include a **Constitution Check** gate section (pre- and post-design).

Tasks MUST be organized by user story per `.specify/templates/tasks-template.md`.

Architectural changes to storage, model routing, retrieval, or permissions MUST be
documented in plan.md before implementation.

## Governance

This constitution supersedes ad-hoc conventions. When conflicts arise, the
constitution takes precedence.

Feature work MUST begin from a written spec and acceptance criteria. Architectural
changes that affect storage, model routing, retrieval strategy, or permissions MUST
be captured as project documentation before implementation.

**Amendment procedure**: Document the rationale for change, bump the constitution
version (MAJOR for backward-incompatible principle changes, MINOR for new principles
or material expansions, PATCH for clarifications), update the Sync Impact Report,
and propagate changes to dependent templates.

**Compliance review**: Every plan.md Constitution Check MUST pass or document
justified exceptions in Complexity Tracking. `/speckit-analyze` validates
cross-artifact consistency across spec.md, plan.md, and tasks.md.

**Approval**: Amendments require solo maintainer approval.

**Version**: 1.1.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-06-27
