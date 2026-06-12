const nodemailer = require("nodemailer");

// Build a transporter from SMTP env vars (e.g. SendGrid SMTP). When none are
// configured (local/dev/test), fall back to logging the OTP to the console so
// the flow is never blocked on real email delivery.
let cachedTransporter;

function getTransporter() {
  if (cachedTransporter !== undefined) return cachedTransporter;

  if (process.env.SMTP_HOST) {
    cachedTransporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: Number(process.env.SMTP_PORT) || 587,
      auth:
        process.env.SMTP_USER && process.env.SMTP_PASS
          ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
          : undefined,
    });
  } else {
    cachedTransporter = null;
  }

  return cachedTransporter;
}

const SUBJECTS = {
  register: "Verify your RIBIL account",
  reset_password: "Reset your RIBIL password",
};

function htmlBody(otp, type) {
  const heading =
    type === "reset_password" ? "Password reset code" : "Account verification code";
  return `
    <div style="font-family: Arial, sans-serif">
      <h2>${heading}</h2>
      <p>Your one-time code is:</p>
      <p style="font-size: 28px; font-weight: bold; letter-spacing: 4px">${otp}</p>
      <p>This code expires in 10 minutes. Do not share it with anyone.</p>
    </div>`;
}

async function sendOtpEmail(to, otp, type) {
  const transporter = getTransporter();

  if (!transporter) {
    // Dev fallback — no SMTP configured.
    console.log(`[mailer:dev] ${type} OTP for ${to}: ${otp}`);
    return { delivered: false, dev: true };
  }

  await transporter.sendMail({
    from: process.env.MAIL_FROM || "no-reply@ribil.local",
    to,
    subject: SUBJECTS[type] || "Your RIBIL code",
    html: htmlBody(otp, type),
  });

  return { delivered: true };
}

module.exports = { sendOtpEmail };
