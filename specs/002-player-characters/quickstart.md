# Quickstart

## Start Local Stack

```bash
cp .env.example .env
docker compose up --build
```

## Try Web Flow

1. Open `http://localhost:5173`.
2. Create or select a campaign.
3. Add a player character with a name and notes.
4. Confirm the character appears in the Player Characters roster.

## Try Discord Flow

Run the bot profile:

```bash
docker compose --profile bot up --build
```

Use:

```text
/lore pc name:Nyra notes:Half-elf ranger searching for the ash crown.
```
