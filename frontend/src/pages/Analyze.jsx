import React, { useState, useRef } from "react";
import { Container, Row, Col, Spinner } from "react-bootstrap";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const getBadgeClass = (rating) => {
  const r = (rating || "").toLowerCase();
  if (r === "avoid") return "badge-avoid";
  if (r === "irritant") return "badge-irritant";
  if (r === "safe") return "badge-safe";
  if (r === "moderate") return "badge-moderate";
  return "badge-unknown";
};

const Analyze = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResults(null);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  };

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setScanProgress(0);

    // Simulate progress
    const interval = setInterval(() => {
      setScanProgress((p) => {
        if (p >= 85) {
          clearInterval(interval);
          return 85;
        }
        return p + Math.random() * 15;
      });
    }, 300);

    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/api/analyze/image`, {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      setScanProgress(100);
      setTimeout(() => setResults(data), 400);
    } catch (err) {
      console.error(err);
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  return (
    <div className="fade-in-up">
      <Container className="py-5">
        {/* Header */}
        <h1 style={{ fontSize: "2.8rem", marginBottom: 12 }}>
          AI Ingredient Scanner
        </h1>
        <p
          className="mb-5"
          style={{
            color: "var(--pc-muted)",
            maxWidth: 520,
            fontSize: "1.05rem",
          }}
        >
          Advanced computer vision analyzing your skincare formulations in
          real-time. Upload a photo of your product label to begin the clinical
          breakdown.
        </p>

        {/* Upload Zone */}
        {!preview && (
          <div
            className={`upload-zone mb-5 ${dragging ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(e) => handleFile(e.target.files[0])}
            />
            <div className="mb-3">
              <span
                className="d-inline-flex align-items-center justify-content-center rounded-3"
                style={{
                  width: 64,
                  height: 64,
                  background: "var(--pc-safe-bg)",
                }}
              >
                <i
                  className="bi bi-image fs-3"
                  style={{ color: "var(--pc-safe)" }}
                ></i>
              </span>
            </div>
            <h5 style={{ fontFamily: "var(--pc-font-serif)" }}>
              Upload Cosmetic Label
            </h5>
            <p style={{ color: "var(--pc-muted)", fontSize: "0.9rem" }}>
              Drag and drop your image here, or click to browse
            </p>
            <div className="d-flex gap-3 justify-content-center mt-3">
              <span className="badge bg-light text-dark border">JPG</span>
              <span className="badge bg-light text-dark border">PNG</span>
              <span className="badge bg-light text-dark border">HEIC</span>
            </div>
          </div>
        )}

        {/* Upload Buttons */}
        {!preview && (
          <Row className="g-3 justify-content-center">
            <Col xs="auto">
              <button
                className="btn btn-outline-pc-secondary btn-lg rounded-pill px-4"
                onClick={() => inputRef.current?.click()}
              >
                <i className="bi bi-image me-2"></i> Browse Files
              </button>
            </Col>
            <Col xs="auto">
              <div className="position-relative">
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  hidden
                  onChange={(e) => handleFile(e.target.files[0])}
                  id="camera-capture"
                />
                <label
                  htmlFor="camera-capture"
                  className="btn btn-pc-primary btn-lg rounded-pill px-4"
                >
                  <i className="bi bi-camera-fill me-2"></i> Take Photo
                </label>
              </div>
            </Col>
          </Row>
        )}

        {/* Preview + Results */}
        {preview && (
          <Row className="g-5">
            <Col md={5}>
              <div className="position-relative">
                <img
                  src={preview}
                  alt="Uploaded label"
                  className="img-fluid rounded-4 shadow"
                  style={{ maxHeight: 500, objectFit: "cover", width: "100%" }}
                />
                {loading && (
                  <div
                    className="position-absolute bottom-0 start-0 end-0 rounded-bottom-4 p-3"
                    style={{
                      background:
                        "linear-gradient(transparent, rgba(26,38,30,0.9))",
                    }}
                  >
                    <div className="d-flex justify-content-between mb-2">
                      <small className="text-white fw-semibold">
                        <i className="bi bi-stars me-1"></i> AI SCANNING ACTIVE
                      </small>
                      <small className="text-warning fw-bold">
                        {Math.round(scanProgress)}% Parsed
                      </small>
                    </div>
                    <div className="pc-progress">
                      <div
                        className="progress-bar"
                        style={{
                          width: `${scanProgress}%`,
                          transition: "width 0.4s",
                        }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
              <div className="d-flex justify-content-between mt-3">
                <button
                  className="btn btn-sm btn-pc-secondary"
                  onClick={() => {
                    setPreview(null);
                    setFile(null);
                    setResults(null);
                  }}
                >
                  <i className="bi bi-x-lg me-1"></i> Remove
                </button>
                {!results && !loading && (
                  <button className="btn btn-pc-primary" onClick={analyze}>
                    <i className="bi bi-cpu me-2"></i> Analyze Label
                  </button>
                )}
              </div>
            </Col>

            <Col md={7}>
              {loading && !results && (
                <div className="text-center py-5">
                  <Spinner
                    animation="border"
                    style={{ color: "var(--pc-gold)" }}
                  />
                  <p className="mt-3" style={{ color: "var(--pc-muted)" }}>
                    Analyzing ingredients...
                  </p>
                </div>
              )}

              {results && (
                <div className="fade-in-up">
                  <div className="d-flex justify-content-between align-items-center mb-4">
                    <h3 style={{ fontSize: "1.8rem" }}>Health Breakdown</h3>
                    <small style={{ color: "var(--pc-muted)" }}>
                      {results.ingredients.length} COMPONENTS
                    </small>
                  </div>

                  {results.ingredients.map((ing, idx) => (
                    <div
                      key={idx}
                      className="ingredient-result d-flex align-items-start justify-content-between fade-in-up"
                      style={{ animationDelay: `${idx * 0.05}s` }}
                    >
                      <div style={{ flex: 1 }}>
                        <div className="d-flex align-items-center gap-2 mb-1">
                          <strong style={{ fontSize: "1.05rem" }}>
                            {ing.name}
                          </strong>
                          <span
                            className={`badge rounded-pill ${getBadgeClass(ing.safety_rating)}`}
                          >
                            {ing.safety_rating}
                          </span>
                          {ing.safety_rating === "Safe" && (
                            <i
                              className="bi bi-check-circle-fill"
                              style={{ color: "var(--pc-safe)" }}
                            ></i>
                          )}
                        </div>
                        <p
                          className="mb-0"
                          style={{
                            color: "var(--pc-muted)",
                            fontSize: "0.88rem",
                          }}
                        >
                          {ing.description}
                        </p>
                      </div>
                      <i
                        className="bi bi-info-circle ms-3"
                        style={{ color: "var(--pc-muted)", cursor: "pointer" }}
                      ></i>
                    </div>
                  ))}
                </div>
              )}
            </Col>
          </Row>
        )}
      </Container>
    </div>
  );
};

export default Analyze;
