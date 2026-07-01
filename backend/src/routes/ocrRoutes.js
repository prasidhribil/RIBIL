const express = require("express");
const router = express.Router();

const { runOCR } = require("../controllers/ocrController");

// Run OCR on a document
router.post("/:id/ocr", runOCR);

module.exports = router;