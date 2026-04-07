from pydantic import BaseModel
from typing import List, Dict, Optional

class LedgerEntry(BaseModel):
    name: str
    quantity: int
    unit: str
    location: str
    last_updated: str  # ISO format

class PendingHook(BaseModel):
    id: str
    description: str
    chapter_introduced: int
    status: str  # active, resolved, abandoned
    priority: str  # low, medium, high

class CurrentState(BaseModel):
    world_state: str
    character_positions: Dict[str, str]
    relationships: Dict[str, List[str]]
    known_information: List[str]
    emotional_arcs: Dict[str, str]

class ParticleLedger(BaseModel):
    entries: List[LedgerEntry]

class PendingHooks(BaseModel):
    hooks: List[PendingHook]
