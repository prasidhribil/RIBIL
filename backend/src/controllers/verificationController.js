const {
    getVerificationSummary,
    getExistingVerification,
    createVerification,
    updateVerification
} = require("../services/verificationService");

// Allowed verification states
const VALID_STATES = [
    "pending",
    "running",
    "passed",
    "failed",
    "flagged",
    "skipped"
];

// Update verification status
const updateVerificationStatus = async (req, res) => {
    try {
        const { id } = req.params;

        const {
            check_type,
            status,
            result_summary,
            flag_details,
            source_url
        } = req.body;

        // Validate required fields
        if (!check_type || !status) {
            return res.status(400).json({
                success: false,
                message: "check_type and status are required."
            });
        }

        // Validate status
        if (!VALID_STATES.includes(status)) {
            return res.status(400).json({
                success: false,
                message: "Invalid verification status."
            });
        }

        let verification = await getExistingVerification(id, check_type);

        if (!verification) {
            verification = await createVerification({
                property_id: id,
                check_type,
                status,
                result_summary,
                flag_details,
                source_url
            });
        } else {
            verification = await updateVerification({
                property_id: id,
                check_type,
                status,
                result_summary,
                flag_details,
                source_url
            });
        }

        return res.status(200).json({
            success: true,
            message: "Verification updated successfully.",
            data: verification
        });

    } catch (error) {
        console.error(error);

        return res.status(500).json({
            success: false,
            message: "Internal Server Error"
        });
    }
};

// Get verification summary
const getVerificationSummaryController = async (req, res) => {
    try {

        const { id } = req.params;

        const checks = await getVerificationSummary(id);

        return res.status(200).json({
            success: true,
            property_id: id,
            total_checks: checks.length,
            checks
        });

    } catch (error) {

        console.error(error);

        return res.status(500).json({
            success: false,
            message: "Internal Server Error"
        });

    }
};

module.exports = {
    updateVerificationStatus,
    getVerificationSummary: getVerificationSummaryController
};