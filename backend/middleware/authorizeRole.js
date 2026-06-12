// Role-based authorization factory.
// Usage: router.get("/admin/users", auth, authorizeRole("admin"), handler)
// Must run after the `auth` middleware so req.user is populated.
function authorizeRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: { code: "FORBIDDEN" } });
    }
    next();
  };
}

module.exports = authorizeRole;
