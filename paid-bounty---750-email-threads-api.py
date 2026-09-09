import os
import re
from datetime import datetime
from typing import Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import asyncio

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, field_validator
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from passlib.context import CryptContext

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/email_threads"
)

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID", "")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ============================================================================
# DATABASE SETUP
# ============================================================================

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=20, max_overflow=30)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================

class EmailProvider(str, Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    IMAP = "imap"


class ThreadAccessPolicy(str, Enum):
    OWNER_ONLY = "owner_only"
    SHARED_WITH_ME = "shared_with_me"
    ALL_ACCESSIBLE = "all_accessible"


class MessageDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class ExcludeOption(str, Enum):
    EXCLUDE_DRAFTS = "exclude_drafts"
    EXCLUDE_DELETED = "exclude_deleted"
    EXCLUDE_ARCHIVED = "exclude_archived"
    NONE = "none"


class ThreadStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SPAM = "spam"
    TRASH = "trash"


# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
    thread_participants = relationship("ThreadParticipant", back_populates="user")
    tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class EmailAccount(Base):
    __tablename__ = "email_accounts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True