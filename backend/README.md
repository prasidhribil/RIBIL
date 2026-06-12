# Auth Practice Backend

Authentication backend built with Node.js, Express, PostgreSQL, JWT, bcrypt,
express-validator, Helmet and express-rate-limit.

## Setup

```bash
npm install
cp .env.example .env        # then edit values (set a strong JWT_SECRET)
psql -d auth_practice -f db/schema.sql
npm run dev                 # or: npm start
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | Secret used to sign/verify JWTs (required) |
| `PORT` | HTTP port (default `3000`) |
| `DATABASE_URL` | Full Postgres connection string (optional) |
| `PGUSER` / `PGPASSWORD` / `PGHOST` / `PGPORT` / `PGDATABASE` | Discrete Postgres connection settings (used when `DATABASE_URL` is unset) |

## API

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/register` | – | Register a new user |
| POST | `/login` | – | Log in, returns a JWT |
| GET | `/profile` | Bearer | Current user profile |
| GET | `/me` | Bearer | Current user id/email/role |
| GET | `/admin` | Bearer + admin | Admin-only check |
| GET | `/users` | Bearer + admin | List all users |
| PUT | `/users/:id` | Bearer (owner or admin) | Update name/email |
| DELETE | `/users/:id` | Bearer (owner or admin) | Delete a user |
| DELETE | `/admin/users/:id` | Bearer + admin | Admin delete a user |

Send the token as `Authorization: Bearer <token>`.

## Testing

```bash
npm test
```

Tests use Jest + supertest with the database layer mocked, so no live
PostgreSQL is required to run them.
