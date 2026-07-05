const calculateRisk = (comparisonResult) => {

    let score = 0;

    comparisonResult.mismatches.forEach((item) => {

        switch (item.field) {

            case "owner_name":
                score += 40;
                break;

            case "survey_no":
                score += 35;
                break;

            case "area_acres":
                score += 15;
                break;

            case "land_use":
                score += 10;
                break;

            default:
                score += 5;
        }

    });

    let riskLevel = "LOW";

    if (score >= 60) {
        riskLevel = "HIGH";
    } else if (score >= 25) {
        riskLevel = "MEDIUM";
    }

    return {
        risk_score: score,
        risk_level: riskLevel,
        verified: comparisonResult.verified
    };
};

module.exports = {
    calculateRisk
};