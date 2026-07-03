"""Vocabulary & flashcard routes. See context/spec/api/vocabulary.md."""
import random

from fastapi import APIRouter, Depends, HTTPException, Query, status

import schemas
from deps import current_user, storage
from services import vocabulary_service
from storage.base import StorageBackend

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])


# ---- groups ----
@router.get("/groups", response_model=schemas.GroupList)
async def list_groups(user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    groups = await store.list_groups(user["id"])
    return schemas.GroupList(items=groups, total=len(groups))


@router.post("/groups", response_model=schemas.GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(body: schemas.CreateGroupRequest, user: dict = Depends(current_user),
                       store: StorageBackend = Depends(storage)):
    if await store.get_group_by_name(user["id"], body.name):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="group_name_taken")
    return await store.create_group(user["id"], body.name)


@router.patch("/groups/{group_id}", response_model=schemas.GroupOut)
async def update_group(group_id: int, body: schemas.UpdateGroupRequest,
                       user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    group = await store.get_group(user["id"], group_id)
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="group_not_found")
    existing = await store.get_group_by_name(user["id"], body.name)
    if existing and existing["id"] != group_id:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="group_name_taken")
    return await store.update_group(user["id"], group_id, body.name)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, user: dict = Depends(current_user),
                       store: StorageBackend = Depends(storage)):
    group = await store.get_group(user["id"], group_id)
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="group_not_found")
    if group["is_default"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cannot_delete_default")
    # Move words to default group, never orphan.
    default = await store.get_default_group(user["id"])
    await store.move_words_to_group(user["id"], group_id, default["id"])
    await store.delete_group(user["id"], group_id)


# ---- words ----
@router.get("/words", response_model=schemas.WordList)
async def list_words(group_id: int | None = None, limit: int = Query(50, le=200), offset: int = 0,
                     user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    items, total = await store.list_words(user["id"], group_id, limit, offset)
    return schemas.WordList(items=items, total=total)


@router.post("/words", response_model=schemas.WordOut, status_code=status.HTTP_201_CREATED)
async def create_word(body: schemas.CreateWordRequest, user: dict = Depends(current_user),
                      store: StorageBackend = Depends(storage)):
    word = await vocabulary_service.add_word(
        store, user, term=body.term, translation=body.translation, group_id=body.group_id,
    )
    return word


@router.patch("/words/{word_id}", response_model=schemas.WordOut)
async def update_word(word_id: int, body: schemas.UpdateWordRequest,
                      user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    word = await store.get_word(user["id"], word_id)
    if word is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="word_not_found")
    if body.group_id is not None and await store.get_group(user["id"], body.group_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="group_not_found")
    return await store.update_word(user["id"], word_id, term=body.term,
                                   translation=body.translation, group_id=body.group_id)


@router.delete("/words/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word(word_id: int, user: dict = Depends(current_user),
                      store: StorageBackend = Depends(storage)):
    if not await store.delete_word(user["id"], word_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="word_not_found")


# ---- review / flashcards ----
@router.get("/groups/{group_id}/review", response_model=schemas.ReviewOut)
async def review_group(group_id: int, user: dict = Depends(current_user),
                       store: StorageBackend = Depends(storage)):
    group = await store.get_group(user["id"], group_id)
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="group_not_found")
    words, _ = await store.list_words(user["id"], group_id, limit=200, offset=0)
    random.shuffle(words)
    cards = [schemas.Flashcard(id=w["id"], front=w["translation"], back=w["term"]) for w in words]
    return schemas.ReviewOut(group=group, cards=cards)
