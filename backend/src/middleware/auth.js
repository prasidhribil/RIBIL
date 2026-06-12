// STUB auth middleware for Sprint 1. Member 1 (auth) owns the real RS256 JWT
// implementation; swap this out for their `authenticateToken` / `authorizeRole`
// once delivered. The interface (req.user = { id, role }) is kept compatible.
//
// In dev, pass `x-dev-user-id` and `x-dev-role` headers to simulate a user.
function authenticateToken(req, res, next) {
  const id = req.header("x-dev-user-id") || null;
  const role = req.header("x-dev-role") || "buyer";
  req.user = { id, role };
  next();
}

function authorizeRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({
        error: { code: "FORBIDDEN", message: "Insufficient role" },
      });
    }
    next();
  };
}

module.exports = { authenticateToken, authorizeRole };
