const pool = require("../config/database");

const VALID_STATUSES = [
    "PENDING",
    "RUNNING",
    "PASSED",
    "FLAGGED",
    "FAILED",
    "SKIPPED"
];

const TERMINAL_STATUSES = [
    "PASSED",
    "FLAGGED",
    "FAILED",
    "SKIPPED"
];

const VALID_CHECK_TYPES = [
    "rtc",
    "pahani",
    "mutation",
    "village_map",
    "ec",
    "court",
    "hc",
    "sc",
    "bbmp",
    "bescom",
    "bwssb",
    "rera",
    "bda",
    "cctns"
];

/**
 * Validate verification payload
 */
function validateVerification(data) {
    if (!VALID_CHECK_TYPES.includes(data.check_type)) {
        throw new Error(`Invalid check type: ${data.check_type}`);
    }

    if (!VALID_STATUSES.includes(data.status)) {
        throw new Error(`Invalid verification status: ${data.status}`);
    }
}

/**
 * Get all verification records for a property
 */
async function getVerificationSummary(propertyId) {
    const result = await pool.query(
        `
        SELECT *
        FROM verification_status
        WHERE property_id = $1
        ORDER BY check_type
        `,
        [propertyId]
    );

    return result.rows;
}

/**
 * Check if a verification already exists
 */
async function getExistingVerification(propertyId, checkType) {
    const result = await pool.query(
        `
        SELECT *
        FROM verification_status
        WHERE property_id = $1
        AND check_type = $2
        `,
        [propertyId, checkType]
    );

    return result.rows[0];
}

/**
 * Create new verification record
 */
async function createVerification(data) {

    validateVerification(data);

    const result = await pool.query(
        `
        INSERT INTO verification_status
        (
            property_id,
            check_type,
            status,
            result_summary,
            flag_details,
            checked_at,
            source_url
        )
        VALUES
        ($1,$2,$3,$4,$5,NOW(),$6)
        RETURNING *
        `,
        [
            data.property_id,
            data.check_type,
            data.status,
            data.result_summary,
            data.flag_details,
            data.source_url
        ]
    );

    return result.rows[0];
}

/**
 * Update existing verification record
 */
async function updateVerification(data) {

    validateVerification(data);

    const existing = await getExistingVerification(
        data.property_id,
        data.check_type
    );

    if (!existing) {
        throw new Error("Verification record not found.");
    }

    // Skip duplicate updates
    if (
        existing.status === data.status &&
        existing.result_summary === data.result_summary &&
        JSON.stringify(existing.flag_details) === JSON.stringify(data.flag_details)
    ) {
        return existing;
    }

    const result = await pool.query(
        `
        UPDATE verification_status
        SET
            status = $3,
            result_summary = $4,
            flag_details = $5,
            checked_at = NOW(),
            source_url = $6
        WHERE
            property_id = $1
            AND check_type = $2
        RETURNING *
        `,
        [
            data.property_id,
            data.check_type,
            data.status,
            data.result_summary,
            data.flag_details,
            data.source_url
        ]
    );

    return result.rows[0];
}

/**
 * Check whether all verification checks have reached
 * a terminal state.
 */
async function areAllChecksTerminal(propertyId) {

    const result = await pool.query(
        `
        SELECT status
        FROM verification_status
        WHERE property_id = $1
        `,
        [propertyId]
    );

    if (result.rows.length === 0) {
        return false;
    }

    return result.rows.every(row =>
        TERMINAL_STATUSES.includes(row.status)
    );
}

module.exports = {
    getVerificationSummary,
    getExistingVerification,
    createVerification,
    updateVerification,
    areAllChecksTerminal
};