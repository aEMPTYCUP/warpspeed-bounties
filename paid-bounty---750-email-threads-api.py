import os
import re
import hashlib
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import json
import uuid

from flask import Flask, request, jsonify, g, Response
from flask_cors import CORS
import jwt
from functools import wraps
import sqlite3
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.environ.get('JWT_SECRET', 'warpspeed-secret-key-change-in-production')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'email_threads.db')


class EmailProvider(Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    IMAP = "imap"


class ThreadAccessPolicy(Enum):
    USER_OWNED = "user_owned"
    SHARED = "shared"
    PUBLIC = "public"


class ExcludeFlag(Enum):
    EXCLUDE_DRAFTS = "exclude_drafts"
    EXCLUDE_DELETED = "exclude_deleted"
    EXCLUDE_ARCHIVED = "exclude_archived"


@dataclass
class User:
    id: str
    email: str
    provider: EmailProvider
    access_token: str
    refresh_token: Optional[str] = None
    scopes: List[str] = field(default_factory=list)


@dataclass
class Message:
    id: str
    thread_id: str
    user_id: str
    provider: EmailProvider
    subject: str
    from_address: str
    to_addresses: List[str]
    cc_addresses: List[str] = field(default_factory=list)
    bcc_addresses: List[str] = field(default_factory=list)
    body_text: str = ""
    body_html: str = ""
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    is_read: bool = True
    is_draft: bool = False
    is_deleted: bool = False
    is_archived: bool = False
    labels: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    in_reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'thread_id': self.thread_id,
            'user_id': self.user_id,
            'provider': self.provider.value,
            'subject': self.subject,
            'from': self.from_address,
            'to': self.to_addresses,
            'cc': self.cc_addresses,
            'bcc': self.bcc_addresses,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'is_read': self.is_read,
            'is_draft': self.is_draft,
            'is_deleted': self.is_deleted,
            'is_archived': self.is_archived,
            'labels': self.labels,
            'references': self.references,
            'in_reply_to': self.in_reply_to,
            'attachments': self.attachments,
            'metadata': self.metadata
        }
        return data


@dataclass
class Thread:
    id: str
    user_id: str
    provider: EmailProvider
    subject: str
    message_ids: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    snippet: str = ""
    message_count: int =