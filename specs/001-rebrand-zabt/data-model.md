# Data Model: Zabt Rebranding & Logto Removal

**Feature**: `001-rebrand-zabt`
**Date**: 2026-02-22

---

> **Note**: This feature introduces **no new data entities**. It is a pure rename/cleanup operation. The data model section documents the *renamed* database and existing entities for completeness.

---

## Renamed: Database

| Field | Old Value | New Value |
|-------|-----------|-----------|
| `POSTGRES_DB` | `pareto_ai` | `zabt` |
| `DATABASE_URL` database segment | `/pareto_ai` | `/zabt` |

**Migration note**: No schema changes. The only required action is `docker-compose down -v` (destroys old named volume) followed by `docker-compose up` (recreates with the new database name).

---

## Existing Entities (unchanged, listed for traceability)

All entity names, fields, and relationships are UNCHANGED by this feature. The rename only affects configuration strings, not table/column names.

| Entity | Table | Notes |
|--------|-------|-------|
| `User` | `user` | `supabase_id` field (updated in 001-migrate-supabase) |
| `Meeting` | `meeting` | No changes |
| `TranscriptSegment` | `transcriptsegment` | No changes |
| `StyleProfile` | `styleprofile` | No changes |
| `Subscription` | `subscription` | No changes |

---

## Validation Rules (unchanged)

All existing model validations carry over without modification. No new fields, no new constraints introduced by this feature.
