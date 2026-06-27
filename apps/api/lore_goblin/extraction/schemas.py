from typing import Literal

from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    name: str
    type: str
    aliases: list[str] = Field(default_factory=list)
    short_description: str = ""
    importance: Literal["major", "minor", "incidental"] = "minor"
    evidence_quote: str = ""


class ResolutionResult(BaseModel):
    extracted_name: str
    matched_entity_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class ExtractedClaim(BaseModel):
    claim_text: str
    subject_entity_name: str
    predicate: str
    object_entity_name: str | None = None
    canon_status: Literal["CONFIRMED", "RUMOR", "THEORY", "DISPUTED"] = "CONFIRMED"
    importance: Literal["major", "minor", "incidental"] = "minor"
    source_quote: str = ""


class ExtractedRelationship(BaseModel):
    source_entity_name: str
    target_entity_name: str
    relationship_type: str
    description: str = ""
