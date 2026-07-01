const express = require("express");
const router = express.Router();

const {
    updateVerificationStatus,
    getVerificationSummary
} = require("../controllers/verificationController");

// Update verification status
router.patch("/:id/status", updateVerificationStatus);

// Get verification summary
router.get("/:id/summary", getVerificationSummary);

module.exports = router;