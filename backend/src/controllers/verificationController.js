function isUUID(value) {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}
const {
    getVerificationSummary,
    getExistingVerification,
    createVerification,
    updateVerification,
    areAllChecksTerminal
} = require("../services/verificationService");

// Allowed verification states
const VALID_STATES = [
    "PENDING",
    "RUNNING",
    "PASSED",
    "FAILED",
    "FLAGGED",
    "SKIPPED"
];

// Update verification status
const updateVerificationStatus = async (req, res) => {

    try {

        const { id } = req.params;

        if (!isUUID(id)) {
            return res.status(400).json({
                success: false,
                message: "Invalid property ID."
            });
        }

        let {
            check_type,
            status,
            result_summary,
            flag_details,
            source_url
        } = req.body;

        if (!check_type || !status) {
            return res.status(400).json({
                success: false,
                message: "check_type and status are required."
            });
        }

        // Normalize values
        check_type = check_type.toLowerCase();
        status = status.toUpperCase();

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

        const completed = await areAllChecksTerminal(id);

        return res.status(200).json({
            success: true,
            message: "Verification updated successfully.",
            all_checks_completed: completed,
            data: verification
        });

    } catch (error) {

        console.error(error);

        return res.status(500).json({
            success: false,
            message: error.message || "Internal Server Error"
        });

    }

};

// Get verification summary
const getVerificationSummaryController = async (req, res) => {

    try {

        const { id } = req.params;

        if (!isUUID(id)) {
            return res.status(400).json({
                success: false,
                message: "Invalid property ID."
            });
        }

        const checks = await getVerificationSummary(id);

        const completed = await areAllChecksTerminal(id);

        return res.status(200).json({
            success: true,
            property_id: id,
            total_checks: checks.length,
            all_checks_completed: completed,
            checks
        });

    } catch (error) {

        console.error(error);

        return res.status(500).json({
            success: false,
            message: error.message || "Internal Server Error"
        });

    }

};

module.exports = {
    updateVerificationStatus,
    getVerificationSummary: getVerificationSummaryController
};