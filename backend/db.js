const { Pool } = require("pg");

const pool = process.env.DATABASE_URL
  ? new Pool({ connectionString: process.env.DATABASE_URL })
  : new Pool({
      user: process.env.PGUSER,
      host: process.env.PGHOST || "localhost",
      database: process.env.PGDATABASE || "auth_practice",
      password: process.env.PGPASSWORD,
      port: Number(process.env.PGPORT) || 5432,
    });

pool.on("error", (err) => {
  console.error("Unexpected error on idle Postgres client", err);
});

module.exports = pool;
