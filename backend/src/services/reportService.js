const generateReport = (
    property,
    ocrData,
    comparisonResult,
    riskResult
) => {

    const recommendations = [];

    if (riskResult.risk_level === "HIGH") {
        recommendations.push(
            "Manual verification is strongly recommended."
        );
    }

    if (riskResult.risk_level === "MEDIUM") {
        recommendations.push(
            "Review property records before approval."
        );
    }

    if (riskResult.risk_level === "LOW") {
        recommendations.push(
            "Property verification passed."
        );
    }

    return {
        generated_at: new Date(),

        property,

        ocr_data: ocrData,

        verification: comparisonResult,

        risk: riskResult,

        recommendations
    };
};

module.exports = {
    generateReport
};