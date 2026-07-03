"""Auth & user routes. See context/spec/api/auth.md."""
from fastapi import APIRouter, Depends, HTTPException, status

import schemas
from deps import current_user, storage
from security import create_access_token, hash_password, verify_password
from storage.base import StorageBackend

router = APIRouter(prefix="/api", tags=["auth"])


def _user_out(user: dict) -> schemas.UserOut:
    return schemas.UserOut(
        id=user["id"], email=user["email"], display_name=user["display_name"],
        learning_language=user["learning_language"], created_at=user["created_at"],
    )


@router.post("/auth/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: schemas.RegisterRequest, store: StorageBackend = Depends(storage)):
    if await store.get_user_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_taken")
    user = await store.create_user(
        email=body.email, password_hash=hash_password(body.password),
        display_name=body.display_name, learning_language=body.learning_language,
    )
    # Provision default vocabulary group.
    await store.create_group(user["id"], name="Group 1", is_default=True)
    token = create_access_token(user["id"])
    return schemas.AuthResponse(user=_user_out(user), access_token=token)


@router.post("/auth/login", response_model=schemas.AuthResponse)
async def login(body: schemas.LoginRequest, store: StorageBackend = Depends(storage)):
    user = await store.get_user_by_email(body.email)
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    token = create_access_token(user["id"])
    return schemas.AuthResponse(user=_user_out(user), access_token=token)


@router.get("/users/me", response_model=schemas.UserOut)
async def get_me(user: dict = Depends(current_user)):
    return _user_out(user)


@router.patch("/users/me", response_model=schemas.UserOut)
async def update_me(body: schemas.UpdateUserRequest, user: dict = Depends(current_user),
                    store: StorageBackend = Depends(storage)):
    updated = await store.update_user(
        user["id"], display_name=body.display_name, learning_language=body.learning_language,
    )
    return _user_out(updated)
