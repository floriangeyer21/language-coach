"""SQLAlchemy Core table definitions for the MySQL backend.

See context/spec/data/mysql.md. Shared MetaData; no ORM.
"""
from sqlalchemy import (
    BigInteger, Boolean, Column, ForeignKey, Index, MetaData,
    String, Table, Text, UniqueConstraint,
)
from sqlalchemy.dialects.mysql import DATETIME

metadata = MetaData()


def DateTime(fsp: int = 6):
    """Microsecond-precision DATETIME (MySQL DATETIME(6))."""
    return DATETIME(fsp=fsp)

users = Table(
    "users", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("display_name", String(255), nullable=False),
    Column("learning_language", String(100), nullable=False),
    Column("created_at", DateTime(fsp=6), nullable=False),
    mysql_charset="utf8mb4",
)

messages = Table(
    "messages", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(16), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime(fsp=6), nullable=False),
    Index("ix_messages_user_id", "user_id", "id"),
    mysql_charset="utf8mb4",
)

memory = Table(
    "memory", metadata,
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("summary", Text, nullable=True),
    Column("summary_updated_at", DateTime(fsp=6), nullable=True),
    mysql_charset="utf8mb4",
)

facts = Table(
    "facts", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("text", Text, nullable=False),
    Column("created_at", DateTime(fsp=6), nullable=False),
    Index("ix_facts_user_id", "user_id"),
    mysql_charset="utf8mb4",
)

vocab_groups = Table(
    "vocab_groups", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("is_default", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(fsp=6), nullable=False),
    UniqueConstraint("user_id", "name", name="uq_group_user_name"),
    Index("ix_groups_user_id", "user_id"),
    mysql_charset="utf8mb4",
)

words = Table(
    "words", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("group_id", BigInteger, ForeignKey("vocab_groups.id"), nullable=False),
    Column("term", String(512), nullable=False),
    Column("translation", String(512), nullable=False),
    Column("created_at", DateTime(fsp=6), nullable=False),
    Index("ix_words_user_id", "user_id"),
    Index("ix_words_group_id", "group_id"),
    mysql_charset="utf8mb4",
)
