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

  changeUserRole,

  deactivateUser,

  reactivateUser,

  getAuditLogs,

  getAdminStats,

} = require("../controllers/userController");

// Admin: Get all users
router.get("/users", auth, adminOnly, getUsers);

// User/Admin: Update user
router.put(
  "/users/:id",
  auth,
  updateUserValidation,
  validate,
  updateUser
);

// User/Admin: Delete own account or admin delete
router.delete(
  "/users/:id",
  auth,
  idParamValidation,
  validate,
  deleteUser
);

// Admin: Delete any user
router.delete(
  "/admin/users/:id",
  auth,
  adminOnly,
  idParamValidation,
  validate,
  deleteUser
);

// Admin: Change user role
router.patch(
  "/admin/users/:id/role",
  auth,
  adminOnly,
  idParamValidation,
  validate,
  changeUserRole
);

// Admin: Deactivate user
router.patch(
  "/admin/users/:id/deactivate",
  auth,
  adminOnly,
  idParamValidation,
  validate,
  deactivateUser
);

// Admin: Reactivate user
router.patch(
  "/admin/users/:id/reactivate",
  auth,
  adminOnly,
  idParamValidation,
  validate,
  reactivateUser
);
// Admin: View audit logs
router.get(
  "/admin/audit-logs",
  auth,
  adminOnly,
  getAuditLogs
);
// Admin: Dashboard stats
router.get(
  "/admin/stats",
  auth,
  adminOnly,
  getAdminStats
);

module.exports = router;
