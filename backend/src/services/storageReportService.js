const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const saveReport = async (propertyId, report) => {

    const reportsDir = path.join(__dirname, "../reports");

    if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
    }

    const timestamp = Date.now();

    const filename = `${propertyId}-${timestamp}.json`;

    const filePath = path.join(reportsDir, filename);

    // Calculate report checksum
    const reportHash = crypto
        .createHash("sha256")
        .update(JSON.stringify(report))
        .digest("hex");

    const reportWithMetadata = {
        metadata: {
            property_id: propertyId,
            generated_at: new Date().toISOString(),
            report_version: 1,
            checksum: reportHash
        },
        report
    };

    fs.writeFileSync(
        filePath,
        JSON.stringify(reportWithMetadata, null, 2),
        "utf8"
    );

    const stats = fs.statSync(filePath);

    return {
        s3_key: filename,
        download_url: `/reports/${filename}`,
        url_expires_at: null,
        checksum: reportHash,
        file_size: stats.size,
        generated_at: reportWithMetadata.metadata.generated_at
    };
};

module.exports = {
    saveReport
};