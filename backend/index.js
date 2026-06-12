require("dotenv").config();

const express = require("express");
const helmet = require("helmet");

const auth = require("./middleware/auth");
const adminOnly = require("./middleware/admin");

const authRoutes = require("./routes/authRoutes");
const userRoutes = require("./routes/userRoutes");

const app = express();

// Hide Express fingerprint
app.disable("x-powered-by");

// Security Headers
app.use(helmet());

// Parse JSON
app.use(express.json({ limit: "10kb" }));

// Route Files
app.use("/", authRoutes);
app.use("/", userRoutes);

// Home Route
app.get("/", (req, res) => {
  res.send("Sprint 1 Ready");
});

// Profile Route
app.get("/profile", auth, (req, res) => {
  res.json({
    message: "Profile accessed successfully",
    user: req.user,
  });
});

// Current User Route
app.get("/me", auth, (req, res) => {
  res.json({
    id: req.user.id,
    email: req.user.email,
    role: req.user.role,
  });
});

// Admin Route
app.get("/admin", auth, adminOnly, (req, res) => {
  res.json({
    message: "Welcome Admin",
  });
});

// 404 Handler
app.use((req, res) => {
  res.status(404).json({
    message: "Route not found",
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error(err.stack);

  res.status(500).json({
    message: "Internal Server Error",
  });
});

const PORT = process.env.PORT || 3000;

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

module.exports = app;