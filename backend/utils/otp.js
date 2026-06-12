const crypto = require("crypto");

const OTP_TTL_MINUTES = 10;

// 6-digit numeric OTP (100000–999999).
function generateOtp() {
  return crypto.randomInt(100000, 1000000).toString();
}

function hashOtp(otp) {
  return crypto.createHash("sha256").update(String(otp)).digest("hex");
}

function otpExpiry() {
  return new Date(Date.now() + OTP_TTL_MINUTES * 60 * 1000);
}

module.exports = { generateOtp, hashOtp, otpExpiry, OTP_TTL_MINUTES };
