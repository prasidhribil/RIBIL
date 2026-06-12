const multer = require("multer");

const ALLOWED_MIME = ["application/pdf", "image/jpeg", "image/png"];
const MAX_BYTES = 10 * 1024 * 1024; // 10 MB

// memoryStorage so the buffer goes to ClamAV + S3 without touching local disk.
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: MAX_BYTES },
  fileFilter: (req, file, cb) => {
    if (ALLOWED_MIME.includes(file.mimetype)) return cb(null, true);
    const err = new Error("Unsupported file type");
    err.code = "UNSUPPORTED_FILE_TYPE";
    cb(err);
  },
});

// Wraps multer's single-file parse and converts its errors into clean JSON.
function uploadSingle(field) {
  const handler = upload.single(field);
  return (req, res, next) => {
    handler(req, res, (err) => {
      if (!err) return next();
      if (err.code === "LIMIT_FILE_SIZE") {
        return res
          .status(413)
          .json({ error: { code: "FILE_TOO_LARGE", message: "Max file size is 10MB" } });
      }
      if (err.code === "UNSUPPORTED_FILE_TYPE") {
        return res.status(415).json({
          error: { code: "UNSUPPORTED_FILE_TYPE", message: "Only PDF, JPG, PNG allowed" },
        });
      }
      return res
        .status(400)
        .json({ error: { code: "UPLOAD_ERROR", message: err.message } });
    });
  };
}

module.exports = { uploadSingle, ALLOWED_MIME, MAX_BYTES };
