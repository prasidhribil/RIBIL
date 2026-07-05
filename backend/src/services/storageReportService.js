const fs = require("fs");
const path = require("path");

const saveReport = async (propertyId, report) => {

    const reportsDir = path.join(__dirname, "../reports");

    if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir);
    }

    const filename = `${propertyId}-${Date.now()}.json`;

    const filePath = path.join(reportsDir, filename);

    fs.writeFileSync(
        filePath,
        JSON.stringify(report, null, 2)
    );

    return {
        s3_key: filename,
        download_url: `/reports/${filename}`,
        url_expires_at: null
    };
};

module.exports = {
    saveReport
};