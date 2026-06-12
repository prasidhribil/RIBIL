# RIBIL Auth API — Documentation (Sprint 1)

Authentication module for the RIBIL platform.
Stack: Node.js, Express 5, PostgreSQL, JWT, bcrypt, Helmet, express-rate-limit, express-validator.

- **Base URL (local):** `http://localhost:3000`
- **Auth scheme:** Bearer JWT — `Authorization: Bearer <token>`
- **Content type:** `application/json`
- **Token lifetime:** 1 hour (`exp` claim)
- **Token payload:** `{ id, email, role, iat, exp }`

> All examples below were verified against the running `feature/auth` build.

---

## Conventions

### Standard error shapes

Validation errors (from `express-validator`) return an `errors` array:

```json
{
  "errors": [
    { "type": "field", "value": "", "msg": "Name is required", "path": "name", "location": "body" }
  ]
}
```

Business/auth errors return a single `message`:

```json
{ "message": "Invalid email or password" }
```

### Common status codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Validation error (missing/invalid fields, non-integer `:id`) |
| 401 | Missing/invalid/expired token, or bad credentials |
| 403 | Authenticated but not authorized (RBAC / ownership) |
| 404 | Resource not found |
| 409 | Conflict (email already exists) |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error |

### Security headers (Helmet)

Every response includes Helmet headers and omits `X-Powered-By`:
`Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
`X-Frame-Options: SAMEORIGIN`, `X-DNS-Prefetch-Control: off`, `X-Download-Options: noopen`.

### Rate limits

| Endpoint | Window | Max requests / IP |
|----------|--------|-------------------|
| `POST /login` | 15 min | 5 |
| `POST /register` | 60 min | 3 |

On exceed: `429` with `{ "message": "Too many ... attempts. Try again later." }` and `X-RateLimit-*` headers.

---

## Endpoints

### 1. `POST /register` — Register a new user

Public. Rate-limited (3/hour). Creates a user with role `user` (role is always assigned server-side and cannot be set by the client).

**Body**

| Field | Type | Rules |
|-------|------|-------|
| `name` | string | required, non-empty |
| `email` | string | required, valid email (normalized) |
| `password` | string | min 8 chars; must contain lowercase, uppercase, digit, and special char (`@$!%*?&`) |

**Request**

```bash
curl -X POST http://localhost:3000/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jo","email":"jo@example.com","password":"Str0ng!Pass"}'
```

**201 Created**

```json
{ "message": "Registration successful" }
```

**400 Bad Request** (weak password)

```json
{
  "errors": [
    { "type": "field", "value": "weak", "msg": "Password must be at least 8 characters", "path": "password", "location": "body" },
    { "type": "field", "value": "weak", "msg": "Password must contain uppercase, lowercase, number and special character", "path": "password", "location": "body" }
  ]
}
```

**409 Conflict**

```json
{ "message": "Email already exists" }
```

---

### 2. `POST /login` — Log in

Public. Rate-limited (5/15 min). Returns a signed JWT.

**Body**

| Field | Type | Rules |
|-------|------|-------|
| `email` | string | required, valid email |
| `password` | string | required |

**Request**

```bash
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jo@example.com","password":"Str0ng!Pass"}'
```

**200 OK**

```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<...>.<signature>"
}
```

**400 Bad Request** (missing password)

```json
{ "errors": [ { "type": "field", "msg": "Password is required", "path": "password", "location": "body" } ] }
```

**401 Unauthorized** (wrong password or unknown email — identical message to avoid user enumeration)

```json
{ "message": "Invalid email or password" }
```

---

### 3. `GET /profile` — Current user profile

Requires Bearer token.

**Request**

```bash
curl http://localhost:3000/profile -H "Authorization: Bearer $TOKEN"
```

**200 OK**

```json
{
  "message": "Profile accessed successfully",
  "user": { "id": 1, "email": "jo@example.com", "role": "user", "iat": 1781250000, "exp": 1781253600 }
}
```

**401 Unauthorized**

```json
{ "message": "Access denied. No token provided." }
```
or, for a malformed/expired token:
```json
{ "message": "Invalid token" }
```

---

### 4. `GET /me` — Current identity

Requires Bearer token. Returns the minimal identity claims.

**200 OK**

```json
{ "id": 1, "email": "jo@example.com", "role": "user" }
```

---

### 5. `GET /admin` — Admin check

Requires Bearer token **and** `role === "admin"`.

**200 OK**

```json
{ "message": "Welcome Admin" }
```

**403 Forbidden** (non-admin)

```json
{ "message": "Admin access required" }
```

---

### 6. `GET /users` — List all users

Requires Bearer token **and** admin role.

**200 OK**

```json
[
  { "id": 1, "name": "Admin", "email": "admin@example.com", "role": "admin", "created_at": "2026-06-12T08:00:00.000Z" },
  { "id": 2, "name": "Jo", "email": "jo@example.com", "role": "user", "created_at": "2026-06-12T08:01:00.000Z" }
]
```

**403 Forbidden** (non-admin) — `{ "message": "Admin access required" }`

> Note: passwords are never returned by this endpoint.

---

### 7. `PUT /users/:id` — Update a user

Requires Bearer token. Caller must be the **owner** (`token.id === :id`) **or** an admin.

**Path params**

| Param | Rules |
|-------|-------|
| `id` | integer ≥ 1 |

**Body**

| Field | Type | Rules |
|-------|------|-------|
| `name` | string | required, non-empty |
| `email` | string | required, valid email (normalized) |

**Request**

```bash
curl -X PUT http://localhost:3000/users/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jo Updated","email":"jo@example.com"}'
```

**200 OK**

```json
{
  "message": "User updated successfully",
  "user": { "id": 2, "name": "Jo Updated", "email": "jo@example.com", "role": "user" }
}
```

**Errors:** `400` (non-integer id / invalid email / missing field), `403` (not owner or admin), `404` (user not found), `409` (email already used by another user).

---

### 8. `DELETE /users/:id` — Delete a user

Requires Bearer token. Caller must be the **owner** or an admin.

**Request**

```bash
curl -X DELETE http://localhost:3000/users/2 -H "Authorization: Bearer $TOKEN"
```

**200 OK** — `{ "message": "User deleted successfully" }`

**Errors:** `400` (non-integer id), `403` (not owner/admin), `404` (not found).

---

### 9. `DELETE /admin/users/:id` — Admin delete a user

Requires Bearer token **and** admin role.

**200 OK** — `{ "message": "User deleted successfully" }`

**Errors:** `400` (non-integer id), `403` (non-admin), `404` (not found).

---

## `/api/auth/*` — Full Sprint 1 auth flow

The endpoints above are the original bare routes (retained for backward compatibility). The complete Sprint 1 flow — OTP email verification, refresh-token rotation, logout, and password reset — lives under the `/api/auth` namespace. Access tokens here are **15 min**; refresh tokens are **7 days** and stored server-side only as SHA-256 hashes in the `sessions` table.

> Auth-middleware errors here carry a stable `code`: `MISSING_TOKEN`, `TOKEN_EXPIRED`, or `INVALID_TOKEN` (all `401`). `authorizeRole` returns `403 { "error": { "code": "FORBIDDEN" } }`.

### `POST /api/auth/register`
Public. bcrypt(12). Creates an **unverified** user and emails a 6-digit OTP (10-min expiry). Optional `phone` (10-digit Indian) and `role` (`buyer`/`agent`).
```bash
curl -X POST http://localhost:3000/api/auth/register -H "Content-Type: application/json" \
  -d '{"name":"Jo","email":"jo@example.com","password":"Str0ng!Pass","role":"buyer"}'
```
**201** → `{ "message": "Registration successful. Verify the OTP sent to your email." }` · **409** if email exists.

### `POST /api/auth/verify-otp`
Public. Validates the register OTP (single-use + expiry) and sets `is_verified=true`.
Body: `{ email, otp }` → **200** `{ "message": "Account verified successfully" }` · **400** invalid/expired OTP.

### `POST /api/auth/resend-otp`
Public. Invalidates prior register OTPs and issues a new one. Throttled to **3/hour** per email.
Body: `{ email }` → **200** · **429** when throttle exceeded.

### `POST /api/auth/login`
Public. Gates on `is_verified` and `is_active`. Returns an access + refresh token pair and records a session.
Body: `{ email, password }` → **200** `{ "message": "Login successful", "accessToken", "refreshToken" }` · **401** bad creds · **403** unverified/deactivated.

### `POST /api/auth/refresh`
Public (refresh token in body). Verifies the refresh JWT and its active session, then **rotates**: the old session is revoked and a new token pair is issued.
Body: `{ refreshToken }` → **200** `{ "accessToken", "refreshToken" }` · **401** invalid/expired/revoked.

### `POST /api/auth/logout`
Public (refresh token in body). Revokes the matching session.
Body: `{ refreshToken }` → **200** `{ "message": "Logged out successfully" }`.

### `POST /api/auth/logout-all`
**Requires Bearer access token.** Revokes every active session for the caller.
→ **200** `{ "message": "Logged out from all devices" }` · **401** without token.

### `POST /api/auth/forgot-password`
Public. **Always returns 200** (no email enumeration). Emails a reset OTP if the account exists.
Body: `{ email }` → **200** `{ "message": "If that email is registered, a reset code has been sent." }`.

### `POST /api/auth/reset-password`
Public. Validates the reset OTP, sets a new bcrypt(12) password, and revokes all of that user's sessions.
Body: `{ email, otp, newPassword }` → **200** `{ "message": "Password reset successfully" }` · **400** invalid/expired OTP or weak password.

---

## Endpoint summary

| Method | Route | Auth | Notes |
|--------|-------|------|-------|
| POST | `/register` | public | legacy; 3/hour |
| POST | `/login` | public | legacy; 5/15min |
| GET | `/profile` | Bearer | – |
| GET | `/me` | Bearer | – |
| GET | `/admin` | Bearer + admin | – |
| GET | `/users` | Bearer + admin | – |
| PUT | `/users/:id` | Bearer (owner or admin) | – |
| DELETE | `/users/:id` | Bearer (owner or admin) | – |
| DELETE | `/admin/users/:id` | Bearer + admin | – |
| POST | `/api/auth/register` | public | bcrypt(12) + OTP |
| POST | `/api/auth/verify-otp` | public | activates account |
| POST | `/api/auth/resend-otp` | public | 3/hour |
| POST | `/api/auth/login` | public | access(15m)+refresh(7d) |
| POST | `/api/auth/refresh` | refresh token | rotates session |
| POST | `/api/auth/logout` | refresh token | revoke one session |
| POST | `/api/auth/logout-all` | Bearer | revoke all sessions |
| POST | `/api/auth/forgot-password` | public | always 200 |
| POST | `/api/auth/reset-password` | reset OTP | revoke all sessions |

## Local setup

```bash
cd backend
npm install
cp .env.example .env        # set a strong JWT_SECRET and PG* / DATABASE_URL
psql -d auth_practice -f db/schema.sql
npm run dev                 # http://localhost:3000
npm test                    # 52 Jest + supertest tests (DB mocked)
```
