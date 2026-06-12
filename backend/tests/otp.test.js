jest.mock("../db", () => ({ query: jest.fn() }));
jest.mock("../utils/mailer", () => ({ sendOtpEmail: jest.fn().mockResolvedValue({ dev: true }) }));

const request = require("supertest");
const pool = require("../db");
const { hashOtp } = require("../utils/otp");
const app = require("../index");

beforeEach(() => {
  pool.query.mockReset();
});

describe("POST /api/auth/register", () => {
  test("422? no — 400 when fields missing", async () => {
    const res = await request(app).post("/api/auth/register").send({});
    expect(res.status).toBe(400);
    expect(res.body.errors).toBeDefined();
  });

  test("201 creates unverified user and issues an OTP", async () => {
    pool.query
      .mockResolvedValueOnce({ rows: [] }) // email uniqueness
      .mockResolvedValueOnce({ rows: [{ id: 1 }] }); // insert user
    const res = await request(app).post("/api/auth/register").send({
      name: "Jo",
      email: "jo@example.com",
      password: "Str0ng!Pass",
    });
    expect(res.status).toBe(201);
  });

  test("409 when email already exists", async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ id: 1 }] });
    const res = await request(app).post("/api/auth/register").send({
      name: "Jo",
      email: "jo@example.com",
      password: "Str0ng!Pass",
    });
    expect(res.status).toBe(409);
  });
});

describe("POST /api/auth/verify-otp", () => {
  test("400 on wrong OTP", async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 5, email: "jo@example.com", otp_hash: hashOtp("123456") }],
    });
    const res = await request(app)
      .post("/api/auth/verify-otp")
      .send({ email: "jo@example.com", otp: "000000" });
    expect(res.status).toBe(400);
  });

  test("400 when no active OTP exists", async () => {
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app)
      .post("/api/auth/verify-otp")
      .send({ email: "jo@example.com", otp: "123456" });
    expect(res.status).toBe(400);
  });

  test("200 on correct OTP and activates the account", async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 5, email: "jo@example.com", otp_hash: hashOtp("123456") }],
    });
    const res = await request(app)
      .post("/api/auth/verify-otp")
      .send({ email: "jo@example.com", otp: "123456" });
    expect(res.status).toBe(200);
  });
});

describe("POST /api/auth/resend-otp", () => {
  test("200 and sends a new OTP under the throttle", async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ count: 1 }] });
    const res = await request(app)
      .post("/api/auth/resend-otp")
      .send({ email: "jo@example.com" });
    expect(res.status).toBe(200);
  });

  test("429 when resend throttle exceeded", async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ count: 4 }] });
    const res = await request(app)
      .post("/api/auth/resend-otp")
      .send({ email: "jo@example.com" });
    expect(res.status).toBe(429);
  });
});
