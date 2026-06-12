const express = require("express");
const router = express.Router();

const auth = require("../middleware/auth");

const {
  register,
  verifyOtp,
  resendOtp,
} = require("../controllers/registrationController");

const {
  login,
  refresh,
  logout,
  logoutAll,
} = require("../controllers/sessionController");

const {
  validate,
  apiRegisterValidation,
  apiLoginValidation,
  verifyOtpValidation,
  resendOtpValidation,
  refreshValidation,
  logoutValidation,
} = require("../validators/apiAuthValidator");

// Registration + OTP (A-02/03)
router.post("/register", apiRegisterValidation, validate, register);
router.post("/verify-otp", verifyOtpValidation, validate, verifyOtp);
router.post("/resend-otp", resendOtpValidation, validate, resendOtp);

// Login, token rotation + logout (A-04/05/06)
router.post("/login", apiLoginValidation, validate, login);
router.post("/refresh", refreshValidation, validate, refresh);
router.post("/logout", logoutValidation, validate, logout);
router.post("/logout-all", auth, logoutAll);

module.exports = router;
