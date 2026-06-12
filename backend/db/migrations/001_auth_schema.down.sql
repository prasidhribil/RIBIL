-- Migration 001 (DOWN): reverse the Sprint 1 auth schema.
-- Drops the new tables and the columns added to users. Run with:
--   psql -d <db> -f db/migrations/001_auth_schema.down.sql

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS otp_verifications;
DROP TABLE IF EXISTS sessions;

DROP INDEX IF EXISTS idx_users_role;

ALTER TABLE users DROP COLUMN IF EXISTS is_verified;
ALTER TABLE users DROP COLUMN IF EXISTS is_active;
ALTER TABLE users DROP COLUMN IF EXISTS phone;
ALTER TABLE users DROP COLUMN IF EXISTS full_name;
ALTER TABLE users DROP COLUMN IF EXISTS aadhaar_name;
ALTER TABLE users DROP COLUMN IF EXISTS aadhaar_last4;
ALTER TABLE users DROP COLUMN IF EXISTS updated_at;

-- NOTE: the base `users` table itself is intentionally NOT dropped here,
-- since it predates this migration.
