const pool = require("../db");
const bcrypt = require("bcrypt");

const { generateOtp, hashOtp, otpExpiry } = require("../utils/otp");
const { sendOtpEmail } = require("../utils/mailer");
const { writeAudit, requestMeta } = require("../utils/audit");

const SALT_ROUNDS = 12;
const MAX_RESENDS_PER_HOUR = 3;

// POST /api/auth/register — create an unverified user and email a register OTP.
const register = async (req, res) => {
  const { name, email, password, phone, role } = req.body;
  const meta = requestMeta(req);

  try {
    const existing = await pool.query("SELECT id FROM users WHERE email = $1", [
      email,
    ]);
    if (existing.rows.length > 0) {
      return res.status(409).json({ message: "Email already exists" });
    }

    const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);

    const inserted = await pool.query(
      `INSERT INTO users (name, email, password, role, phone, is_verified)
       VALUES ($1, $2, $3, $4, $5, false)
       RETURNING id`,
      [name, email, hashedPassword, role || "user", phone || null]
    );
    const userId = inserted.rows[0].id;

    const otp = generateOtp();
    await pool.query(
      `INSERT INTO otp_verifications (email, otp_hash, type, expires_at)
       VALUES ($1, $2, 'register', $3)`,
      [email, hashOtp(otp), otpExpiry()]
    );

    await sendOtpEmail(email, otp, "register");
    await writeAudit({ userId, action: "register", resource: email, ...meta });

    res.status(201).json({
      message: "Registration successful. Verify the OTP sent to your email.",
    });
  } catch (error) {
    if (error.code === "23505") {
      return res.status(409).json({ message: "Email already exists" });
    }
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

// POST /api/auth/verify-otp — validate a register OTP and activate the account.
const verifyOtp = async (req, res) => {
  const { email, otp } = req.body;
  const meta = requestMeta(req);

  try {
    const result = await pool.query(
      `SELECT * FROM otp_verifications
       WHERE email = $1 AND type = 'register' AND is_used = false AND expires_at > now()
       ORDER BY created_at DESC
       LIMIT 1`,
      [email]
    );

    const record = result.rows[0];
    if (!record || record.otp_hash !== hashOtp(otp)) {
      return res.status(400).json({ message: "Invalid or expired OTP" });
    }

    await pool.query(
      "UPDATE users SET is_verified = true, updated_at = now() WHERE email = $1",
      [email]
    );
    await pool.query(
      "UPDATE otp_verifications SET is_used = true WHERE id = $1",
      [record.id]
    );
    await writeAudit({ action: "verify_otp", resource: email, ...meta });

    res.json({ message: "Account verified successfully" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

// POST /api/auth/resend-otp — invalidate prior OTPs and email a fresh one.
const resendOtp = async (req, res) => {
  const { email } = req.body;
  const meta = requestMeta(req);

  try {
    const counter = await pool.query(
      `SELECT COUNT(*)::int AS count FROM otp_verifications
       WHERE email = $1 AND type = 'register' AND created_at > now() - interval '1 hour'`,
      [email]
    );
    if (counter.rows[0].count > MAX_RESENDS_PER_HOUR) {
      return res
        .status(429)
        .json({ message: "Too many OTP requests. Try again later." });
    }

    await pool.query(
      `UPDATE otp_verifications SET is_used = true
       WHERE email = $1 AND type = 'register' AND is_used = false`,
      [email]
    );

    const otp = generateOtp();
    await pool.query(
      `INSERT INTO otp_verifications (email, otp_hash, type, expires_at)
       VALUES ($1, $2, 'register', $3)`,
      [email, hashOtp(otp), otpExpiry()]
    );

    await sendOtpEmail(email, otp, "register");
    await writeAudit({ action: "resend_otp", resource: email, ...meta });

    res.json({ message: "A new OTP has been sent." });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
};

module.exports = { register, verifyOtp, resendOtp };
