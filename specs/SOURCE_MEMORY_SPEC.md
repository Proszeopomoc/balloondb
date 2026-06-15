# Source memory spec V0

BalloonDB must remember where external data lives without importing everything.

Core logical record types:
- SOURCE_SEED
- LOCATION_SEED
- FORMAT_SEED
- SCHEMA_SEED
- FRAGMENT_REF
- ACCESS_ROUTE
- PROVENANCE_RECORD
- HYDRATED_FRAGMENT

Rules:
- External sources are read-only by default.
- New agent-created data is written natively to BalloonDB.
- Write-back to external DB/file requires explicit adapter and user permission.
- Hydration must be bounded by rows/bytes/time and recorded through WAL/cache/audit.
