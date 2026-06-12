const { Pool } = require("pg");
require("dotenv").config();

// Prefer DATABASE_URL (matches docker-compose / .env.example); fall back to
// discrete DB_* vars for local setups that don't use a connection string.
const pool = process.env.DATABASE_URL
  ? new Pool({ connectionString: process.env.DATABASE_URL })
  : new Pool({
      user: process.env.DB_USER,
      host: process.env.DB_HOST,
      database: process.env.DB_NAME,
      password: process.env.DB_PASSWORD,
      port: process.env.DB_PORT,
    });

module.exports = pool;
