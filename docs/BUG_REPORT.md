# RIBIL Auth — Bug Report (Sprint 1)

**Reviewer:** Manish (Member 1 — Testing / QA)
**Branch:** `feature/auth`
**Date:** 2026-06-12
**Method:** Static review + 22 automated tests (`npm test`, all passing) + live testing against PostgreSQL 16.

## Summary

The authentication module is **functionally complete and verified**. An earlier QA pass (against
an older snapshot) had flagged several defects; **all of them are resolved on the current
`feature/auth` branch** and re-verified here. Remaining items are non-blocking hardening
observations and one CI gap that this deliverable fixes.

| State | Count |
|-------|-------|
| Resolved & verified | 8 |
| Open observations (non-blocking) | 4 |
| Blocking defects | 0 |

---

## Resolved defects (re-verified on `feature/auth`)

| ID | Issue (earlier snapshot) | Fix on current branch | Verification |
|----|--------------------------|-----------------------|--------------|
| R-1 | Weak/hardcoded `JWT_SECRET` committed in `.env` | Secret read from env; app **throws on boot if unset**; `.env` is gitignored; `.env.example` ships `change-me` | Boot fail-fast confirmed; `.env` in `.gitignore` |
| R-2 | `GET /users` reachable by any authenticated user (PII leak) | Route now `auth, adminOnly, getUsers` | Live: user → **403**, admin → **200** |
| R-3 | `POST /login` returned **500** when password missing | `loginValidation` (email valid + password required) added | Live: missing password → **400** |
| R-4 | `PUT /users/:id` accepted invalid email / no validation | `updateUserValidation` (int id + name + valid email) added | Live: invalid email → **400** |
| R-5 | Non-integer `:id` caused **500** | `idParamValidation` / `param("id").isInt({min:1})` on PUT & DELETE | Live: `/users/abc` → **400** |
| R-6 | Debug middleware leaked `X-JO-TEST` header on every response | Debug middleware removed | Live: header **absent** |
| R-7 | DB credentials hardcoded in `db.js` | `db.js` now uses `DATABASE_URL` or `PG*` env vars | Code review |
| R-8 | No schema, no tests, placeholder `npm test` | `db/schema.sql` added; `jest`+`supertest` suite (22 tests); `npm test` runs Jest | `npm test` → **22 passed** |

Additional improvements observed: `express.json({ limit: "10kb" })`, email `normalizeEmail()`,
duplicate-email handled both pre-check and via PG `23505`, and `app` exported for testability.

---

## Open observations (non-blocking hardening)

| ID | Severity | Observation | Recommendation |
|----|----------|-------------|----------------|
| OBS-1 | Low | No CORS middleware. A browser SPA on another origin cannot call the API. | Add `cors` with an allow-list before frontend integration. |
| OBS-2 | Low | `express-rate-limit` uses the default in-memory store and `trust proxy` is not set. Limits are per-process and, behind a proxy, may key all clients to one IP. | Use a shared store (Redis) for multi-instance; set `app.set("trust proxy", 1)` when behind a proxy. |
| OBS-3 | Low | JWTs are 1-hour, non-revocable, with no refresh-token flow. | Add refresh tokens / rotation + a revocation list in a later sprint. |
| OBS-4 | Info | `Dockerfile` `CMD ["sh"]` does not start the app, and `docker-compose.yml` provisions Postgres/Redis but not the API service. | If containerized run is intended for Sprint 1, set `CMD ["node","backend/index.js"]` and add an `app` service. (Out of scope for auth verification.) |

---

## CI gap fixed by this deliverable

The existing `.github/workflows/ci.yml` was a **stub** — it only ran
`echo "CI Pipeline Running Successfully"` and never executed the test suite, so the "tests passing
in CI" status was not actually enforced. This PR replaces it with a workflow that runs
`npm ci` + `npm test` in `backend/` on every push and pull request (Node 18 & 20).

---

## Test evidence

```
Test Suites: 3 passed, 3 total
Tests:       22 passed, 22 total
```

Live spot-checks (PostgreSQL 16, `feature/auth`):

```
GET  /users        (user)        -> 403
GET  /users        (admin)       -> 200
POST /login        (no password) -> 400
PUT  /users/2      (bad email)   -> 400
PUT  /users/abc    (non-int id)  -> 400
GET  /            (X-JO-TEST)     -> absent
POST /login        (valid)       -> 200 + token
```

## Sign-off

**Sprint 1 authentication: PASS.** No blocking defects. Recommend merging this documentation +
CI deliverable; track OBS-1..4 as backlog items for hardening.
