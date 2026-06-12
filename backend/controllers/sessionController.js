const pool = require("../db");
const bcrypt = require("bcrypt");

const {
  signAccessToken,
  signRefreshToken,
  verifyRefreshToken,
  hashToken,
  refreshExpiryDate,
} = require("../utils/tokens");
const { writeAudit, requestMeta } = require("../utils/audit");

// Persist a new refresh-token session row for a user.
async function createSession(user, refreshToken, req) {
  await pool.query(
    `INSERT INTO sessions (user_id, refresh_token_hash, device_info, ip_address, expires_at)
     VALUES ($1, $2, $3, $4, $5)`,
    [
      user.id,
      hashToken(refreshToken),
      req.headers["user-agent"] || null,
      req.ip,
      refreshExpiryDate(),
    ]
  );
}

// POST /api/auth/login — verify credentials, issue access + refresh tokens.
const login = async (req, res) => {
  const { email, password } = req.body;
  const meta = requestMeta(req);

  try {
    const result = await pool.query("SELECT * FROM users WHERE email = $1", [
      email,
    ]);
    const user = result.rows[0];
    if (!user) {
      return res.status(401).json({ message: "Invalid email or password" });
    }
    if (user.is_active === false) {
      return res.status(403).json({ message: "Account is deactivated" });
    }
    if (user.is_verified === false) {
      return res.status(403).json({ message: "Account is not verified" });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: "Invalid email or password" });
    }

    const accessToken = signAccessToken(user);
    const refreshToken = signRefreshToken(user);
    await createSession(user, refreshToken, req);
    await writeAudit({ userId: user.id, action: "login", ...meta });

    res.json({ message: "Login successful", accessToken, refreshToken });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

// POST /api/auth/refresh — rotate the refresh token, revoking the old session.
const refresh = async (req, res) => {
  const { refreshToken } = req.body;
  const meta = requestMeta(req);

  let decoded;
  try {
    decoded = verifyRefreshToken(refreshToken);
  } catch (error) {
    return res.status(401).json({ message: "Invalid refresh token" });
  }

  try {
    const session = await pool.query(
      `SELECT * FROM sessions
       WHERE refresh_token_hash = $1 AND is_revoked = false AND expires_at > now()`,
      [hashToken(refreshToken)]
    );
    if (session.rows.length === 0) {
      return res.status(401).json({ message: "Invalid refresh token" });
    }

    await pool.query("UPDATE sessions SET is_revoked = true WHERE id = $1", [
      session.rows[0].id,
    ]);

    const userResult = await pool.query(
      "SELECT id, email, role FROM users WHERE id = $1",
      [decoded.id]
    );
    const user = userResult.rows[0];
    if (!user) {
      return res.status(401).json({ message: "Invalid refresh token" });
    }

    const newAccess = signAccessToken(user);
    const newRefresh = signRefreshToken(user);
    await createSession(user, newRefresh, req);
    await writeAudit({ userId: user.id, action: "refresh", ...meta });

    res.json({ accessToken: newAccess, refreshToken: newRefresh });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

// POST /api/auth/logout — revoke the session for the supplied refresh token.
const logout = async (req, res) => {
  const { refreshToken } = req.body;
  const meta = requestMeta(req);

  try {
    const result = await pool.query(
      `UPDATE sessions SET is_revoked = true
       WHERE refresh_token_hash = $1 AND is_revoked = false
       RETURNING user_id`,
      [hashToken(refreshToken)]
    );
    const userId = result.rows[0] ? result.rows[0].user_id : null;
    await writeAudit({ userId, action: "logout", ...meta });

    res.json({ message: "Logged out successfully" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

// POST /api/auth/logout-all — revoke every active session for the caller.
const logoutAll = async (req, res) => {
  const meta = requestMeta(req);

  try {
    await pool.query(
      "UPDATE sessions SET is_revoked = true WHERE user_id = $1 AND is_revoked = false",
      [req.user.id]
    );
    await writeAudit({ userId: req.user.id, action: "logout_all", ...meta });

    res.json({ message: "Logged out from all devices" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

module.exports = { login, refresh, logout, logoutAll };
