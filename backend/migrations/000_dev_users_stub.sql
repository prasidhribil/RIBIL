-- DEV ONLY — minimal users table so Member 5's schema can run standalone before
-- Member 1's auth migration is merged. Member 1 owns the real users table; in
-- integration their migration runs first and this file is skipped (IF NOT EXISTS).
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    role VARCHAR DEFAULT 'buyer',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
