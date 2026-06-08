const express = require("express");
const router = express.Router();

const auth = require("../middleware/auth");
const adminOnly = require("../middleware/admin");

const {
  getUsers,
  updateUser,
  deleteUser,
} = require("../controllers/userController");

router.get("/users", auth, getUsers);
router.put("/users/:id", auth, updateUser);
router.delete("/users/:id", auth, deleteUser);

// Admin delete user
router.delete(
  "/admin/users/:id",
  auth,
  adminOnly,
  deleteUser
);

module.exports = router;