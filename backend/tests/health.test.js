const request = require("supertest");
const app = require("../server");

describe("Health API", () => {

    test("GET /health should return server status", async () => {

        const response = await request(app).get("/health");

        expect(response.status).toBe(200);

        expect(response.body).toHaveProperty("status", "ok");
        expect(response.body).toHaveProperty("service", "RIBIL Backend");
        expect(response.body).toHaveProperty("message", "Server is running");

    });

});