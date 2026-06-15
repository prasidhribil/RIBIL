const express = require("express");

const router = express.Router();

router.get("/digilocker/initiate", (req, res) => {
  res.json({
    message: "DigiLocker OAuth initiation placeholder",
  });
});

router.get("/digilocker/callback", (req, res) => {
  res.json({
    message: "DigiLocker OAuth callback placeholder",
  });
});

module.exports = router;