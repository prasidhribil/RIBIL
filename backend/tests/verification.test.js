const request = require("supertest");
const app = require("../server");

describe("Verification API", () => {

    test("GET verification summary with invalid UUID", async () => {

        const response = await request(app)
            .get("/api/verify/invalid-id/summary");

        expect(response.status).toBe(400);
        expect(response.body.success).toBe(false);

    });

    test("PATCH verification without body", async () => {

        const response = await request(app)
            .patch("/api/verify/123e4567-e89b-12d3-a456-426614174000/status")
            .send({});

        expect(response.status).toBe(400);
        expect(response.body.success).toBe(false);

    });

});