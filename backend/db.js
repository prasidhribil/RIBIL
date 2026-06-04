const { Pool } = require("pg");

const pool = new Pool({
  user: "tejovanthkemburaj",
  host: "localhost",
  database: "auth_practice",
  port: 5432,
});

module.exports = pool;