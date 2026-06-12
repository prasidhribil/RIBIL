jest.mock("../db", () => ({ query: jest.fn().mockResolvedValue({ rows: [] }) }));

const request = require("supertest");
const app = require("../index");

describe("rate limiting", () => {
  test("login returns 429 after exceeding the limit", async () => {
    const body = { email: "jo@example.com", password: "Str0ng!Pass" };
    let last;
    for (let i = 0; i < 6; i++) {
      last = await request(app).post("/login").send(body);
    }
    expect(last.status).toBe(429);
  });
});
