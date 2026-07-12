# Data Model: Lift-and-Shift Backend to Contabo VPS

No data model changes. This is an infrastructure-only migration.

## Existing Entities (unchanged)

All existing database tables (User, Meeting, TranscriptSegment, SummaryTemplate, etc.) remain unchanged. The same PostgreSQL schema runs on the VPS as it did locally.

## New Infrastructure Entity

### Qdrant (Vector Database)

- Added to docker-compose as a service but **no application code connects to it yet**
- Empty on deployment — will be populated by the future AI Chat feature
- Data persisted via Docker volume `qdrant_data`
- Runs on default port 6333 (internal Docker network only)
