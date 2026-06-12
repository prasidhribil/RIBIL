const express = require("express");

const { authenticateToken, authorizeRole } = require("../middleware/auth");
const { uploadSingle } = require("../middleware/upload");
const {
  uploadDocument,
  listDocuments,
  downloadDocument,
  serveLocalFile,
} = require("../controllers/documentController");

const router = express.Router();

// Dev-only local file server for the local storage driver. Declared before the
// param routes so "_local" is not captured as a :property_id.
router.get("/_local", serveLocalFile);

router.post(
  "/upload",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  uploadSingle("document"),
  uploadDocument
);

router.get(
  "/:id/download",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  downloadDocument
);

router.get(
  "/:property_id",
  authenticateToken,
  authorizeRole("buyer", "agent", "admin"),
  listDocuments
);

module.exports = router;
