const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

// Storage driver: real S3 when AWS creds are present, otherwise a local-disk
// fallback so the upload/download pipeline is testable without AWS.
const DRIVER =
  process.env.STORAGE_DRIVER ||
  (process.env.AWS_ACCESS_KEY && process.env.AWS_SECRET_KEY ? "s3" : "local");

const BUCKET = process.env.S3_BUCKET;
const LOCAL_DIR = path.join(__dirname, "..", "..", ".local-storage");
const SIGN_SECRET = process.env.LOCAL_SIGN_SECRET || "dev-secret";

let s3 = null;
if (DRIVER === "s3") {
  const AWS = require("aws-sdk");
  s3 = new AWS.S3({
    accessKeyId: process.env.AWS_ACCESS_KEY,
    secretAccessKey: process.env.AWS_SECRET_KEY,
    region: process.env.AWS_REGION || "ap-south-1",
  });
}

async function putObject({ key, body, contentType }) {
  if (DRIVER === "s3") {
    await s3
      .putObject({
        Bucket: BUCKET,
        Key: key,
        Body: body,
        ContentType: contentType,
        ACL: "private",
      })
      .promise();
    return key;
  }
  const dest = path.join(LOCAL_DIR, key);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, body);
  return key;
}

// Returns { url, expiresAt }. S3 returns a real pre-signed URL; local mode
// returns an HMAC-signed, time-limited URL served by GET /api/documents/_local.
function getSignedUrl({ key, expiresSeconds = 900 }) {
  if (DRIVER === "s3") {
    const url = s3.getSignedUrl("getObject", {
      Bucket: BUCKET,
      Key: key,
      Expires: expiresSeconds,
    });
    return {
      url,
      expiresAt: new Date(Date.now() + expiresSeconds * 1000).toISOString(),
    };
  }
  const expires = Date.now() + expiresSeconds * 1000;
  const sig = crypto
    .createHmac("sha256", SIGN_SECRET)
    .update(`${key}:${expires}`)
    .digest("hex");
  const base =
    process.env.PUBLIC_BASE_URL || `http://localhost:${process.env.PORT || 3000}`;
  const url = `${base}/api/documents/_local?key=${encodeURIComponent(
    key
  )}&expires=${expires}&sig=${sig}`;
  return { url, expiresAt: new Date(expires).toISOString() };
}

// Validate a local signed URL and return the file path (local driver only).
function resolveLocal({ key, expires, sig }) {
  const expected = crypto
    .createHmac("sha256", SIGN_SECRET)
    .update(`${key}:${expires}`)
    .digest("hex");
  if (sig !== expected) return { ok: false, reason: "bad signature" };
  if (Date.now() > Number(expires)) return { ok: false, reason: "expired" };
  const filePath = path.join(LOCAL_DIR, key);
  if (!fs.existsSync(filePath)) return { ok: false, reason: "not found" };
  return { ok: true, filePath };
}

module.exports = { DRIVER, BUCKET, putObject, getSignedUrl, resolveLocal };
