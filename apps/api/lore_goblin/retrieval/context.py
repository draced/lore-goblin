from __future__ import annotations

from .hybrid import RetrievedItem


def build_context_blocks(items: list[RetrievedItem]) -> str:
    if not items:
        return ""

    ordered = sorted(
        items,
        key=lambda item: (
            0 if item.result_type == "claim" else 1 if item.result_type == "entity" else 2,
            -item.score,
        ),
    )

    parts: list[str] = []
    for index, item in enumerate(ordered, start=1):
        label = item.source_title or item.entity_name or item.result_type.title()
        lines = [f"[Context {index}] Type: {item.result_type}", f"Source: {label}"]
        if item.canon_status:
            lines.append(f"Canon status: {item.canon_status}")
        if item.entity_type:
            lines.append(f"Entity type: {item.entity_type}")
        lines.append(f"Text: {item.text}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def build_citations(items: list[RetrievedItem]) -> list[dict[str, str | None]]:
    citations: list[dict[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for item in items:
        if item.result_type not in {"claim", "chunk", "source", "entity"}:
            continue
        label = item.source_title or item.entity_name
        if not label:
            continue
        key = (label, item.source_type)
        if key in seen:
            continue
        seen.add(key)
        citation: dict[str, str | None] = {
            "label": label,
            "source_type": item.source_type,
            "claim_quote": item.claim_text if item.result_type == "claim" else None,
        }
        citations.append(citation)
    return citations


def has_disputed_claims(items: list[RetrievedItem]) -> bool:
    return any(item.result_type == "claim" and item.canon_status == "DISPUTED" for item in items)
