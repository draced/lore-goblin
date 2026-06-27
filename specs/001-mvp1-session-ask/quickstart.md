# Quickstart

## Start Local Stack

```bash
cp .env.example .env
docker compose up --build
```

## Pull A Local Model

```bash
docker compose exec ollama ollama pull llama3.1:8b
```

## Configure

1. Open `http://localhost:5173`.
2. Create a campaign.
3. Set the campaign tone.
4. Link a Discord guild ID.

## Try Web Flow

1. Submit a session note from the web UI.
2. Ask a question related to the note.
3. Confirm the answer cites the session.

## Try Discord Flow

Run the bot profile:

```bash
docker compose --profile bot up --build
```

Use:

```text
/lore session
/lore ask
```

