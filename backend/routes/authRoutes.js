const express = require("express");
const router = express.Router();

const {
  register,
  login,
} = require("../controllers/authController");

const {
  registerValidation,
  loginValidation,
  validate,
} = require("../validators/authValidator");

const {
  loginLimiter,
  registerLimiter,
} = require("../middleware/rateLimiter");

router.post(
  "/register",
  registerLimiter,
  registerValidation,
  validate,
  register
);

router.post(
  "/login",
  loginLimiter,
  loginValidation,
  validate,
  login
);

module.exports = router;
