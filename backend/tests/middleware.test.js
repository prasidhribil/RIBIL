const express = require("express");
const request = require("supertest");
const jwt = require("jsonwebtoken");

const auth = require("../middleware/auth");
const authorizeRole = require("../middleware/authorizeRole");

const SECRET = process.env.JWT_SECRET;

// Minimal app exercising the auth + authorizeRole middleware in isolation.
const app = express();
app.get("/protected", auth, (req, res) => res.json({ user: req.user }));
app.get("/admin-only", auth, authorizeRole("admin"), (req, res) =>
  res.json({ ok: true })
);

const sign = (payload, opts = {}) => jwt.sign(payload, SECRET, opts);

describe("authenticateToken middleware", () => {
  test("no token → 401 MISSING_TOKEN", async () => {
    const res = await request(app).get("/protected");
    expect(res.status).toBe(401);
    expect(res.body.code).toBe("MISSING_TOKEN");
  });

  test("expired token → 401 TOKEN_EXPIRED", async () => {
    const token = sign({ id: 1, role: "buyer" }, { expiresIn: "-10s" });
    const res = await request(app)
      .get("/protected")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(401);
    expect(res.body.code).toBe("TOKEN_EXPIRED");
  });

  test("tampered token → 401 INVALID_TOKEN", async () => {
    const token = sign({ id: 1, role: "buyer" });
    const tampered = token.slice(0, -2) + (token.endsWith("a") ? "bb" : "aa");
    const res = await request(app)
      .get("/protected")
      .set("Authorization", `Bearer ${tampered}`);
    expect(res.status).toBe(401);
    expect(res.body.code).toBe("INVALID_TOKEN");
  });

  test("valid buyer token → 200 and req.user populated", async () => {
    const token = sign({ id: 1, role: "buyer", email: "b@example.com" });
    const res = await request(app)
      .get("/protected")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.user.role).toBe("buyer");
  });
});

describe("authorizeRole middleware", () => {
  test("buyer on admin route → 403 FORBIDDEN", async () => {
    const token = sign({ id: 1, role: "buyer" });
    const res = await request(app)
      .get("/admin-only")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(403);
    expect(res.body.error.code).toBe("FORBIDDEN");
  });

  test("admin on admin route → 200", async () => {
    const token = sign({ id: 2, role: "admin" });
    const res = await request(app)
      .get("/admin-only")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
  });
});
