from .ollama import OllamaClient
from .repository import get_campaign, get_model_settings, list_player_characters
from .retrieval import RetrievedChunk, retrieve_chunks


def build_citations(chunks: list[RetrievedChunk]) -> list[dict[str, str | None]]:
    seen: set[tuple[str, str | None]] = set()
    citations: list[dict[str, str | None]] = []
    for chunk in chunks:
        key = (chunk.session_date, chunk.session_label)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "session_id": chunk.session_id,
                "session_date": chunk.session_date,
                "session_label": chunk.session_label,
                "label": chunk.citation_label,
            }
        )
    return citations


def format_context(chunks: list[RetrievedChunk]) -> str:
    context_parts = []
    for index, chunk in enumerate(chunks, start=1):
        author = chunk.author_display_name or "Unknown player"
        context_parts.append(
            "\n".join(
                [
                    f"[Source {index}] Session: {chunk.citation_label}",
                    f"Submitted by: {author}",
                    f"Text: {chunk.chunk_text}",
                ]
            )
        )
    return "\n\n".join(context_parts)


def format_player_character_context(player_characters: list[dict]) -> str:
    if not player_characters:
        return "No player characters have been recorded for this campaign yet."
    lines = []
    for character in player_characters:
        lines.append(f"- {character['name']}: {character['notes']}")
    return "\n".join(lines)


def answer_question(campaign_id: str, question: str) -> dict:
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise ValueError("Campaign not found")

    player_characters = list_player_characters(campaign_id)
    chunks = retrieve_chunks(campaign_id, question)
    citations = build_citations(chunks)
    if player_characters:
        citations.append({"label": "PC roster"})
    if not chunks and not player_characters:
        return {
            "answer": "Lore Goblin checks the stacks, squints at the labels, and finds no saved session notes that answer this yet.",
            "citations": [],
            "used_model": None,
        }

    settings = get_model_settings(campaign_id)
    client = OllamaClient(settings["base_url"], settings["chat_model"])
    context = format_context(chunks)
    player_character_context = format_player_character_context(player_characters)
    system_prompt = f"""
You are Lore Goblin, an in-world notetaking goblin for a tabletop RPG campaign.
Campaign tone: {campaign["tone"]}

Answer only from the provided campaign sources and player character roster.
If the sources do not answer the question, say you do not know from the notes.
If sources disagree or describe different versions of events, call out the disagreement.
Include citations inline using the session labels provided, like [2026-06-26 - The Ruined Mill].
When using player character roster details, cite them as [PC roster].
Do not invent campaign canon.
""".strip()
    user_prompt = f"""
Question:
{question}

Player character roster:
{player_character_context}

Campaign sources:
{context if context else "No matching session note sources were retrieved."}
""".strip()
    answer = client.chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return {
        "answer": answer,
        "citations": citations,
        "used_model": settings["chat_model"],
    }

