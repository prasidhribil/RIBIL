const pool = require("../db");
const bcrypt = require("bcrypt");

const { generateOtp, hashOtp, otpExpiry } = require("../utils/otp");
const { sendOtpEmail } = require("../utils/mailer");
const { writeAudit, requestMeta } = require("../utils/audit");

const SALT_ROUNDS = 12;

// POST /api/auth/forgot-password — email a reset OTP. Always returns 200 to
// avoid leaking which emails are registered (account enumeration).
const forgotPassword = async (req, res) => {
  const { email } = req.body;
  const meta = requestMeta(req);

  try {
    const user = await pool.query("SELECT id FROM users WHERE email = $1", [
      email,
    ]);

    if (user.rows.length > 0) {
      await pool.query(
        `UPDATE otp_verifications SET is_used = true
         WHERE email = $1 AND type = 'reset_password' AND is_used = false`,
        [email]
      );

      const otp = generateOtp();
      await pool.query(
        `INSERT INTO otp_verifications (email, otp_hash, type, expires_at)
         VALUES ($1, $2, 'reset_password', $3)`,
        [email, hashOtp(otp), otpExpiry()]
      );

      await sendOtpEmail(email, otp, "reset_password");
      await writeAudit({
        userId: user.rows[0].id,
        action: "forgot_password",
        resource: email,
        ...meta,
      });
    }

    res.json({
      message: "If that email is registered, a reset code has been sent.",
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

// POST /api/auth/reset-password — validate the reset OTP, set a new password,
// and revoke every existing session for that user.
const resetPassword = async (req, res) => {
  const { email, otp, newPassword } = req.body;
  const meta = requestMeta(req);

  try {
    const result = await pool.query(
      `SELECT * FROM otp_verifications
       WHERE email = $1 AND type = 'reset_password' AND is_used = false AND expires_at > now()
       ORDER BY created_at DESC
       LIMIT 1`,
      [email]
    );

    const record = result.rows[0];
    if (!record || record.otp_hash !== hashOtp(otp)) {
      return res.status(400).json({ message: "Invalid or expired OTP" });
    }

    const hashedPassword = await bcrypt.hash(newPassword, SALT_ROUNDS);
    await pool.query(
      "UPDATE users SET password = $1, updated_at = now() WHERE email = $2",
      [hashedPassword, email]
    );
    await pool.query(
      "UPDATE otp_verifications SET is_used = true WHERE id = $1",
      [record.id]
    );
    await pool.query(
      `UPDATE sessions SET is_revoked = true
       WHERE user_id = (SELECT id FROM users WHERE email = $1)`,
      [email]
    );
    await writeAudit({ action: "reset_password", resource: email, ...meta });

    res.json({ message: "Password reset successfully" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

module.exports = { forgotPassword, resetPassword };
