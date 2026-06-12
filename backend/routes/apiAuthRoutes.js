const express = require("express");
const router = express.Router();

const {
  register,
  verifyOtp,
  resendOtp,
} = require("../controllers/registrationController");

const {
  validate,
  apiRegisterValidation,
  verifyOtpValidation,
  resendOtpValidation,
} = require("../validators/apiAuthValidator");

// Registration + OTP (A-02/03)
router.post("/register", apiRegisterValidation, validate, register);
router.post("/verify-otp", verifyOtpValidation, validate, verifyOtp);
router.post("/resend-otp", resendOtpValidation, validate, resendOtp);

module.exports = router;
