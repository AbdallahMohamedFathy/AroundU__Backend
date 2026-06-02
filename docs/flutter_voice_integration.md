# Voice Message Integration — Flutter Team Guide

**Date:** 2026-06-02  
**Backend version:** current `main` branch  
**Prepared by:** Backend Team

---

## Overview

The backend now supports voice-originated messages. The Flutter app is responsible for converting speech to text locally (using `speech_to_text` or any equivalent package). The backend receives only the final transcribed text — no audio data is ever sent.

---

## What Changed on the Backend

| Area | Change |
|---|---|
| `POST /api/mobile/ai/chat` | Accepts new optional field `message_source` |
| Validation | Message is trimmed; empty/whitespace-only messages are rejected |
| Logging | `message_source` is stored in the database for future analytics |
| Pipeline | Voice messages go through the exact same chatbot pipeline as typed messages |

---

## API Endpoint

```
POST /api/mobile/ai/chat
Authorization: Bearer <token>
Content-Type: application/json
```

---

## Request Body

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | `string` | Yes | — | Transcribed text (max 2000 characters) |
| `session_id` | `string` | No | auto-generated | Pass the same ID to keep conversation context |
| `user_lat` | `float` | No | `null` | User latitude |
| `user_lon` | `float` | No | `null` | User longitude |
| `message_source` | `string` | No | `"text"` | Origin of the message: `"text"` or `"voice"` |

### Typed message example
```json
{
  "message": "أقرب مطعم عندي",
  "session_id": "abc-123",
  "user_lat": 29.0661,
  "user_lon": 31.0994,
  "message_source": "text"
}
```

### Voice message example
```json
{
  "message": "ما هي أعراض مرض السكري؟",
  "session_id": "abc-123",
  "user_lat": 29.0661,
  "user_lon": 31.0994,
  "message_source": "voice"
}
```

---

## Response Body

The response is **identical** for both typed and voice messages — no change on the Flutter side for parsing.

```json
{
  "reply": "...",
  "intent": "...",
  "confidence": 0.95,
  "entities": {},
  "best_place": null,
  "session_id": "abc-123",
  "is_fallback": false
}
```

---

## Validation Rules

The backend enforces these rules on `message`:

- Leading and trailing whitespace is stripped automatically.
- After stripping, if the message is empty it is rejected with `422 Unprocessable Entity`.
- Maximum length is **2000 characters**.

Recommended: disable the send button in the UI while speech recognition is still in progress to avoid accidentally sending empty strings.

---

## Error Responses

### Empty message after trimming
```json
HTTP 422 Unprocessable Entity
{
  "success": false,
  "error": {
    "message": "Validation Error",
    "details": [
      {
        "loc": ["body", "message"],
        "msg": "message must not be empty or whitespace",
        "type": "value_error"
      }
    ],
    "code": 422
  }
}
```

### Message too long
```json
HTTP 422 Unprocessable Entity
{
  "success": false,
  "error": {
    "message": "Validation Error",
    "details": [
      {
        "loc": ["body", "message"],
        "msg": "String should have at most 2000 characters",
        "type": "string_too_long"
      }
    ],
    "code": 422
  }
}
```

### Not authenticated
```json
HTTP 401 Unauthorized
```

### Rate limit exceeded
```json
HTTP 429 Too Many Requests
```

---

## Suggested Flutter Implementation

```dart
Future<void> sendVoiceMessage(String transcribedText, String sessionId) async {
  final trimmed = transcribedText.trim();
  if (trimmed.isEmpty) return; // guard before hitting the API

  final response = await http.post(
    Uri.parse('$baseUrl/api/mobile/ai/chat'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'message': trimmed,
      'session_id': sessionId,
      'user_lat': currentLat,
      'user_lon': currentLon,
      'message_source': 'voice',   // <-- only difference from typed messages
    }),
  );

  // Parse response exactly the same as typed messages
  final data = jsonDecode(response.body);
  // ...
}
```

---

## Important Notes

1. **No audio should ever be sent to the backend.** Only the final transcribed string.
2. **`message_source` is optional.** If omitted, the backend defaults to `"text"`. Always send `"voice"` for speech-originated messages to enable future analytics.
3. **Session continuity:** Use the same `session_id` across the conversation so the chatbot maintains context whether the user types or speaks.
4. **No new endpoints.** Voice messages use the exact same `/api/mobile/ai/chat` endpoint as typed messages.
5. **No infrastructure changes.** No audio upload, no STT on the server, no new dependencies.

---

## Questions?

Reach out to the backend team on the project channel.
