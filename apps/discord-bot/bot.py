import json
import os
from urllib import request

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("LORE_GOBLIN_API_URL", "http://localhost:8000").rstrip("/")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{API_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str) -> dict | list:
    req = request.Request(f"{API_URL}{path}", method="GET")
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def format_campaign_line(campaign: dict, active_campaign_id: str | None = None) -> str:
    marker = " (active)" if campaign["id"] == active_campaign_id else ""
    return f"- `{campaign['id']}` - {campaign['name']}{marker}"


def format_campaign_list(campaigns: list[dict], active_campaign_id: str | None = None) -> str:
    lines = ["Available campaigns:"]
    for index, campaign in enumerate(campaigns):
        line = format_campaign_line(campaign, active_campaign_id)
        remaining_count = len(campaigns) - index
        if len("\n".join([*lines, line, f"...and {remaining_count} more."])) > 1900:
            lines.append(f"...and {remaining_count} more.")
            break
        lines.append(line)
    return "\n".join(lines)


def resolve_campaign(campaigns: list[dict], campaign: str) -> tuple[dict | None, str | None]:
    normalized = campaign.strip().casefold()
    if not normalized:
        return None, "Give Lore Goblin a campaign ID or exact campaign name."

    for candidate in campaigns:
        if candidate["id"].casefold() == normalized:
            return candidate, None

    matches = [candidate for candidate in campaigns if candidate["name"].casefold() == normalized]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        ids = ", ".join(f"`{candidate['id']}`" for candidate in matches)
        return None, f"More than one campaign is named `{campaign}`. Use one of these IDs: {ids}"
    return None, f"Lore Goblin cannot find a campaign named or identified by `{campaign}`."


class LoreGoblinClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=int(DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


client = LoreGoblinClient()
lore = app_commands.Group(name="lore", description="Ask and feed the campaign's notetaking goblin.")


@lore.command(name="session", description="Submit a full session note dump.")
@app_commands.describe(
    session_date="Session date in YYYY-MM-DD format.",
    notes="Messy session notes. Paste the useful pile, or upload a text attachment.",
    label="Optional session label.",
    attachment="Optional text file for longer notes.",
)
async def lore_session(
    interaction: discord.Interaction,
    session_date: str,
    notes: str | None = None,
    label: str | None = None,
    attachment: discord.Attachment | None = None,
) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    if not interaction.guild_id:
        await interaction.followup.send("Lore Goblin needs a server-linked campaign before filing notes.")
        return
    note_content = notes or ""
    if attachment:
        try:
            note_content = (await attachment.read()).decode("utf-8")
        except UnicodeDecodeError:
            await interaction.followup.send("Lore Goblin can only read UTF-8 text attachments for MVP1.")
            return
    if not note_content.strip():
        await interaction.followup.send("Give Lore Goblin notes to file, either as text or a text attachment.")
        return
    try:
        result = post_json(
            "/sessions",
            {
                "guild_id": str(interaction.guild_id),
                "session_date": session_date,
                "label": label,
                "raw_content": note_content,
                "author_display_name": interaction.user.display_name,
                "discord_user_id": str(interaction.user.id),
            },
        )
    except Exception as exc:
        await interaction.followup.send(f"Lore Goblin dropped the inkpot: `{exc}`")
        return

    session = result["session"]
    label_text = f" - {session['label']}" if session.get("label") else ""
    await interaction.followup.send(
        f"Filed notes for `{session['session_date']}{label_text}` and indexed {result['chunk_count']} chunk(s)."
    )


@lore.command(name="ask", description="Ask Lore Goblin a campaign question.")
@app_commands.describe(question="Question to answer from saved session notes.")
async def lore_ask(interaction: discord.Interaction, question: str) -> None:
    await interaction.response.defer(thinking=True)
    if not interaction.guild_id:
        await interaction.followup.send("Lore Goblin needs a server-linked campaign before answering.")
        return
    try:
        result = post_json(
            "/ask",
            {
                "guild_id": str(interaction.guild_id),
                "question": question,
            },
        )
    except Exception as exc:
        await interaction.followup.send(f"Lore Goblin cannot reach the stacks: `{exc}`")
        return

    citations = result.get("citations", [])
    citation_text = ""
    if citations:
        labels = ", ".join(f"`{citation['label']}`" for citation in citations)
        citation_text = f"\n\nSources: {labels}"
    await interaction.followup.send(f"{result['answer']}{citation_text}")


@lore.command(name="campaigns", description="List the available campaigns.")
async def lore_campaigns(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    active_campaign_id = None
    try:
        campaigns = get_json("/campaigns")
        if interaction.guild_id:
            active_campaign = get_json(f"/discord/guilds/{interaction.guild_id}/campaign")
            active_campaign_id = active_campaign.get("id") if active_campaign else None
    except Exception as exc:
        await interaction.followup.send(f"Lore Goblin cannot read the campaign shelf: `{exc}`")
        return

    if not campaigns:
        await interaction.followup.send("No campaigns exist yet. Create one in the web UI first.")
        return

    await interaction.followup.send(format_campaign_list(campaigns, active_campaign_id))


@lore.command(name="switch", description="Switch this server to another campaign.")
@app_commands.describe(campaign="Campaign ID or exact campaign name from /lore campaigns.")
async def lore_switch(interaction: discord.Interaction, campaign: str) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    if not interaction.guild_id:
        await interaction.followup.send("Lore Goblin can only switch campaigns inside a Discord server.")
        return

    try:
        campaigns = get_json("/campaigns")
        selected_campaign, error = resolve_campaign(campaigns, campaign)
        if error:
            await interaction.followup.send(error)
            return
        post_json(
            "/discord/guild-links",
            {
                "campaign_id": selected_campaign["id"],
                "guild_id": str(interaction.guild_id),
            },
        )
    except Exception as exc:
        await interaction.followup.send(f"Lore Goblin fumbled the campaign map: `{exc}`")
        return

    await interaction.followup.send(
        f"Switched this server to `{selected_campaign['name']}` (`{selected_campaign['id']}`)."
    )


client.tree.add_command(lore)


if not DISCORD_BOT_TOKEN:
    raise SystemExit("DISCORD_BOT_TOKEN is required to run the Lore Goblin Discord bot.")

client.run(DISCORD_BOT_TOKEN)
