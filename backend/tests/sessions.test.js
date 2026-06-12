jest.mock("../db", () => ({ query: jest.fn() }));

const request = require("supertest");
const bcrypt = require("bcrypt");
const pool = require("../db");
const {
  signAccessToken,
  signRefreshToken,
  hashToken,
} = require("../utils/tokens");
const app = require("../index");

const verifiedUser = (hash) => ({
  id: 1,
  email: "jo@example.com",
  role: "buyer",
  password: hash,
  is_verified: true,
  is_active: true,
});

beforeEach(() => {
  pool.query.mockReset();
});

describe("POST /api/auth/login", () => {
  test("200 returns access + refresh tokens for a verified user", async () => {
    const hash = await bcrypt.hash("Str0ng!Pass", 10);
    pool.query.mockResolvedValueOnce({ rows: [verifiedUser(hash)] });
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "jo@example.com", password: "Str0ng!Pass" });
    expect(res.status).toBe(200);
    expect(res.body.accessToken).toBeDefined();
    expect(res.body.refreshToken).toBeDefined();
  });

  test("403 when account is not verified", async () => {
    const hash = await bcrypt.hash("Str0ng!Pass", 10);
    pool.query.mockResolvedValueOnce({
      rows: [{ ...verifiedUser(hash), is_verified: false }],
    });
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "jo@example.com", password: "Str0ng!Pass" });
    expect(res.status).toBe(403);
  });

  test("401 on wrong password", async () => {
    const hash = await bcrypt.hash("Str0ng!Pass", 10);
    pool.query.mockResolvedValueOnce({ rows: [verifiedUser(hash)] });
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "jo@example.com", password: "WrongPass1!" });
    expect(res.status).toBe(401);
  });
});

describe("POST /api/auth/refresh", () => {
  test("200 rotates and returns a new token pair", async () => {
    const token = signRefreshToken({ id: 1 });
    pool.query
      .mockResolvedValueOnce({ rows: [{ id: 9, user_id: 1 }] }) // active session lookup
      .mockResolvedValueOnce({}) // revoke old session
      .mockResolvedValueOnce({ rows: [{ id: 1, email: "jo@example.com", role: "buyer" }] }); // user
    const res = await request(app)
      .post("/api/auth/refresh")
      .send({ refreshToken: token });
    expect(res.status).toBe(200);
    expect(res.body.accessToken).toBeDefined();
    expect(res.body.refreshToken).toBeDefined();
  });

  test("401 when refresh token is not a valid JWT", async () => {
    const res = await request(app)
      .post("/api/auth/refresh")
      .send({ refreshToken: "garbage.token.value" });
    expect(res.status).toBe(401);
  });

  test("401 when session is revoked / not found", async () => {
    const token = signRefreshToken({ id: 1 });
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app)
      .post("/api/auth/refresh")
      .send({ refreshToken: token });
    expect(res.status).toBe(401);
  });

  test("401 when an access token is used in place of a refresh token", async () => {
    const access = signAccessToken({ id: 1, email: "jo@example.com", role: "buyer" });
    const res = await request(app)
      .post("/api/auth/refresh")
      .send({ refreshToken: access });
    expect(res.status).toBe(401);
  });
});

describe("POST /api/auth/logout", () => {
  test("200 revokes the matching session", async () => {
    const token = signRefreshToken({ id: 1 });
    pool.query.mockResolvedValueOnce({ rows: [{ user_id: 1 }] });
    const res = await request(app)
      .post("/api/auth/logout")
      .send({ refreshToken: token });
    expect(res.status).toBe(200);
    expect(pool.query).toHaveBeenCalledWith(
      expect.stringContaining("UPDATE sessions SET is_revoked = true"),
      [hashToken(token)]
    );
  });
});

describe("POST /api/auth/logout-all", () => {
  test("401 without an access token", async () => {
    const res = await request(app).post("/api/auth/logout-all").send({});
    expect(res.status).toBe(401);
  });

  test("200 revokes all sessions for the authenticated user", async () => {
    const access = signAccessToken({ id: 1, email: "jo@example.com", role: "buyer" });
    pool.query.mockResolvedValue({});
    const res = await request(app)
      .post("/api/auth/logout-all")
      .set("Authorization", `Bearer ${access}`)
      .send({});
    expect(res.status).toBe(200);
  });
});
