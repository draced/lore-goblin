# Implementation Plan: Player Characters

## Architecture

Lore Goblin keeps the backend as the source of truth:

- `apps/api`: stores player characters and exposes HTTP endpoints.
- `apps/web`: calls the API to add and list player characters for the selected campaign.
- `apps/discord-bot`: resolves the active campaign through the linked guild and calls the API.

## Data Flow

Web player character creation:

1. User selects a campaign.
2. User submits a player character name and notes.
3. Web UI posts the campaign ID, name, and notes to the API.
4. API validates the campaign and required fields.
5. API stores the player character and returns it.
6. Web UI refreshes the roster.

Discord player character creation:

1. User runs `/lore pc` in a Discord guild.
2. Discord bot sends guild ID, name, and notes to the API.
3. API resolves the linked campaign.
4. API validates required fields.
5. API stores the player character and returns it.
6. Discord bot confirms the character was added.

## Persistence

Player characters are stored in SQLite in a campaign-scoped table. MVP keeps names non-unique so tables can handle rare duplicate names or renamed characters without forcing premature conflict handling.

## Answer Context

The roster is stored as structured campaign data and injected ahead of retrieved session note chunks so Lore Goblin has stable PC context during answers. When roster details are used, Lore Goblin cites them as `[PC roster]`.
