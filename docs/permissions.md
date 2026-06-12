# Role & Permission Matrix

Authorization is enforced by two middleware exported from `backend/middleware`:

- `auth` (`authenticateToken`) — verifies the bearer access token, attaches
  `req.user = { id, email, role }`, and returns `401` with a `code` of
  `MISSING_TOKEN`, `TOKEN_EXPIRED`, or `INVALID_TOKEN`.
- `authorizeRole(...roles)` — factory that returns `403 { error: { code: "FORBIDDEN" } }`
  unless `req.user.role` is in the allowed set. Always chained after `auth`:

  ```js
  router.get("/admin/users", auth, authorizeRole("admin"), handler);
  ```

## Roles

| Role  | Scope |
|-------|-------|
| **buyer** | Own data only (own profile, own verification requests/reports). |
| **agent** | Own clients' data + bulk verification + share reports. |
| **admin** | Everything: user management, audit logs, analytics, all data. |

> Note: the legacy routes in this repo historically use the role value `user`.
> New `/api/auth` registrations accept `buyer` / `agent`. `admin` is assigned
> out of band. The `authorizeRole` factory works with any role string, so both
> vocabularies are supported during the transition.

## Endpoint access (auth domain)

| Endpoint | Auth required | Allowed roles |
|----------|---------------|---------------|
| `POST /api/auth/register` | No | — |
| `POST /api/auth/verify-otp` | No | — |
| `POST /api/auth/resend-otp` | No | — |
| `POST /api/auth/login` | No | — |
| `POST /api/auth/refresh` | No (refresh token) | — |
| `POST /api/auth/forgot-password` | No | — |
| `POST /api/auth/reset-password` | No (reset OTP) | — |
| `POST /api/auth/logout` | No (refresh token) | — |
| `POST /api/auth/logout-all` | Yes (access token) | any authenticated |
| `GET /me`, `GET /profile` | Yes | any authenticated |
| `GET /users` | Yes | admin |
| `GET /admin` | Yes | admin |
| `DELETE /admin/users/:id` | Yes | admin |
