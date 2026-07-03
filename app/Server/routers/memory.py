"""Memory management routes. See context/spec/api/memory.md."""
from fastapi import APIRouter, Depends, HTTPException, status

import schemas
from deps import current_user, storage
from storage.base import StorageBackend

router = APIRouter(prefix="/api/memory", tags=["memory"])


def _memory_out(mem: dict) -> schemas.MemoryOut:
    return schemas.MemoryOut(
        summary=mem.get("summary"),
        summary_updated_at=mem.get("summary_updated_at"),
        facts=mem.get("facts", []),
    )


@router.get("", response_model=schemas.MemoryOut)
async def get_memory(user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    return _memory_out(await store.get_memory(user["id"]))


@router.put("/summary", response_model=schemas.MemoryOut)
async def set_summary(body: schemas.SetSummaryRequest, user: dict = Depends(current_user),
                      store: StorageBackend = Depends(storage)):
    await store.set_summary(user["id"], body.summary)
    return _memory_out(await store.get_memory(user["id"]))


@router.post("/facts", response_model=schemas.FactOut, status_code=status.HTTP_201_CREATED)
async def add_fact(body: schemas.AddFactRequest, user: dict = Depends(current_user),
                   store: StorageBackend = Depends(storage)):
    return await store.add_fact(user["id"], body.text)


@router.delete("/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact(fact_id: int, user: dict = Depends(current_user),
                      store: StorageBackend = Depends(storage)):
    if not await store.delete_fact(user["id"], fact_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="fact_not_found")


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def wipe_memory(user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    await store.wipe_memory(user["id"])
