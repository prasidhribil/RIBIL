// Auth middleware integrated with Member 1's auth service.
//
// `authenticateToken` mirrors Member 1's `auth` middleware contract
// (backend/middleware/auth.js on feature/auth): it expects an
// `Authorization: Bearer <token>` header and a JWT signed with JWT_SECRET
// (HS256). On success it sets req.user = { id, email, role } from the token.
// When the auth module is consolidated during integration this can be replaced
// by a direct require of the shared middleware without changing call sites.
require("dotenv").config();
const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET;

function authenticateToken(req, res, next) {
  const authHeader = req.headers.authorization;
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) {
    return res
      .status(401)
      .json({ error: { code: "MISSING_TOKEN", message: "Access denied. No token provided." } });
  }

  if (!JWT_SECRET) {
    return res
      .status(500)
      .json({ error: { code: "AUTH_MISCONFIGURED", message: "JWT_SECRET is not set" } });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded; // { id, email, role }
    next();
  } catch (error) {
    if (error.name === "TokenExpiredError") {
      return res
        .status(401)
        .json({ error: { code: "TOKEN_EXPIRED", message: "Token expired" } });
    }
    return res
      .status(401)
      .json({ error: { code: "INVALID_TOKEN", message: "Invalid token" } });
  }
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
