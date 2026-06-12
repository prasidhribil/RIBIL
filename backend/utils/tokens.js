const jwt = require("jsonwebtoken");
const crypto = require("crypto");

const JWT_SECRET = process.env.JWT_SECRET;

if (!JWT_SECRET) {
  throw new Error("JWT_SECRET is not set. Define it in the environment.");
}

const ACCESS_TTL = "15m";
const REFRESH_TTL = "7d";
const REFRESH_TTL_MS = 7 * 24 * 60 * 60 * 1000;

// Short-lived access token carrying identity + role.
function signAccessToken(user) {
  return jwt.sign(
    { id: user.id, email: user.email, role: user.role },
    JWT_SECRET,
    { expiresIn: ACCESS_TTL }
  );
}

// Long-lived refresh token. Only the SHA-256 hash is ever stored server-side.
// A random jti guarantees each issued token (and thus its hash) is unique, so
// rotation reliably revokes the exact previous token.
function signRefreshToken(user) {
  return jwt.sign(
    { id: user.id, type: "refresh", jti: crypto.randomBytes(16).toString("hex") },
    JWT_SECRET,
    { expiresIn: REFRESH_TTL }
  );
}

function verifyRefreshToken(token) {
  const decoded = jwt.verify(token, JWT_SECRET);
  if (decoded.type !== "refresh") {
    throw new Error("Not a refresh token");
  }
  return decoded;
}

function hashToken(token) {
  return crypto.createHash("sha256").update(token).digest("hex");
}

function refreshExpiryDate() {
  return new Date(Date.now() + REFRESH_TTL_MS);
}

module.exports = {
  signAccessToken,
  signRefreshToken,
  verifyRefreshToken,
  hashToken,
  refreshExpiryDate,
  ACCESS_TTL,
  REFRESH_TTL,
};
