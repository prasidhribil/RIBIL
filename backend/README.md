# RIBIL Backend — Document Pipeline (Member 5)

Sprint 1 (D-01): document upload, virus scan, storage, listing, and pre-signed
download, plus the 5-table document/verification schema.

## Setup

```bash
cd backend
npm install
cp ../.env.example .env   # then fill in values (see below)
npm run migrate           # applies migrations/*.sql in order
npm run dev               # starts server on PORT (default 3000)
```

### Environment
`database.js` accepts either `DATABASE_URL` (preferred, matches
`docker-compose.yml`) or discrete `DB_USER/DB_HOST/DB_NAME/DB_PASSWORD/DB_PORT`.

Storage uses `STORAGE_DRIVER`:
- `s3` — real AWS S3 (needs `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_REGION`, `S3_BUCKET`).
- `local` — dev fallback that writes to `backend/.local-storage/` and serves
  files via HMAC-signed, time-limited URLs (`LOCAL_SIGN_SECRET`). Used automatically
  when no AWS creds are present.

Virus scanning uses ClamAV (`clamscan` on PATH). If unavailable it falls back to
EICAR-signature detection so the security path still works in dev. `SKIP_VIRUS_SCAN=true`
disables scanning entirely.

## Endpoints

All routes are gated by `authenticateToken` + `authorizeRole('buyer','agent','admin')`.
Auth is currently a **stub** (Member 1 owns the real RS256 JWT); in dev pass
`x-dev-role` and optional `x-dev-user-id` headers.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | multipart field `document` + body `property_id`. memoryStorage → validate (≤10MB, PDF/JPG/PNG) → ClamAV → S3 → DB insert → async classify. |
| `GET` | `/api/documents/:property_id` | List documents for a property. |
| `GET` | `/api/documents/:id/download` | Returns `{ download_url, expires_at }` (pre-signed, 15-min expiry). |
| `GET` | `/api/documents/_local` | Dev-only: serves a local-driver file behind a signed URL. |

### Example (local dev)
```bash
# upload
curl -H "x-dev-role: buyer" -X POST http://localhost:3000/api/documents/upload \
  -F "document=@test.pdf;type=application/pdf" -F "property_id=<uuid>"

# list
curl -H "x-dev-role: buyer" http://localhost:3000/api/documents/<property_id>

# download
curl -H "x-dev-role: buyer" http://localhost:3000/api/documents/<doc_id>/download
```

## Schema
`migrations/001_member5_schema.sql` creates: `properties` (PostGIS `geom`),
`property_documents`, `doc_ocr_extracts`, `verification_status` (14 check types),
`verification_reports`. `migrations/000_dev_users_stub.sql` is a **dev-only**
minimal `users` table so the schema runs before Member 1's auth migration is merged.

## Not yet implemented (next sprints)
OCR pipeline + field extractors (D-02), verification state machine endpoints
`PATCH /api/verify/:id/status` & `GET /api/verify/:id/summary` (D-03), CCTNS check (D-06).
