# RIBIL Auth — Integration Notes (Sprint 1)

Reference for downstream teams (frontend, GIS, reports, document-pipeline) integrating with the
authentication module on `feature/auth`.

## 1. Architecture overview

```
Client ──HTTP──► Express app (backend/index.js)
                   │
                   ├─ helmet()                 security headers
                   ├─ express.json({limit:10kb})
                   ├─ authRoutes  → rateLimiter → validator → controller
                   ├─ userRoutes  → auth → (adminOnly|validator) → controller
                   ├─ inline routes: / /profile /me /admin
                   ├─ 404 handler
                   └─ error handler (500)
                        │
                  PostgreSQL (backend/db.js → pg Pool)
```

- **Entrypoint:** `backend/index.js` calls `require("dotenv").config()` first, exports `app`,
  and only calls `app.listen()` when run directly (`require.main === module`) — this lets
  supertest import the app without binding a port.
- **DB layer:** `backend/db.js` uses `DATABASE_URL` if present, otherwise discrete `PG*` env vars.
- **Auth:** stateless JWT (HS256), 1-hour expiry. No server-side session/store.

## 2. Environment configuration

`backend/.env` (copy from `backend/.env.example`, never commit):

| Variable | Required | Notes |
|----------|----------|-------|
| `JWT_SECRET` | **yes** | App fail-fasts on boot if unset (`authController` throws). Use a long random value. |
| `PORT` | no | Defaults to `3000`. |
| `DATABASE_URL` | optional | Full connection string; takes precedence over `PG*`. |
| `PGUSER` / `PGPASSWORD` / `PGHOST` / `PGPORT` / `PGDATABASE` | when no `DATABASE_URL` | Discrete Postgres settings. |

> The repo-root `.env.example` is the **platform-wide** template (Postgres, Redis, S3, etc.).
> The auth service only consumes the variables in `backend/.env.example`.

## 3. Database

- Schema lives at `backend/db/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- Apply with: `psql -d auth_practice -f backend/db/schema.sql`.
- The `email` `UNIQUE` constraint backstops the application-level duplicate check
  (`authController` also handles PG error `23505`).
- **Admin bootstrap:** `/register` always creates `role = 'user'`. To create an admin, update a
  row directly: `UPDATE users SET role='admin' WHERE email='...';`.

## 4. How to integrate (frontend / services)

1. **Register** → `POST /register`.
2. **Login** → `POST /login`, store the returned `token`.
3. Send `Authorization: Bearer <token>` on every protected call.
4. Handle `401` by redirecting to login (token missing/expired/invalid).
5. Handle `403` as "not allowed" (RBAC/ownership), distinct from `401`.
6. Treat `429` as "back off and retry later" (respect `X-RateLimit-Reset`).
7. Decode the JWT client-side only for display (`id`, `email`, `role`); never trust it for
   authorization — the server re-verifies every request.

### Authorization model

| Action | Allowed for |
|--------|-------------|
| `/admin`, `/users`, `/admin/users/:id` | admin only |
| `PUT/DELETE /users/:id` | the owner (`token.id === id`) **or** an admin |
| `/profile`, `/me` | any authenticated user |

## 5. Cross-cutting behavior

- **CORS:** not configured yet. A browser SPA on a different origin will need a CORS middleware
  added before integration (flagged in BUG_REPORT as OBS-1).
- **Body size:** JSON limited to `10kb`; larger payloads get a `400`/`413`.
- **Rate limiting:** in-memory per-process store. Across multiple instances/behind a proxy it is
  not shared and `trust proxy` is not set — see BUG_REPORT OBS-2 before horizontal scaling.
- **Error contract:** validation → `{ errors: [...] }`; everything else → `{ message: "..." }`.
  Integrators should branch on the presence of `errors` vs `message`.

## 6. Testing & CI

- **Local:** `cd backend && npm test` — 52 Jest + supertest tests, DB and rate-limiter mocked,
  so **no live Postgres is required** to run them. (22 cover the legacy routes; 30 cover the
  `/api/auth` OTP, session/refresh, password-reset, and middleware flows.)
- **CI:** owned by the CI/CD member — not covered by this deliverable. (At time of writing the
  workflow is a placeholder; running the suite in CI is tracked with that owner.)
- **Manual/integration:** import `docs/postman/RIBIL_Auth_Sprint1.postman_collection.json` and the
  matching environment; run the requests top-to-bottom (Register → Login captures the token
  automatically into `{{token}}`).

## 7. Verified end-to-end flow (against live PostgreSQL)

| Step | Result |
|------|--------|
| Register → Login → `/profile` with token | 201 → 200+token → 200 |
| `/me` returns id/email/role | 200 |
| `/admin` as user / as admin | 403 / 200 |
| `/users` as user / as admin | 403 / 200 |
| `PUT /users/:id` owner / other-user / invalid email / non-int id | 200 / 403 / 400 / 400 |
| `DELETE /users/:id` owner, `DELETE /admin/users/:id` admin | 200 / 200 |
| Login/Register rate limits | 429 after threshold |
| SQL injection probe on `/login` | safe (parameterized) → 401 |
| `/api/auth` register → verify-otp → login | 201 → 200 → 200 + access/refresh |
| `/api/auth` login before OTP verify | 403 (gated on `is_verified`) |
| `/api/auth` refresh rotation (reuse old token) | new pair issued; old token → 401 |
| `/api/auth` logout-all then refresh | sessions revoked → 401 |
| `/api/auth` forgot-password → reset-password → login (new pw) | 200 → 200 → 200 |

## 8. Known integration gaps

See `docs/BUG_REPORT.md`. Nothing blocks Sprint 1 sign-off; open items are CORS and a shared
rate-limit store for multi-instance. Refresh-token rotation is now implemented under `/api/auth`
(sessions stored hashed; rotation revokes the prior token via a per-token `jti`).
