const comparePropertyData = (property, ocrData) => {
    const mismatches = [];

    // Owner comparison
    if (
        property.owner_name &&
        ocrData.owner_name &&
        property.owner_name.trim().toLowerCase() !==
        ocrData.owner_name.trim().toLowerCase()
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
        property.survey_no !== ocrData.survey_no
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
        Number(property.area_acres) !== Number(ocrData.area_acres)
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
        property.land_use !== ocrData.land_use
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
        mismatches
    };
};

module.exports = {
    comparePropertyData
};