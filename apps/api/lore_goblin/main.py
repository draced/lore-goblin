from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .answering import answer_question
from .config import Settings, get_settings
from .db import initialize_database
from .repository import (
    add_session_note,
    create_campaign,
    create_player_character,
    get_campaign,
    get_campaign_for_guild,
    link_discord_guild,
    list_campaigns,
    list_player_characters,
    list_sessions,
)


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1)
    tone: str = Field(
        default="A cheerful in-world notetaking goblin who answers with receipts.",
        min_length=1,
    )
    owner_display_name: str = Field(default="Campaign Owner", min_length=1)


class LinkGuildRequest(BaseModel):
    campaign_id: str
    guild_id: str


class AddSessionRequest(BaseModel):
    campaign_id: str | None = None
    guild_id: str | None = None
    session_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    label: str | None = None
    raw_content: str = Field(min_length=1)
    author_display_name: str = Field(min_length=1)
    discord_user_id: str | None = None


class AddPlayerCharacterRequest(BaseModel):
    campaign_id: str | None = None
    guild_id: str | None = None
    name: str = Field(min_length=1)
    notes: str = Field(min_length=1)


class AskRequest(BaseModel):
    campaign_id: str | None = None
    guild_id: str | None = None
    question: str = Field(min_length=1)


def create_app(settings: Settings) -> FastAPI:
    initialize_database()
    app = FastAPI(title="Lore Goblin API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/campaigns")
    def campaigns() -> list[dict]:
        return list_campaigns()

    @app.post("/campaigns", status_code=201)
    def campaign_create(request: CreateCampaignRequest) -> dict:
        return create_campaign(request.name, request.tone, request.owner_display_name)

    @app.post("/discord/guild-links")
    def guild_link(request: LinkGuildRequest) -> dict:
        if not get_campaign(request.campaign_id):
            raise HTTPException(status_code=404, detail="Campaign not found")
        return link_discord_guild(request.campaign_id, request.guild_id)

    @app.get("/discord/guilds/{guild_id}/campaign")
    def guild_campaign(guild_id: str) -> dict | None:
        return get_campaign_for_guild(guild_id)

    @app.get("/campaigns/{campaign_id}/sessions")
    def sessions(campaign_id: str) -> list[dict]:
        return list_sessions(campaign_id)

    @app.get("/campaigns/{campaign_id}/player-characters")
    def player_characters(campaign_id: str) -> list[dict]:
        if not get_campaign(campaign_id):
            raise HTTPException(status_code=404, detail="Campaign not found")
        return list_player_characters(campaign_id)

    @app.post("/player-characters", status_code=201)
    def player_character_create(request: AddPlayerCharacterRequest) -> dict:
        campaign_id = resolve_campaign_id(request.campaign_id, request.guild_id)
        try:
            return create_player_character(campaign_id, request.name, request.notes)
        except ValueError as exc:
            status_code = 404 if str(exc) == "Campaign not found" else 400
            raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    @app.post("/sessions", status_code=201)
    def session_create(request: AddSessionRequest) -> dict:
        campaign_id = resolve_campaign_id(request.campaign_id, request.guild_id)
        return add_session_note(
            campaign_id=campaign_id,
            session_date=request.session_date,
            label=request.label,
            raw_content=request.raw_content,
            author_display_name=request.author_display_name,
            discord_user_id=request.discord_user_id,
        )

    @app.post("/ask")
    def ask(request: AskRequest) -> dict:
        campaign_id = resolve_campaign_id(request.campaign_id, request.guild_id)
        try:
            return answer_question(campaign_id, request.question)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Model request failed: {exc}") from exc

    return app


def resolve_campaign_id(campaign_id: str | None, guild_id: str | None) -> str:
    if campaign_id:
        return campaign_id
    if guild_id:
        campaign = get_campaign_for_guild(guild_id)
        if campaign:
            return campaign["id"]
    raise HTTPException(status_code=400, detail="campaign_id or linked guild_id is required")


app = create_app(get_settings())
