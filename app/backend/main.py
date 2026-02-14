from __future__ import annotations

import secrets
from typing import List

from fastapi import FastAPI, HTTPException, Response, status

from .models import Entity, EntityCreate, LoginRequest, LoginResponse
from .store import InMemoryStore

app = FastAPI(title="AI-Assisted CI Triage PoC Backend", version="0.1.0")

store = InMemoryStore()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    # Intentionally minimal / insecure: no real auth, no hashing, no user DB.
    # This is deliberate for later testing/triage scenarios.
    if body.username.strip().lower() == "blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_BLOCKED", "message": "User is blocked"},
        )

    token = secrets.token_urlsafe(24)
    return LoginResponse(access_token=token)


@app.get("/entities", response_model=List[Entity])
def list_entities() -> List[Entity]:
    return store.list_entities()


@app.post("/entities", response_model=Entity, status_code=status.HTTP_201_CREATED)
def create_entity(body: EntityCreate) -> Entity:
    if body.name.strip().lower() == "explode":
        # A controlled "intentional bug" hook for future tests/triage demos.
        # Deterministic trigger, no randomness.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTENTIONAL_BUG", "message": "Intentional failure trigger"},
        )
    return store.create_entity(body)


@app.get("/entities/{entity_id}", response_model=Entity)
def get_entity(entity_id: int) -> Entity:
    entity = store.get_entity(entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Entity not found", "id": entity_id},
        )
    return entity


@app.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(entity_id: int) -> Response:
    ok = store.delete_entity(entity_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Entity not found", "id": entity_id},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
