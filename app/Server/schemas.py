"""Pydantic request/response models. Mirrors context/spec/api/*."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---- auth / users ----
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str = Field(min_length=1)
    learning_language: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    learning_language: str
    created_at: str


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    token_type: str = "bearer"


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    learning_language: Optional[str] = None


# ---- chat ----
class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ChatAction(BaseModel):
    type: str
    word_id: Optional[int] = None
    term: Optional[str] = None
    group_id: Optional[int] = None


class SendMessageResponse(BaseModel):
    message: MessageOut
    actions: list[ChatAction] = []


class MessageList(BaseModel):
    items: list[MessageOut]
    total: int


# ---- memory ----
class FactOut(BaseModel):
    id: int
    text: str
    created_at: str


class MemoryOut(BaseModel):
    summary: Optional[str]
    summary_updated_at: Optional[str]
    facts: list[FactOut]


class SetSummaryRequest(BaseModel):
    summary: str


class AddFactRequest(BaseModel):
    text: str = Field(min_length=1)


# ---- vocabulary ----
class GroupOut(BaseModel):
    id: int
    name: str
    is_default: bool
    word_count: int = 0
    created_at: str


class GroupList(BaseModel):
    items: list[GroupOut]
    total: int


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1)


class UpdateGroupRequest(BaseModel):
    name: str = Field(min_length=1)


class WordOut(BaseModel):
    id: int
    term: str
    translation: str
    group_id: int
    created_at: str


class WordList(BaseModel):
    items: list[WordOut]
    total: int


class CreateWordRequest(BaseModel):
    term: str = Field(min_length=1)
    translation: Optional[str] = None
    group_id: Optional[int] = None


class UpdateWordRequest(BaseModel):
    term: Optional[str] = None
    translation: Optional[str] = None
    group_id: Optional[int] = None


class Flashcard(BaseModel):
    id: int
    front: str
    back: str


class ReviewOut(BaseModel):
    group: GroupOut
    cards: list[Flashcard]
