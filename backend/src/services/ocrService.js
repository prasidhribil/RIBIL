const pool = require("../config/database");

/**
 * OCR Extraction Service
 * (Sprint 4 Ready)
 *
 * Current:
 *  - Uses dummy OCR data.
 * Future:
 *  - Google Vision
 *  - AWS Textract
 *  - Azure OCR
 *  - Tesseract
 */
async function extractDocument(documentId) {

    // Verify document exists
    const documentResult = await pool.query(
        `
        SELECT *
        FROM property_documents
        WHERE id = $1
        `,
        [documentId]
    );

    if (documentResult.rows.length === 0) {
        throw new Error("Document not found");
    }

    const document = documentResult.rows[0];

    // ------------------------------------------------------------------
    // TODO:
    // Replace this block with actual OCR provider.
    // ------------------------------------------------------------------

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
        raw_extract: "Dummy OCR output generated for Sprint 4",
        confidence_score: 0.97,
        ocr_provider: "SIMULATED"
    };

    // Check if OCR already exists
    const existing = await pool.query(
        `
        SELECT id
        FROM doc_ocr_extracts
        WHERE document_id = $1
        `,
        [documentId]
    );

    if (existing.rows.length > 0) {
        await pool.query(
            `
            UPDATE doc_ocr_extracts
            SET
                owner_name=$2,
                survey_no=$3,
                area_acres=$4,
                land_use=$5,
                registration_date=$6,
                amount_rs=$7,
                parties=$8,
                raw_extract=$9,
                extracted_at=NOW()
            WHERE document_id=$1
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
    } else {

        await pool.query(
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
    }

    return {
        success: true,
        provider: extractedData.ocr_provider,
        confidence: extractedData.confidence_score,
        extracted_fields: extractedData
    };
}

module.exports = {
    extractDocument
};