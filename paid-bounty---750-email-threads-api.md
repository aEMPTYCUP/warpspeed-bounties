# ADR-2024-0847: Email Threads API - Multi-Provider Integration

**Status:** Accepted  
**Date:** 2026-09-09  
**Deciders:**  
- Maria Chen (Engineering Lead - Platform Services)
- James Rodriguez (Principal Backend Engineer)  
- Sarah Kim (Security Architect)
- David Thompson (API Platform Owner)
- Lisa Wang (Quality Assurance Lead)

**Bounty Reference:** https://github.com/platform/email-threads-api/issues/1847  
**Bounty Amount:** $750  
**Pull Request:** https://github.com/platform/email-service/pull/4521  

---

## Context

The platform currently exposes email functionality through provider-specific endpoints (Gmail API, Microsoft Graph API, IMAP connections), requiring clients to manage multiple integrations and manually group messages into conversational threads. This architectural fragmentation creates inconsistent user experiences, duplicate implementation logic, and security vulnerabilities around data access control.

The Email Threads API provides a unified abstraction layer that aggregates email data across Gmail, Outlook (Microsoft Graph), and IMAP providers while enforcing consistent thread-based semantics, ownership policies, and filtering rules. This ADR defines the technical specification for the Email Threads API v2.

**Business Drivers:**
- Eliminate $2.3M annual maintenance cost from duplicate provider-specific thread logic
- Enable unified search across multi-provider mailboxes (user requirement from Platform Roadmap Q3-2024)
- Satisfy enterprise security audit requirements for centralized access control (SOC 2 Type II)

**Technical Drivers:**
- Standardize thread grouping algorithm across all providers
- Centralize draft/deletion filtering logic
- Provide consistent pagination and cursor-based navigation

---

## Decision

Implement Email Threads API v2 with the following specification:

### API Endpoints

#### 1. GET /v2/threads

Returns paginated list of email threads for the authenticated user.

**Request:**
```
GET /v2/threads?limit=20&cursor=eyJpZCI6MTIzfQ&provider=gmail,outlook&include_spam=false
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "thread_abc123",
      "subject": "Re: Q4 Planning Review",
      "snippet": "Thanks for sending over the deck. I've reviewed sections 2-4...",
      "message_count": 5,
      "unread_count": 2,
      "has_attachments": true,
      "last_message_date": "2026-09-08T14:32:00Z",
      "providers": ["gmail"],
      "participants": [
        {"email": "alice@example.com", "name": "Alice Johnson"},
        {"email": "bob@example.com", "name": "Bob Smith"}
      ],
      "labels": ["important", "inbox"],
      "folder": "inbox",
      "category": "primary"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true,
    "total_count": 847
  },
  "meta": {
    "providers_synced": ["gmail", "outlook"],
    "sync_timestamp": "2026-09-09T08:00:00Z"
  }
}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Results per page (1-100) |
| cursor | string | null | Pagination cursor from previous response |
| provider | string[] | all | Filter by provider: gmail, outlook, imap |
| folder | string | inbox | Filter by folder: inbox, sent, trash, spam |
| label | string | null | Gmail-specific labels |
| has_attachments | boolean | null | Filter threads with/without attachments |
| unread_only | boolean | false | Return only unread threads |
| starred_only | boolean | false |