# Architecture Decision Record: Email Threads API

**ADR Number:** ADR-2026-0014  
**Title:** Email Threads API - Multi-Provider Conversational Email Units  
**Date:** 2026-09-09  
**Status:** Accepted  
**Bounty Reference:** https://github.com/bhos/warpspeed/issues/BHOS-WARPSPEED-4  
**Bounty Amount:** $750 (PAID BOUNTY)  
**Owner:** AF-via-OMX  

---

## Context

The platform currently exposes email functionality through provider-specific endpoints that return individual messages without thread awareness. As multi-provider email integration expands (Gmail, Outlook, IMAP), users need a unified view of email conversations that transcends provider boundaries while maintaining strict data isolation.

The existing email API returns messages in isolation without thread grouping semantics, leading to:
- Duplicate conversation views when users access emails through different provider integrations
- Inconsistent thread membership across providers
- Missing thread-level access control enforcement
- No standardized way to search across threads

We need to design an Email Threads API that provides conversational email units across all integrated providers.

---

## Decision

We will implement the Email Threads API with the following design:

### 1. API Endpoints

#### GET /v2/threads
Returns paginated list of email threads for the authenticated user.

**Request Parameters:**
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 20, max: 100): Items per page
- `provider` (string, optional): Filter by provider (gmail, outlook, imap)
- `folder` (string, optional): Filter by folder (inbox, sent, trash, spam)
- `has_attachment` (boolean, optional): Filter threads with attachments
- `from_date` (ISO8601, optional): Start date filter
- `to_date` (ISO8601, optional): End date filter
- `sort` (string, default: "desc"): Sort order (asc, desc)
- `sort_by` (string, default: "last_message_date"): Sort field

**Response:**
```json
{
  "data": [
    {
      "id": "thread_gm_a1b2c3d4e5f6",
      "subject": "Q4 Planning Discussion",
      "snippet": "Let's schedule a meeting to discuss the roadmap priorities...",
      "message_count": 5,
      "unread_count": 2,
      "has_attachments": true,
      "last_message_date": "2026-09-08T14:30:00Z",
      "first_message_date": "2026-09-01T09:15:00Z",
      "participants": [
        {"email": "alice@example.com", "name": "Alice Smith"},
        {"email": "bob@example.com", "name": "Bob Johnson"}
      ],
      "providers": ["gmail", "outlook"],
      "folders": ["inbox"],
      "labels": ["important", "work"],
      "is_read": false,
      "is_starred": false
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_count": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

#### GET /v2/threads/:id
Returns detailed thread information with all messages.

**Path Parameters:**
- `id` (string, required): Thread identifier

**Response:**
```json
{
  "data": {
    "id": "thread_gm_a1b2c3d4e5f6",
    "subject": "Q4 Planning Discussion",
    "messages": [
      {
        "id": "msg_gm_abc123",
        "provider": "gmail",
        "message_id": "<CAHB4xyz@mail.gmail.com>",
        "from":