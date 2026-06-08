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
app.use(express.json());

// Debug middleware (temporary)
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);

  // Temporary header to verify middleware execution
  res.setHeader("X-JO-TEST", "WORKING");

  next();
});

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
<<<<<<< HEAD
// ME (Protected Route)
=======

// Current User Route
>>>>>>> 8faf37c90c243ee5906d0656d78f6df15183c885
app.get("/me", auth, (req, res) => {
  res.json({
    id: req.user.id,
    email: req.user.email,
<<<<<<< HEAD
  });
});
// USERS
app.get("/users", async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT id, name, email, created_at FROM users ORDER BY id"
    );
=======
    role: req.user.role,
  });
});
>>>>>>> 8faf37c90c243ee5906d0656d78f6df15183c885

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

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});