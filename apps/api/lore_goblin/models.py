from enum import StrEnum


class SourceType(StrEnum):
    SESSION_NOTE = "SESSION_NOTE"
    PLAYER_CHARACTER_DESC = "PLAYER_CHARACTER_DESC"
    ITEM_DESC = "ITEM_DESC"
    NPC_DESC = "NPC_DESC"
    LOCATION_DESC = "LOCATION_DESC"
    MANUAL_EDIT = "MANUAL_EDIT"


class EntityType(StrEnum):
    PC = "PC"
    NPC = "NPC"
    LOCATION = "LOCATION"
    FACTION = "FACTION"
    ITEM = "ITEM"
    QUEST = "QUEST"
    EVENT = "EVENT"
    DEITY = "DEITY"
    MONSTER = "MONSTER"
    ORGANIZATION = "ORGANIZATION"
    RUMOR = "RUMOR"


SOURCE_TYPES = frozenset(SourceType)
ENTITY_TYPES = frozenset(EntityType)
