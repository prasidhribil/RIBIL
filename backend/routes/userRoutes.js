const express = require("express");
const router = express.Router();

const auth = require("../middleware/auth");
const adminOnly = require("../middleware/admin");

const {
  updateUserValidation,
  idParamValidation,
  validate,
} = require("../validators/authValidator");

const {
  getUsers,
  updateUser,
  deleteUser,
} = require("../controllers/userController");

router.get("/users", auth, adminOnly, getUsers);

router.put(
  "/users/:id",
  auth,
  updateUserValidation,
  validate,
  updateUser
);

router.delete(
  "/users/:id",
  auth,
  idParamValidation,
  validate,
  deleteUser
);

// Admin delete user
router.delete(
  "/admin/users/:id",
  auth,
  adminOnly,
  idParamValidation,
  validate,
  deleteUser
);

module.exports = router;
