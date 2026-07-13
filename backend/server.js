require("dotenv").config();

const express = require("express");
const cors = require("cors");

const documentRoutes = require("./src/routes/documentRoutes");
const verificationRoutes = require("./src/routes/verificationRoutes");
const verificationEngineRoutes = require("./src/routes/verificationEngineRoutes");
const app = express();
// ======================
// Middleware
// ======================
app.use(cors());
app.use(express.json());
// ======================
// Health Check
// ======================
app.get("/health", (req, res) => {
    res.json({
        status: "ok",
        service: "RIBIL Backend",
        message: "Server is running"
    });
});
// ======================
// Existing Verification Start Endpoint
// ======================
app.get("/api/verification/start", (req, res) => {
    res.json({
        success: true,
        surveyNumber: "47/3",
        village: "Kadubeesanahalli",
        status: "Verification Started"
    });
});
// ======================
// Routes
// ======================

// Sprint 1
app.use("/api/documents", documentRoutes);
// Sprint 2
app.use("/api/verify", verificationRoutes);

// Sprint 3
app.use("/api/verification-engine", verificationEngineRoutes);

// ======================
// 404 Handler
// ======================
app.use((req, res) => {
    res.status(404).json({
        success: false,
        message: "API endpoint not found"
    });
});

// ======================
// Start Server
// ======================
const PORT = process.env.PORT || 3000;

if (require.main === module) {

    app.listen(PORT, () => {

        console.log(`🚀 RIBIL Backend running on port ${PORT}`);

    });

}

module.exports = app;