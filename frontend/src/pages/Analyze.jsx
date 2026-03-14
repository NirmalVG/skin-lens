import React, { useState, useRef } from "react"
import { Container, Row, Col, Spinner, Modal } from "react-bootstrap"
import Skeleton from "react-loading-skeleton"
import "react-loading-skeleton/dist/skeleton.css"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

const getBadgeClass = (rating) => {
  const r = (rating || "").toLowerCase()
  if (r === "avoid") return "badge-avoid"
  if (r === "irritant") return "badge-irritant"
  if (r === "safe") return "badge-safe"
  if (r === "moderate") return "badge-moderate"
  return "badge-unknown"
}

const Analyze = () => {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [showClinicalModal, setShowClinicalModal] = useState(false)
  const [selectedIngredient, setSelectedIngredient] = useState(null)
  const inputRef = useRef(null)

  const openClinicalDetails = (ingredient) => {
    setSelectedIngredient(ingredient)
    setShowClinicalModal(true)
  }

  const closeClinicalDetails = () => {
    setShowClinicalModal(false)
  }

  const clinicalSummaryForRating = (rating) => {
    const r = (rating || "").toLowerCase()
    if (r === "safe")
      return "Generally well-tolerated in leave‑on and rinse‑off formulas when used as directed."
    if (r === "moderate")
      return "Use with some caution, especially on very sensitive or barrier‑impaired skin."
    if (r === "irritant")
      return "More likely to cause stinging, dryness, or redness—especially with frequent use."
    if (r === "avoid")
      return "Best avoided when possible; higher likelihood of irritation or other concerns."
    return "Clinical profile varies by concentration, formulation, and individual tolerance."
  }

  const handleFile = (f) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResults(null)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0])
  }

  const analyze = async () => {
    if (!file) return
    setLoading(true)
    setScanProgress(0)

    // Simulate progress
    const interval = setInterval(() => {
      setScanProgress((p) => {
        if (p >= 85) {
          clearInterval(interval)
          return 85
        }
        return p + Math.random() * 15
      })
    }, 300)

    try {
      const fd = new FormData()
      fd.append("file", file)
      const res = await fetch(`${API}/api/analyze/image`, {
        method: "POST",
        body: fd,
      })
      const data = await res.json()
      setScanProgress(100)
      setTimeout(() => setResults(data), 400)
    } catch (err) {
      console.error(err)
    } finally {
      clearInterval(interval)
      setLoading(false)
    }
  }

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
              e.preventDefault()
              setDragging(true)
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
                    <small className="text-white fw-semibold d-block mb-2">
                      <i className="bi bi-stars me-1"></i> AI SCANNING ACTIVE
                    </small>

                    <div className="d-flex align-items-center gap-2 w-100">
                      <div
                        style={{
                          flex: 1,
                          height: "8px",
                          background: "var(--pc-border)",
                          borderRadius: "99px",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            borderRadius: "99px",
                            width: `${scanProgress}%`,
                            backgroundColor: "#79a6b1",
                            boxShadow: "0 0 8px rgba(121, 166, 177, 0.5)",
                            transition: "width 0.5s ease-in-out",
                          }}
                        ></div>
                      </div>
                      <small
                        style={{
                          color: "#fff",
                          fontSize: "0.75rem",
                          minWidth: "35px",
                          textAlign: "right",
                          flexShrink: 0,
                        }}
                      >
                        {Math.round(scanProgress)}%
                      </small>
                    </div>
                  </div>
                )}
              </div>
              <div className="d-flex justify-content-between mt-3">
                <button
                  className="btn btn-sm btn-pc-secondary"
                  onClick={() => {
                    setPreview(null)
                    setFile(null)
                    setResults(null)
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
                <div className="fade-in-up">
                  {/* Header Skeleton */}
                  <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-2">
                    <h3
                      style={{
                        fontSize: "1.8rem",
                        margin: 0,
                        maxWidth: "100%",
                      }}
                    >
                      <Skeleton
                        width="100%"
                        style={{ maxWidth: 240 }}
                        height={30}
                      />
                    </h3>
                    <small style={{ color: "var(--pc-muted)" }}>
                      <Skeleton width={100} height={18} />
                    </small>
                  </div>

                  {/* List Items Skeleton */}
                  {[...Array(5)].map((_, idx) => (
                    <div
                      key={idx}
                      className="ingredient-result d-flex align-items-start justify-content-between fade-in-up"
                      style={{ animationDelay: `${idx * 0.05}s` }}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        {" "}
                        <div className="d-flex align-items-center flex-wrap gap-2 mb-2">
                          <Skeleton
                            width="40%"
                            style={{ maxWidth: 140, minWidth: 100 }}
                            height={20}
                          />
                          <Skeleton
                            width={60}
                            height={24}
                            className="rounded-pill"
                          />
                          <Skeleton circle width={18} height={18} />
                          <Skeleton width={90} height={20} />
                        </div>
                        <Skeleton width="100%" height={14} className="mb-1" />
                        <Skeleton
                          width="85%"
                          height={14}
                          className="mb-1 d-none d-md-block"
                        />{" "}
                        <Skeleton width="60%" height={12} />
                      </div>

                      <div className="ms-3 flex-shrink-0 mt-1">
                        <Skeleton circle width={24} height={24} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {results &&
              results.ingredients &&
              results.ingredients.length > 0 ? (
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
                            {String(ing.name)}
                          </strong>
                          <span
                            className={`badge rounded-pill ${getBadgeClass(ing.safety_rating)}`}
                          >
                            {String(ing.safety_rating)}
                          </span>
                          {ing.safety_rating === "Safe" && (
                            <i
                              className="bi bi-check-circle-fill"
                              style={{ color: "var(--pc-safe)" }}
                            ></i>
                          )}
                          {ing.source === "gemini" && (
                            <span
                              className="badge ms-2"
                              style={{
                                background: "var(--pc-gold-light)",
                                color: "var(--pc-accent)",
                                border: "1px solid var(--pc-accent)",
                                fontSize: "0.75rem",
                              }}
                            >
                              ✨ AI Analyzed
                            </span>
                          )}
                        </div>
                        <p
                          className="mb-1"
                          style={{
                            color: "var(--pc-muted)",
                            fontSize: "0.88rem",
                          }}
                        >
                          {String(ing.description)}
                        </p>
                        <small
                          style={{
                            color: "var(--pc-muted)",
                            fontSize: "0.75rem",
                          }}
                        >
                          Compatible: {String(ing.compatible_skin_types)}
                        </small>
                      </div>
                      <button
                        type="button"
                        className="btn btn-link p-0 ms-3"
                        style={{
                          color: "var(--pc-muted)",
                          cursor: "pointer",
                          fontSize: "1.25rem",
                        }}
                        onClick={() => openClinicalDetails(ing)}
                      >
                        <i className="bi bi-info-circle"></i>
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                results && (
                  <div className="text-center py-5">
                    <i
                      className="bi bi-exclamation-circle fs-1 mb-3 d-block"
                      style={{ color: "var(--pc-gold)" }}
                    ></i>
                    <h5>No ingredients found</h5>
                    <p style={{ color: "var(--pc-muted)" }}>
                      Try a clearer photo of the ingredient list on the label.
                    </p>
                  </div>
                )
              )}
            </Col>
          </Row>
        )}
      </Container>

      <Modal
        show={showClinicalModal}
        onHide={closeClinicalDetails}
        centered
        size="lg"
      >
        <Modal.Header closeButton>
          <div>
            <div
              style={{
                fontFamily: "var(--pc-font-serif)",
                fontSize: "1.25rem",
                lineHeight: 1.2,
              }}
            >
              {selectedIngredient?.name || "Clinical Details"}
            </div>
            {selectedIngredient && (
              <div className="d-flex flex-wrap gap-2 mt-2">
                <span
                  className={`badge rounded-pill ${getBadgeClass(
                    selectedIngredient.safety_rating,
                  )}`}
                >
                  {selectedIngredient.safety_rating || "Unknown"}
                </span>
                <span className="badge rounded-pill bg-light text-dark border">
                  {selectedIngredient.compatible_skin_types || "All skin types"}
                </span>
              </div>
            )}
          </div>
        </Modal.Header>
        <Modal.Body>
          {!selectedIngredient ? (
            <p className="mb-0" style={{ color: "var(--pc-muted)" }}>
              No ingredient selected.
            </p>
          ) : (
            <>
              <p style={{ color: "var(--pc-muted)" }}>
                {selectedIngredient.description ||
                  "No description available for this ingredient yet."}
              </p>

              <hr style={{ borderColor: "var(--pc-border)" }} />

              <h6
                style={{
                  fontFamily: "var(--pc-font-serif)",
                  marginBottom: 10,
                }}
              >
                Clinical interpretation
              </h6>
              <ul style={{ color: "var(--pc-muted)", fontSize: "0.92rem" }}>
                <li>
                  <strong>Risk level</strong>:{" "}
                  {selectedIngredient.safety_rating || "Unknown"} —{" "}
                  {clinicalSummaryForRating(selectedIngredient.safety_rating)}
                </li>
                <li>
                  <strong>Compatible skin types</strong>:{" "}
                  {selectedIngredient.compatible_skin_types || "All"}
                </li>
                <li>
                  <strong>Routine guidance</strong>: Patch test new products and
                  avoid stacking multiple potentially irritating actives in the
                  same routine.
                </li>
              </ul>
            </>
          )}
        </Modal.Body>
      </Modal>
    </div>
  )
}

export default Analyze
