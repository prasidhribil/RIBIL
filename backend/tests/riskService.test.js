const {
    calculateRisk
} = require("../src/services/riskService");

describe("Risk Service", () => {

    test("No mismatch should be LOW risk", () => {

        const result = calculateRisk({
            verified: true,
            mismatch_count: 0,
            mismatches: []
        });

        expect(result.risk_level).toBe("LOW");

    });

    test("Owner mismatch should be HIGH risk", () => {

        const result = calculateRisk({
            verified: false,
            mismatch_count: 1,
            mismatches: [
                {
                    field: "owner_name"
                }
            ]
        });

        expect(result.risk_level).toBe("MEDIUM");

    });

});