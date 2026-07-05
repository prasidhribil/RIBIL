const express = require("express");

const {
    runVerification
} = require("../controllers/verificationEngineController");

const router = express.Router();

// Run complete verification
router.post(
    "/:propertyId/run",
    runVerification
);

module.exports = router;