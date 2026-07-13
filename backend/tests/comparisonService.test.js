const {
    comparePropertyData
} = require("../src/services/comparisonService");

describe("Comparison Service", () => {

    test("Matching property data should verify successfully", () => {

        const property = {
            owner_name: "John Doe",
            survey_no: "47/3",
            area_acres: 2.35,
            land_use: "Residential"
        };

        const ocr = {
            owner_name: "John Doe",
            survey_no: "47/3",
            area_acres: 2.35,
            land_use: "Residential"
        };

        const result = comparePropertyData(property, ocr);

        expect(result.verified).toBe(true);
        expect(result.mismatch_count).toBe(0);

    });

    test("Different owner should create mismatch", () => {

        const property = {
            owner_name: "John Doe"
        };

        const ocr = {
            owner_name: "Jane Doe"
        };

        const result = comparePropertyData(property, ocr);

        expect(result.verified).toBe(false);
        expect(result.mismatch_count).toBe(1);

    });

});