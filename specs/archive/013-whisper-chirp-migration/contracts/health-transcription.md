# Contract: Transcription Health Check

**Endpoint**: `GET /api/v1/health/transcription`
**Added by**: 013-whisper-chirp-migration
**Authentication**: Admin or internal access only

## Purpose

Expose the current transcription provider state and circuit breaker status
for operational monitoring.

## Request

```
GET /api/v1/health/transcription
Authorization: Bearer <admin_jwt>
```

No request body or query parameters.

## Success Response (200 OK)

```json
{
  "provider": "chirp_3",
  "fallback_provider": "whisper",
  "circuit_breaker_state": "CLOSED",
  "consecutive_failures": 0,
  "fallback_active": false,
  "config": {
    "transcription_provider": "chirp",
    "chirp_model": "chirp_3",
    "circuit_breaker_threshold": 5,
    "circuit_breaker_cooldown_seconds": 300
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| provider | string | Currently active provider name |
| fallback_provider | string | Fallback provider name |
| circuit_breaker_state | string | "CLOSED" (normal) or "OPEN" (fallback active) |
| consecutive_failures | int | Number of consecutive failures since last success |
| fallback_active | bool | True if requests are being routed to fallback |
| config | object | Current configuration values |

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

## Notes

- This endpoint does NOT modify any state
- When `fallback_active` is `true`, all transcription requests are routed to
  the `fallback_provider` regardless of `config.transcription_provider`
- The `consecutive_failures` counter resets to 0 on any successful transcription
