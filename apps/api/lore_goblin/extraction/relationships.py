from __future__ import annotations

from .claims import claims_to_relationships
from .schemas import ExtractedClaim


def extract_relationships(claims: list[ExtractedClaim]) -> list[dict]:
    return claims_to_relationships(claims)
