const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");

// EICAR antivirus test signature — the standard harmless string used to verify
// that virus detection works. Detected directly as a fallback when clamscan is
// not installed, so the security path is demonstrable in dev.
const EICAR =
  "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*";

// Returns { infected: boolean, scanner: 'clamav' | 'eicar-fallback' | 'skipped' }
function scanBuffer(buffer) {
  if (process.env.SKIP_VIRUS_SCAN === "true") {
    return Promise.resolve({ infected: false, scanner: "skipped" });
  }

  const tmp = path.join(os.tmpdir(), `ribil-scan-${crypto.randomUUID()}`);
  fs.writeFileSync(tmp, buffer);

  return new Promise((resolve) => {
    const proc = spawn("clamscan", ["--stdout", "--no-summary", tmp]);
    let unavailable = false;

    proc.on("error", () => {
      unavailable = true;
    });

    proc.on("close", (code) => {
      fs.unlink(tmp, () => {});
      if (unavailable) {
        // clamscan not on PATH — fall back to EICAR signature detection.
        const infected = buffer.includes(Buffer.from(EICAR));
        return resolve({ infected, scanner: "eicar-fallback" });
      }
      // clamscan exit code 1 = infected, 0 = clean.
      resolve({ infected: code === 1, scanner: "clamav" });
    });
  });
}

module.exports = { scanBuffer };
