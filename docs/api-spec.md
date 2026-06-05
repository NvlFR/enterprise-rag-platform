# API Specification

## Overview
The Enterprise Knowledge Assistant (EKA) provides a RESTful API for document management, knowledge retrieval, and AI-powered chat. All endpoints are versioned and require authentication via JWT.

- **Base URL:** `/api/v1`
- **Content-Type:** `application/json`

---

## Authentication

### Login
`POST /auth/login`

**Request:**
```json
{
  "email": "user@enterprise.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

---

## Document Management

### Upload Document
`POST /documents`

**Request:** `multipart/form-data`
- `file`: (Binary) PDF, DOCX, or TXT file.
- `tags`: (Optional) Stringified array of tags.

**Response (201 Created):**
```json
{
  "id": "doc_88291",
  "filename": "HR_Policy_2024.pdf",
  "status": "processing",
  "created_at": "2024-06-05T10:00:00Z"
}
```

### List Documents
`GET /documents`

**Response (200 OK):**
```json
[
  {
    "id": "doc_88291",
    "filename": "HR_Policy_2024.pdf",
    "status": "completed",
    "page_count": 45
  }
]
```

---

## Chat & Retrieval

### Chat with AI
`POST /chat`

**Request:**
```json
{
  "message": "What is the policy for annual leave?",
  "conversation_id": "conv_12345",
  "stream": false
}
```

**Response (200 OK):**
```json
{
  "message_id": "msg_9901",
  "content": "According to the HR Policy 2024, employees are entitled to 20 days of annual leave per year [1].",
  "citations": [
    {
      "id": 1,
      "source": "HR_Policy_2024.pdf",
      "page": 12,
      "text": "Full-time employees shall receive 20 days of paid annual leave..."
    }
  ]
}
```

---

## Error Handling

| Code | Meaning | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid input parameters. |
| 401 | Unauthorized | Missing or invalid authentication token. |
| 403 | Forbidden | Insufficient permissions for this resource. |
| 404 | Not Found | The requested resource does not exist. |
| 429 | Too Many Requests | Rate limit exceeded. |
| 500 | Internal Server Error | Something went wrong on our end. |

**Standard Error Response:**
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Document with ID doc_999 not found."
  }
}
```
