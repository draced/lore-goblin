from .ollama import OllamaClient
from .repository import get_campaign, get_model_settings
from .retrieval.context import build_citations, build_context_blocks, has_disputed_claims
from .retrieval.hybrid import hybrid_retrieve


ADMIT_UNKNOWN_ANSWER = (
    "Lore Goblin checks the stacks, squints at the labels, "
    "and finds no saved campaign sources that answer this yet."
)


def answer_question(campaign_id: str, question: str) -> dict:
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise ValueError("Campaign not found")

    items = hybrid_retrieve(campaign_id, question)
    citations = build_citations(items)
    if not items:
        return {
            "answer": ADMIT_UNKNOWN_ANSWER,
            "citations": [],
            "used_model": None,
        }

    settings = get_model_settings(campaign_id)
    client = OllamaClient(settings["base_url"], settings["chat_model"])
    context = build_context_blocks(items)
    disputed_note = ""
    if has_disputed_claims(items):
        disputed_note = (
            "\nSome retrieved claims are marked DISPUTED. "
            "Surface the disagreement without merging them silently."
        )
    system_prompt = f"""
You are Lore Goblin, an in-world notetaking goblin for a tabletop RPG campaign.
Campaign tone: {campaign["tone"]}

Answer only from the provided retrieved campaign context below.
If the context does not answer the question, say you do not know from the campaign sources.
If sources disagree or describe different versions of events, call out the disagreement.
Cite sources inline using the source titles provided in the context blocks.
Do not invent campaign canon.{disputed_note}
""".strip()
    user_prompt = f"""
Question:
{question}

Retrieved campaign context:
{context}
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
