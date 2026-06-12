// Beta document classifier (POST /api/classify/document), owned by Team Beta.
// Called after every upload. If CLASSIFIER_URL is unset or the call fails, we
// fall back to a stub so the upload pipeline is never blocked (per the guide).
async function classifyDocument(text) {
  const url = process.env.CLASSIFIER_URL;
  const stub = { predicted_class: "other", confidence: 0.5, extracted_fields: {} };
  if (!url) return stub;

  try {
    const res = await fetch(`${url.replace(/\/$/, "")}/api/classify/document`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text || "" }),
    });
    if (!res.ok) throw new Error(`classifier returned ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("[classifier] using stub:", err.message);
    return stub;
  }
}

module.exports = { classifyDocument };
