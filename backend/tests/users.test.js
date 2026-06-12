jest.mock("../db", () => ({ query: jest.fn() }));
jest.mock("../middleware/rateLimiter", () => ({
  loginLimiter: (req, res, next) => next(),
  registerLimiter: (req, res, next) => next(),
}));

const request = require("supertest");
const jwt = require("jsonwebtoken");
const pool = require("../db");
const app = require("../index");

const sign = (payload) => jwt.sign(payload, process.env.JWT_SECRET);
const USER_ID = "11111111-1111-4111-8111-111111111111";
const OTHER_ID = "22222222-2222-4222-8222-222222222222";
const ADMIN_ID = "99999999-9999-4999-8999-999999999999";
const MISSING_ID = "33333333-3333-4333-8333-333333333333";
const userToken = sign({ id: USER_ID, email: "u@example.com", role: "buyer" });
const adminToken = sign({ id: ADMIN_ID, email: "a@example.com", role: "admin" });

beforeEach(() => {
  pool.query.mockReset();
});

describe("protected routes & RBAC", () => {
  test("401 without token on /me", async () => {
    const res = await request(app).get("/me");
    expect(res.status).toBe(401);
  });

  test("401 with invalid token", async () => {
    const res = await request(app)
      .get("/me")
      .set("Authorization", "Bearer garbage");
    expect(res.status).toBe(401);
  });

  test("200 on /me with valid token", async () => {
    const res = await request(app)
      .get("/me")
      .set("Authorization", `Bearer ${userToken}`);
    expect(res.status).toBe(200);
    expect(res.body.role).toBe("buyer");
  });

  test("403 on /admin for non-admin", async () => {
    const res = await request(app)
      .get("/admin")
      .set("Authorization", `Bearer ${userToken}`);
    expect(res.status).toBe(403);
  });

  test("200 on /admin for admin", async () => {
    const res = await request(app)
      .get("/admin")
      .set("Authorization", `Bearer ${adminToken}`);
    expect(res.status).toBe(200);
  });
});

describe("GET /users", () => {
  test("403 for non-admin", async () => {
    const res = await request(app)
      .get("/users")
      .set("Authorization", `Bearer ${userToken}`);
    expect(res.status).toBe(403);
  });

  test("200 for admin", async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 1, name: "U", email: "u@example.com", role: "user" }],
    });
    const res = await request(app)
      .get("/users")
      .set("Authorization", `Bearer ${adminToken}`);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });
});

describe("PUT /users/:id", () => {
  test("400 for a non-UUID id", async () => {
    const res = await request(app)
      .put("/users/abc")
      .set("Authorization", `Bearer ${userToken}`)
      .send({ name: "X", email: "x@example.com" });
    expect(res.status).toBe(400);
  });

  test("403 when updating another user as non-admin", async () => {
    const res = await request(app)
      .put(`/users/${OTHER_ID}`)
      .set("Authorization", `Bearer ${userToken}`)
      .send({ name: "X", email: "x@example.com" });
    expect(res.status).toBe(403);
  });

  test("200 when owner updates own record", async () => {
    pool.query
      .mockResolvedValueOnce({ rows: [] }) // email uniqueness check
      .mockResolvedValueOnce({
        rows: [{ id: USER_ID, name: "X", email: "x@example.com", role: "buyer" }],
      });
    const res = await request(app)
      .put(`/users/${USER_ID}`)
      .set("Authorization", `Bearer ${userToken}`)
      .send({ name: "X", email: "x@example.com" });
    expect(res.status).toBe(200);
    expect(res.body.user.id).toBe(USER_ID);
  });
});

describe("DELETE /users/:id", () => {
  test("200 when owner deletes own record", async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ id: USER_ID }] });
    const res = await request(app)
      .delete(`/users/${USER_ID}`)
      .set("Authorization", `Bearer ${userToken}`);
    expect(res.status).toBe(200);
  });

  test("404 when admin deletes a missing user", async () => {
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app)
      .delete(`/admin/users/${MISSING_ID}`)
      .set("Authorization", `Bearer ${adminToken}`);
    expect(res.status).toBe(404);
  });
});
