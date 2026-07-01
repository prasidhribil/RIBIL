const express = require("express");

const { authenticateToken, authorizeRole } = require("../middleware/auth");
const { uploadSingle } = require("../middleware/upload");

const {
  uploadDocument,
  listDocuments,
  downloadDocument,
  serveLocalFile,
} = require("../controllers/documentController");

const { runOCR } = require("../controllers/ocrController");

const router = express.Router();

// Dev-only local file server
router.get("/_local", serveLocalFile);

// Upload document
router.post(
  "/upload",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  uploadSingle("document"),
  uploadDocument
);

// Run OCR on uploaded document (Sprint 2)
router.post(
  "/:id/ocr",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  runOCR
);

// Download document
router.get(
  "/:id/download",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  downloadDocument
);

// List documents for a property
router.get(
  "/:property_id",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  listDocuments
);

module.exports = router;