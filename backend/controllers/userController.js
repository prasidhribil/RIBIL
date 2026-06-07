const pool = require("../db");

const getUsers = async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT id, name, email, role, created_at FROM users ORDER BY id"
    );

    res.json(result.rows);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

const updateUser = async (req, res) => {
  const { id } = req.params;
  const { name, email } = req.body;

  if (
    req.user.id !== Number(id) &&
    req.user.role !== "admin"
  ) {
    return res.status(403).json({
      message: "Access denied",
    });
  }

  if (!name || !email) {
    return res.status(400).json({
      message: "Name and email are required",
    });
  }

  try {
    const emailCheck = await pool.query(
      `
      SELECT * FROM users
      WHERE email = $1
      AND id != $2
      `,
      [email, id]
    );

    if (emailCheck.rows.length > 0) {
      return res.status(409).json({
        message: "Email already exists",
      });
    }

    const result = await pool.query(
      `
      UPDATE users
      SET name = $1, email = $2
      WHERE id = $3
      RETURNING id, name, email, role
      `,
      [name, email, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "User not found",
      });
    }

    res.json({
      message: "User updated successfully",
      user: result.rows[0],
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Server error",
    });
  }
};

const deleteUser = async (req, res) => {
  const { id } = req.params;

  if (
    req.user.id !== Number(id) &&
    req.user.role !== "admin"
  ) {
    return res.status(403).json({
      message: "Access denied",
    });
  }

  try {
    const result = await pool.query(
      "DELETE FROM users WHERE id = $1 RETURNING *",
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "User not found",
      });
    }

    res.json({
      message: "User deleted successfully",
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Server error",
    });
  }
};

module.exports = {
  getUsers,
  updateUser,
  deleteUser,
};