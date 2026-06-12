jest.mock("../db", () => ({ query: jest.fn() }));
jest.mock("../middleware/rateLimiter", () => ({
  loginLimiter: (req, res, next) => next(),
  registerLimiter: (req, res, next) => next(),
}));

const request = require("supertest");
const bcrypt = require("bcrypt");
const pool = require("../db");
const app = require("../index");

const validUser = {
  name: "Jo",
  email: "jo@example.com",
  password: "Str0ng!Pass",
};

beforeEach(() => {
  pool.query.mockReset();
});

describe("POST /register", () => {
  test("400 when fields are missing", async () => {
    const res = await request(app).post("/register").send({});
    expect(res.status).toBe(400);
    expect(res.body.errors).toBeDefined();
  });

  test("400 when password is weak", async () => {
    const res = await request(app)
      .post("/register")
      .send({ ...validUser, password: "weak" });
    expect(res.status).toBe(400);
  });

  test("201 on successful registration", async () => {
    pool.query
      .mockResolvedValueOnce({ rows: [] }) // existing email check
      .mockResolvedValueOnce({ rows: [] }); // insert
    const res = await request(app).post("/register").send(validUser);
    expect(res.status).toBe(201);
    expect(res.body.message).toMatch(/successful/i);
  });

  test("409 when email already exists", async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ id: 1 }] });
    const res = await request(app).post("/register").send(validUser);
    expect(res.status).toBe(409);
  });
});

describe("POST /login", () => {
  test("400 when email is invalid", async () => {
    const res = await request(app)
      .post("/login")
      .send({ email: "nope", password: "x" });
    expect(res.status).toBe(400);
  });

  test("400 when password is missing", async () => {
    const res = await request(app)
      .post("/login")
      .send({ email: "jo@example.com" });
    expect(res.status).toBe(400);
  });

  test("401 for unknown email", async () => {
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app)
      .post("/login")
      .send({ email: "jo@example.com", password: "Str0ng!Pass" });
    expect(res.status).toBe(401);
  });

  test("401 for wrong password", async () => {
    const hash = await bcrypt.hash("Str0ng!Pass", 10);
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 1, email: "jo@example.com", role: "user", password: hash }],
    });
    const res = await request(app)
      .post("/login")
      .send({ email: "jo@example.com", password: "WrongPass1!" });
    expect(res.status).toBe(401);
  });

  test("200 and token on valid credentials", async () => {
    const hash = await bcrypt.hash("Str0ng!Pass", 10);
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 1, email: "jo@example.com", role: "user", password: hash }],
    });
    const res = await request(app)
      .post("/login")
      .send({ email: "jo@example.com", password: "Str0ng!Pass" });
    expect(res.status).toBe(200);
    expect(res.body.token).toBeDefined();
  });
});
