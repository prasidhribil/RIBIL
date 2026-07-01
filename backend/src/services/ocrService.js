const pool = require("../config/database");

/**
 * Simulated OCR extraction service
 * (Replace later with Tesseract, Google Vision, AWS Textract, etc.)
 */
async function extractDocument(documentId) {

    // Check if document exists
    const document = await pool.query(
        `
        SELECT *
        FROM property_documents
        WHERE id = $1
        `,
        [documentId]
    );

    if (document.rows.length === 0) {
        throw new Error("Document not found");
    }

    // Dummy OCR output
    const extractedData = {
        owner_name: "John Doe",
        survey_no: "47/3",
        area_acres: 2.35,
        land_use: "Residential",
        registration_date: "2024-01-15",
        amount_rs: 2500000,
        parties: {
            seller: "ABC Developers",
            buyer: "John Doe"
        },
        raw_extract: "Dummy OCR output generated for Sprint 2"
    };

    // Save extracted data
    const result = await pool.query(
        `
        INSERT INTO doc_ocr_extracts
        (
            document_id,
            owner_name,
            survey_no,
            area_acres,
            land_use,
            registration_date,
            amount_rs,
            parties,
            raw_extract
        )
        VALUES
        ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        RETURNING *
        `,
        [
            documentId,
            extractedData.owner_name,
            extractedData.survey_no,
            extractedData.area_acres,
            extractedData.land_use,
            extractedData.registration_date,
            extractedData.amount_rs,
            JSON.stringify(extractedData.parties),
            extractedData.raw_extract
        ]
    );

    return result.rows[0];
}

module.exports = {
    extractDocument
};