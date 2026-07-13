const pool = require("../config/database");

const {
    comparePropertyData
} = require("../services/comparisonService");

const {
    calculateRisk
} = require("../services/riskService");

const {
    generateReport
} = require("../services/reportService");

const {
    saveReport
} = require("../services/storageReportService");

const {
    areAllChecksTerminal
} = require("../services/verificationService");

const runVerification = async (req, res) => {

    try {

        const { propertyId } = req.params;

        // Verify that all verification checks have completed
        const completed = await areAllChecksTerminal(propertyId);

        if (!completed) {
            return res.status(409).json({
                success: false,
                message: "Verification pipeline is still running. Report cannot be generated yet."
            });
        }

        // Fetch Property
        const propertyResult = await pool.query(
            `
            SELECT *
            FROM properties
            WHERE id = $1
            `,
            [propertyId]
        );

        if (propertyResult.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: "Property not found."
            });
        }

        const property = propertyResult.rows[0];

        // Fetch latest OCR extraction
        const ocrResult = await pool.query(
            `
            SELECT *
            FROM doc_ocr_extracts
            WHERE document_id IN
            (
                SELECT id
                FROM property_documents
                WHERE property_id = $1
                ORDER BY uploaded_at DESC
                LIMIT 1
            )
            ORDER BY extracted_at DESC
            LIMIT 1
            `,
            [propertyId]
        );

        if (ocrResult.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: "No OCR data found."
            });
        }

        const ocrData = ocrResult.rows[0];

        // Compare OCR with property data
        const comparisonResult =
            comparePropertyData(property, ocrData);

        // Calculate risk
        const riskResult =
            calculateRisk(comparisonResult);

        // Generate verification report
        const report =
            generateReport(
                property,
                ocrData,
                comparisonResult,
                riskResult
            );

        // Save report
        const storage =
            await saveReport(propertyId, report);

        // Store metadata
        await pool.query(
            `
            INSERT INTO verification_reports
            (
                property_id,
                risk_score,
                risk_level,
                s3_key,
                download_url,
                url_expires_at
            )
            VALUES
            (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6
            )
            `,
            [
                propertyId,
                riskResult.risk_score,
                riskResult.risk_level,
                storage.s3_key,
                storage.download_url,
                storage.url_expires_at
            ]
        );

        return res.status(200).json({
            success: true,
            report,
            storage
        });

    } catch (error) {

        console.error(error);

        return res.status(500).json({
            success: false,
            message: error.message
        });

    }

};

module.exports = {
    runVerification
};