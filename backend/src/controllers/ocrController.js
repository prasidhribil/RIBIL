const { extractDocument } = require("../services/ocrService");

const runOCR = async (req, res) => {
    try {
        const { id } = req.params;

        const result = await extractDocument(id);

        return res.status(200).json({
            success: true,
            message: "OCR completed successfully.",
            data: result
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
    runOCR
};