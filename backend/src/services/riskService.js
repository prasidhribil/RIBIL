const calculateRisk = (comparisonResult) => {

    let score = 0;
    const riskFactors = [];

    comparisonResult.mismatches.forEach((item) => {

        switch (item.field) {

            case "owner_name":
                score += 40;
                riskFactors.push("Owner name mismatch");
                break;

            case "survey_no":
                score += 35;
                riskFactors.push("Survey number mismatch");
                break;

            case "area_acres":
                score += 15;
                riskFactors.push("Area mismatch");
                break;

            case "land_use":
                score += 10;
                riskFactors.push("Land use mismatch");
                break;

            default:
                score += 5;
                riskFactors.push(item.field);
        }

    });

    // Clamp score
    score = Math.min(score, 100);

    let riskLevel = "LOW";

    if (score >= 60) {
        riskLevel = "HIGH";
    } else if (score >= 25) {
        riskLevel = "MEDIUM";
    }

    const recommendation =
        riskLevel === "HIGH"
            ? "Manual verification required before approval."
            : riskLevel === "MEDIUM"
            ? "Review mismatched fields before approval."
            : "Property verification passed.";

    return {
        verified: comparisonResult.verified,
        risk_score: score,
        risk_level: riskLevel,
        mismatch_count: comparisonResult.mismatch_count,
        risk_factors: riskFactors,
        recommendation
    };
};

module.exports = {
    calculateRisk
};