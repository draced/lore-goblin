# Discord Bot Testing Guide

This guide walks through testing Lore Goblin's MVP1 Discord commands:

- `/lore campaigns`
- `/lore switch`
- `/lore session`
- `/lore ask`

## Prerequisites

- Docker Desktop is running.
- You have created a Discord application and bot in the Discord Developer Portal.
- The bot has been invited to a test Discord server.
- You have pulled the local Ollama model:

```powershell
docker compose exec ollama ollama pull llama3.1:8b
```

## 1. Configure Environment

From the repo root:

```powershell
cd D:\Projects\repos\lore-goblin
copy .env.example .env
```

Edit `.env` and set:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_test_server_id_here
OLLAMA_CHAT_MODEL=llama3.1:8b
```

`DISCORD_GUILD_ID` is optional, but recommended for testing because slash commands sync faster to one guild than globally.

## 2. Start The App Stack

Start API, web, and Ollama:

```powershell
docker compose up --build
```

Leave this terminal running.

Open the web UI:

```text
http://localhost:5173
```

## 3. Create And Link A Campaign

In the web UI:

1. Create a campaign.
2. Set the campaign tone.
3. In the Discord panel, enter your Discord test server's guild ID.
4. Click **Link guild**.

The Discord bot uses this guild link to decide which campaign `/lore session` and `/lore ask` should use.

## 4. Start The Discord Bot

Open a second terminal:

```powershell
cd D:\Projects\repos\lore-goblin
docker compose --profile bot up --build discord-bot
```

Watch the logs for startup errors. If the token is invalid or missing, the bot container will exit.

## 5. Confirm Slash Commands

In your Discord test server, type:

```text
/lore
```

You should see:

```text
/lore campaigns
/lore switch
/lore session
/lore ask
```

If commands do not appear:

- Confirm `DISCORD_GUILD_ID` is the test server ID.
- Confirm the bot was invited to that server.
- Restart the bot container.
- Wait a minute and refresh Discord with `Ctrl+R`.

## 6. Test Campaign Listing And Switching

Run:

```text
/lore campaigns
```

Expected behavior:

- Lore Goblin lists every campaign created in the web UI.
- The server's linked campaign is marked `(active)`.

Create a second campaign in the web UI, then run:

```text
/lore switch
```

Use the campaign ID from `/lore campaigns`, or the exact campaign name.

Expected result:

```text
Switched this server to `Campaign Name` (`cmp_...`).
```

Run `/lore campaigns` again and confirm the new campaign is marked `(active)`.

## 7. Test Session Ingestion

Run:

```text
/lore session
```

Use values like:

```text
session_date: 2026-06-26
label: First Discord Test
notes: The party met Captain Mira at the ruined mill. She gave them a silver compass and warned them about Lord Vane.
```

Expected result:

```text
Filed notes for `2026-06-26 - First Discord Test` and indexed 1 chunk(s).
```

For long notes, upload a UTF-8 `.txt` file with the `attachment` option instead of pasting everything into `notes`.

## 8. Test Ask

Run:

```text
/lore ask
```

Use:

```text
question: Who gave the party the silver compass?
```

Expected behavior:

- Lore Goblin answers from the submitted session notes.
- The response includes a `Sources:` line.
- The source includes `2026-06-26 - First Discord Test`.

## 9. Test Unknown Answer Behavior

Ask something that is not in the notes:

```text
question: What is the name of the dragon queen?
```

Expected behavior:

- Lore Goblin should say the saved notes do not answer this yet.
- It should not invent campaign canon.

## 10. Useful Debug Commands

Check running containers:

```powershell
docker compose ps
```

Read API logs:

```powershell
docker compose logs api --tail 100
```

Read bot logs:

```powershell
docker compose logs discord-bot --tail 100
```

Check installed Ollama models:

```powershell
docker compose exec ollama ollama list
```

Inspect stored sessions and chunks:

```powershell
docker compose exec api python -c "import sqlite3; con=sqlite3.connect('/data/lore_goblin.sqlite3'); con.row_factory=sqlite3.Row; print([dict(r) for r in con.execute('select session_date,label from sessions')]); print(con.execute('select count(*) from content_chunks').fetchone()[0])"
```

## Common Issues

### Slash commands do not show up

Use `DISCORD_GUILD_ID` during testing and restart the bot. Guild command sync is much faster than global command sync.

### Bot says the guild is not linked

Open the web UI and link the Discord guild ID to the campaign.

### `/lore ask` says no notes answer the question

Confirm `/lore session` successfully indexed chunks. Also try a question with direct terms from the notes, such as an NPC name or item name.

### `/lore ask` times out

The local model may be slow. Confirm Ollama has the model installed and running:

```powershell
docker compose exec ollama ollama list
```

For faster testing, use shorter notes or a smaller model.
