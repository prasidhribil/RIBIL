const normalizeText = (value) => {
    if (!value) return "";
    return value
        .toString()
        .trim()
        .toLowerCase()
        .replace(/\s+/g, " ");
};

const compareNumbers = (a, b, tolerance = 0.01) => {
    return Math.abs(Number(a) - Number(b)) <= tolerance;
};

const comparePropertyData = (property, ocrData) => {

    const mismatches = [];

    // Owner Name
    if (
        property.owner_name &&
        ocrData.owner_name &&
        normalizeText(property.owner_name) !==
        normalizeText(ocrData.owner_name)
    ) {
        mismatches.push({
            field: "owner_name",
            property_value: property.owner_name,
            ocr_value: ocrData.owner_name,
            message: "Owner name mismatch"
        });
    }

    // Survey Number
    if (
        property.survey_no &&
        ocrData.survey_no &&
        normalizeText(property.survey_no) !==
        normalizeText(ocrData.survey_no)
    ) {
        mismatches.push({
            field: "survey_no",
            property_value: property.survey_no,
            ocr_value: ocrData.survey_no,
            message: "Survey number mismatch"
        });
    }

    // Area
    if (
        property.area_acres &&
        ocrData.area_acres &&
        !compareNumbers(
            property.area_acres,
            ocrData.area_acres
        )
    ) {
        mismatches.push({
            field: "area_acres",
            property_value: property.area_acres,
            ocr_value: ocrData.area_acres,
            message: "Area mismatch"
        });
    }

    // Land Use
    if (
        property.land_use &&
        ocrData.land_use &&
        normalizeText(property.land_use) !==
        normalizeText(ocrData.land_use)
    ) {
        mismatches.push({
            field: "land_use",
            property_value: property.land_use,
            ocr_value: ocrData.land_use,
            message: "Land use mismatch"
        });
    }

    return {
        verified: mismatches.length === 0,
        mismatch_count: mismatches.length,
        match_count: 4 - mismatches.length,
        confidence:
            mismatches.length === 0
                ? "HIGH"
                : mismatches.length <= 2
                ? "MEDIUM"
                : "LOW",
        mismatches
    };
};

module.exports = {
    comparePropertyData
};