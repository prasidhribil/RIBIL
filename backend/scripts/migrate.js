// Minimal migration runner: executes every .sql file in /migrations in
// lexical order against the configured database. Safe to extend later.
require("dotenv").config();
const fs = require("fs");
const path = require("path");
const pool = require("../src/config/database");

async function run() {
  const dir = path.join(__dirname, "..", "migrations");
  const files = fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".sql"))
    .sort();

  for (const file of files) {
    const sql = fs.readFileSync(path.join(dir, file), "utf8");
    process.stdout.write(`Running ${file} ... `);
    await pool.query(sql);
    console.log("done");
  }
  await pool.end();
  console.log("All migrations applied.");
}

run().catch((err) => {
  console.error("Migration failed:", err.message);
  process.exit(1);
});
