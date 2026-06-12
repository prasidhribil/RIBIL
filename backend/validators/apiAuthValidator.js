const { body } = require("express-validator");
const { validate } = require("./authValidator");

const strongPassword = (field) =>
  body(field)
    .isLength({ min: 8 })
    .withMessage("Password must be at least 8 characters")
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])/)
    .withMessage(
      "Password must contain uppercase, lowercase, number and special character"
    );

const emailField = body("email")
  .isEmail()
  .withMessage("Valid email is required")
  .normalizeEmail();

const otpField = body("otp")
  .isLength({ min: 6, max: 6 })
  .withMessage("OTP must be 6 digits")
  .isNumeric()
  .withMessage("OTP must be numeric");

const apiRegisterValidation = [
  body("name").trim().notEmpty().withMessage("Name is required"),
  emailField,
  strongPassword("password"),
  body("phone")
    .optional()
    .matches(/^[6-9]\d{9}$/)
    .withMessage("Phone must be a valid 10-digit Indian number"),
  body("role")
    .optional()
    .isIn(["buyer", "seller"])
    .withMessage("Role must be buyer or seller"),
];

const apiLoginValidation = [
  emailField,
  body("password").notEmpty().withMessage("Password is required"),
];

const verifyOtpValidation = [emailField, otpField];

const resendOtpValidation = [emailField];

const refreshValidation = [
  body("refreshToken").notEmpty().withMessage("Refresh token is required"),
];

const logoutValidation = [
  body("refreshToken").notEmpty().withMessage("Refresh token is required"),
];

const forgotPasswordValidation = [emailField];

const resetPasswordValidation = [
  emailField,
  otpField,
  strongPassword("newPassword"),
];

module.exports = {
  validate,
  apiRegisterValidation,
  apiLoginValidation,
  verifyOtpValidation,
  resendOtpValidation,
  refreshValidation,
  logoutValidation,
  forgotPasswordValidation,
  resetPasswordValidation,
};
