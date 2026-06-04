const pool = require("./db");

async function testConnection() {
  try {
    const result = await pool.query("SELECT NOW()");
    console.log(result.rows);
  } catch (err) {
    console.error(err);
  }
}

testConnection();