const fs = require("fs");
const path = require("path");
const { randomUUID } = require("crypto");
const mime = require("mime-types");

const pool = require("../config/database");
const storage = require("../config/storage");
const { scanBuffer } = require("../services/virusScan");
const { classifyDocument } = require("../services/classifier");

// Best-effort audit log. audit_logs is owned by Member 1 (auth); if the table
// does not exist yet we silently skip rather than failing the request.
async function audit(action, userId, meta) {
  try {
    await pool.query(
      `INSERT INTO audit_logs (user_id, action, metadata) VALUES ($1, $2, $3::jsonb)`,
      [userId, action, JSON.stringify(meta || {})]
    );
  } catch (err) {
    if (err.code !== "42P01") {
      console.warn("[audit] failed:", err.message);
    }
  }
}

function extFor(file) {
  const fromName = path.extname(file.originalname).replace(".", "").toLowerCase();
  return fromName || mime.extension(file.mimetype) || "bin";
}

// POST /api/documents/upload  (field: "document", body: { property_id })
async function uploadDocument(req, res) {
  try {
    if (!req.file) {
      return res
        .status(400)
        .json({ error: { code: "NO_FILE", message: "No file in 'document' field" } });
    }
    const propertyId = req.body.property_id;
    if (!propertyId) {
      return res
        .status(400)
        .json({ error: { code: "MISSING_PROPERTY_ID", message: "property_id is required" } });
    }

    const property = await pool.query("SELECT id FROM properties WHERE id = $1", [propertyId]);
    if (property.rowCount === 0) {
      return res
        .status(404)
        .json({ error: { code: "PROPERTY_NOT_FOUND", message: "Unknown property_id" } });
    }

    const scan = await scanBuffer(req.file.buffer);
    if (scan.infected) {
      return res
        .status(422)
        .json({ error: { code: "INFECTED_FILE", message: "File failed virus scan" } });
    }

    const key = `documents/${propertyId}/${randomUUID()}.${extFor(req.file)}`;
    await storage.putObject({
      key,
      body: req.file.buffer,
      contentType: req.file.mimetype,
    });

    const insert = await pool.query(
      `INSERT INTO property_documents
        (property_id, source, s3_key, filename, file_size_bytes, mime_type, uploaded_at)
       VALUES ($1, 'uploaded', $2, $3, $4, $5, NOW())
       RETURNING *`,
      [propertyId, key, req.file.originalname, req.file.size, req.file.mimetype]
    );
    const doc = insert.rows[0];

    await audit("document.upload", req.user && req.user.id, { document_id: doc.id, key });

    // Async classification — never blocks the upload response.
    classifyDocument("")
      .then((result) =>
        pool.query("UPDATE property_documents SET doc_type = $1 WHERE id = $2", [
          result.predicted_class || "other",
          doc.id,
        ])
      )
      .catch((err) => console.warn("[classify] update failed:", err.message));

    return res.status(201).json({ document: doc, scanner: scan.scanner });
  } catch (err) {
    console.error("[uploadDocument]", err);
    return res
      .status(500)
      .json({ error: { code: "UPLOAD_FAILED", message: err.message } });
  }
}

// GET /api/documents/:property_id  — role-gated document list
async function listDocuments(req, res) {
  try {
    const result = await pool.query(
      `SELECT id, property_id, doc_type, source, s3_key, filename, file_size_bytes,
              mime_type, version_no, is_latest, scraped_at, uploaded_at
       FROM property_documents
       WHERE property_id = $1
       ORDER BY uploaded_at DESC`,
      [req.params.property_id]
    );
    return res.json({ documents: result.rows });
  } catch (err) {
    console.error("[listDocuments]", err);
    return res
      .status(500)
      .json({ error: { code: "LIST_FAILED", message: err.message } });
  }
}

// GET /api/documents/:id/download — pre-signed URL (15-min expiry)
async function downloadDocument(req, res) {
  try {
    const result = await pool.query(
      "SELECT id, s3_key FROM property_documents WHERE id = $1",
      [req.params.id]
    );
    if (result.rowCount === 0) {
      return res
        .status(404)
        .json({ error: { code: "DOCUMENT_NOT_FOUND", message: "Unknown document id" } });
    }
    const { url, expiresAt } = storage.getSignedUrl({
      key: result.rows[0].s3_key,
      expiresSeconds: 900,
    });
    await audit("document.download", req.user && req.user.id, {
      document_id: result.rows[0].id,
    });
    return res.json({ download_url: url, expires_at: expiresAt });
  } catch (err) {
    console.error("[downloadDocument]", err);
    return res
      .status(500)
      .json({ error: { code: "DOWNLOAD_FAILED", message: err.message } });
  }
}

// GET /api/documents/_local — dev-only handler that serves local-driver files
// behind the HMAC-signed URL produced by storage.getSignedUrl.
function serveLocalFile(req, res) {
  if (storage.DRIVER !== "local") {
    return res.status(404).json({ error: { code: "NOT_FOUND" } });
  }
  const { key, expires, sig } = req.query;
  const resolved = storage.resolveLocal({ key, expires, sig });
  if (!resolved.ok) {
    return res
      .status(403)
      .json({ error: { code: "INVALID_OR_EXPIRED_URL", message: resolved.reason } });
  }
  // Stream directly (res.sendFile ignores the dotfile ".local-storage" path).
  res.setHeader("Content-Type", mime.lookup(resolved.filePath) || "application/octet-stream");
  return fs.createReadStream(resolved.filePath).pipe(res);
}

module.exports = {
  uploadDocument,
  listDocuments,
  downloadDocument,
  serveLocalFile,
};
