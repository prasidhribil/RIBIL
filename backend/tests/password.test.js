jest.mock("../db", () => ({ query: jest.fn() }));
jest.mock("../utils/mailer", () => ({ sendOtpEmail: jest.fn().mockResolvedValue({ dev: true }) }));

const request = require("supertest");
const pool = require("../db");
const { hashOtp } = require("../utils/otp");
const app = require("../index");

beforeEach(() => {
  pool.query.mockReset();
});

describe("POST /api/auth/forgot-password", () => {
  test("200 even when the email is unknown (no enumeration)", async () => {
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app)
      .post("/api/auth/forgot-password")
      .send({ email: "ghost@example.com" });
    expect(res.status).toBe(200);
  });

  test("200 and issues a reset OTP for a known email", async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ id: 1 }] });
    const res = await request(app)
      .post("/api/auth/forgot-password")
      .send({ email: "jo@example.com" });
    expect(res.status).toBe(200);
  });
});

describe("POST /api/auth/reset-password", () => {
  test("400 when no valid reset OTP exists", async () => {
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app).post("/api/auth/reset-password").send({
      email: "jo@example.com",
      otp: "123456",
      newPassword: "N3w!Strong",
    });
    expect(res.status).toBe(400);
  });

  test("400 on wrong OTP", async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 7, otp_hash: hashOtp("123456") }],
    });
    const res = await request(app).post("/api/auth/reset-password").send({
      email: "jo@example.com",
      otp: "000000",
      newPassword: "N3w!Strong",
    });
    expect(res.status).toBe(400);
  });

  test("200 resets the password on a valid OTP", async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 7, otp_hash: hashOtp("123456") }],
    });
    const res = await request(app).post("/api/auth/reset-password").send({
      email: "jo@example.com",
      otp: "123456",
      newPassword: "N3w!Strong",
    });
    expect(res.status).toBe(200);
  });

  test("400 when the new password is weak", async () => {
    const res = await request(app).post("/api/auth/reset-password").send({
      email: "jo@example.com",
      otp: "123456",
      newPassword: "weak",
    });
    expect(res.status).toBe(400);
  });
});
