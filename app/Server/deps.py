"""Shared FastAPI dependencies: auth + storage."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from security import decode_access_token
from storage import get_storage
from storage.base import StorageBackend

_bearer = HTTPBearer(auto_error=False)


def storage() -> StorageBackend:
    return get_storage()


async def current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    store: StorageBackend = Depends(storage),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    user = await store.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    return user
