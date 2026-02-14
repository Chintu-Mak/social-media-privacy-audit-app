import React, { useState } from "react";

export default function UploadForm() {
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return alert("Please choose an image file to analyze.");

    const form = new FormData();
    form.append("file", file);
    form.append("caption", caption);

    setLoading(true);
    setReport(null);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Server error");
      }

      const data = await res.json();
      setReport(data.report);
    } catch (err) {
      alert("Error analyzing image: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="upload-form">
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <textarea
          placeholder="Optional caption..."
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          rows={3}
        />

        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {report && (
        <div className="report-card">
          <h2>
            Privacy Risk Score:
            <span className="risk-score">
              {report.privacy_risk_score}/100
            </span>
          </h2>

          {report.preview_image && (
            <div className="image-preview">
              <img
                src={report.preview_image}
                alt="Analyzed Preview"
              />
            </div>
          )}

          <h3>Reasons:</h3>
          <ul>
            {report.reasons && report.reasons.length > 0 ? (
              report.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))
            ) : (
              <li>None detected</li>
            )}
          </ul>

          <h3>Recommendations:</h3>
          <ul>
            {report.recommendations &&
              report.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
          </ul>

          <h3>Findings (raw):</h3>
          <pre>
            {JSON.stringify(report.findings, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
