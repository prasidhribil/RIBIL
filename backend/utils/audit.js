const pool = require("../db");

// Append-only audit trail. Audit failures must never break the request that
// triggered them, so errors are swallowed and logged.
async function writeAudit({
  userId = null,
  action,
  resource = null,
  ip = null,
  userAgent = null,
}) {
  try {
    await pool.query(
      `INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent)
       VALUES ($1, $2, $3, $4, $5)`,
      [userId, action, resource, ip, userAgent]
    );
  } catch (error) {
    console.error("audit log write failed:", error.message);
  }
}

// Pull request metadata used on every audit entry.
function requestMeta(req) {
  return { ip: req.ip, userAgent: req.headers["user-agent"] || null };
}

module.exports = { writeAudit, requestMeta };
