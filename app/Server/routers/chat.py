"""AI chat routes. See context/spec/api/chat.md."""
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

import schemas
from deps import current_user, storage
from services import chat_service, memory_service
from storage.base import StorageBackend

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/messages", response_model=schemas.MessageList)
async def list_messages(limit: int = Query(50, le=200), offset: int = 0,
                        user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    items, total = await store.list_messages(user["id"], limit, offset)
    return schemas.MessageList(items=items, total=total)


@router.post("/messages", response_model=schemas.SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(body: schemas.SendMessageRequest, background: BackgroundTasks,
                       user: dict = Depends(current_user), store: StorageBackend = Depends(storage)):
    user_id = user["id"]
    # 1. persist user message
    await store.add_message(user_id, role="user", content=body.content)
    # 2. assemble prompt from memory tiers
    preamble, recent = await memory_service.build_context_blocks(store, user_id)
    # 3. generate reply (may invoke tools)
    text, actions = await chat_service.generate_reply(store, user, preamble, recent)
    # 4. persist + return assistant message
    assistant = await store.add_message(user_id, role="assistant", content=text)
    # 5. async post-turn memory update
    background.add_task(memory_service.update_memory_after_turn, store, user_id)
    return schemas.SendMessageResponse(
        message=assistant,
        actions=[schemas.ChatAction(**a) for a in actions],
    )


@router.delete("/messages", status_code=status.HTTP_204_NO_CONTENT)
async def clear_messages(reset_memory: bool = False, user: dict = Depends(current_user),
                         store: StorageBackend = Depends(storage)):
    await store.clear_messages(user["id"])
    if reset_memory:
        await store.wipe_memory(user["id"])
