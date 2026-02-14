from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional

from .models import Entity, EntityCreate


@dataclass
class InMemoryStore:
    _lock: Lock = field(default_factory=Lock)
    _next_id: int = 1
    _entities: Dict[int, Entity] = field(default_factory=dict)

    def list_entities(self) -> List[Entity]:
        # intentionally simple (no pagination/sorting guarantees yet)
        with self._lock:
            return list(self._entities.values())

    def get_entity(self, entity_id: int) -> Optional[Entity]:
        with self._lock:
            return self._entities.get(entity_id)

    def create_entity(self, data: EntityCreate) -> Entity:
        with self._lock:
            entity = Entity(id=self._next_id, name=data.name, payload=data.payload)
            self._entities[self._next_id] = entity
            self._next_id += 1
            return entity

    def delete_entity(self, entity_id: int) -> bool:
        with self._lock:
            return self._entities.pop(entity_id, None) is not None
