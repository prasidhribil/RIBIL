const express = require("express");

const auth = require("./middleware/auth");
const adminOnly = require("./middleware/admin");

const authRoutes = require("./routes/authRoutes");
const userRoutes = require("./routes/userRoutes");

const app = express();

app.use(express.json());

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

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});