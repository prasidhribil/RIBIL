const pool = require("./db");

async function insertUser() {
  try {
    await pool.query(
      "INSERT INTO users (name, email, password) VALUES ($1, $2, $3)",
      ["Test User", "test@example.com", "123456"]
    );

    console.log("User inserted successfully!");
  } catch (error) {
    console.error(error);
  } finally {
    process.exit();
  }
}

insertUser();