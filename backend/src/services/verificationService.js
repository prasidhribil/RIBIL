const pool = require("../config/database");

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
 * Create a new verification record
 */
async function createVerification(data) {
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
 * Update an existing verification record
 */
async function updateVerification(data) {
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

module.exports = {
    getVerificationSummary,
    getExistingVerification,
    createVerification,
    updateVerification
};