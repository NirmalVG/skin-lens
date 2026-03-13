import React, { useState, useEffect, useCallback } from "react"
import { Container, Row, Col, Pagination, Modal } from "react-bootstrap"
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

const getBarClass = (rating) => {
  const r = (rating || "").toLowerCase()
  if (r === "avoid") return "status-bar-avoid"
  if (r === "irritant") return "status-bar-irritant"
  if (r === "safe") return "status-bar-safe"
  if (r === "moderate") return "status-bar-moderate"
  return ""
}

const Encyclopedia = () => {
  const [query, setQuery] = useState("")
  const [ingredients, setIngredients] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [showClinicalModal, setShowClinicalModal] = useState(false)
  const [selectedIngredient, setSelectedIngredient] = useState(null)
  const [debouncedQuery, setDebouncedQuery] = useState(query)
  // Filters
  const [riskFilter, setRiskFilter] = useState("")

  const openClinicalDetails = (ingredient) => {
    setSelectedIngredient(ingredient)
    setShowClinicalModal(true)
  }

  const closeClinicalDetails = () => {
    setShowClinicalModal(false)
    setSelectedIngredient(null)
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

  const fetchIngredients = useCallback(async (searchQuery, pg, riskLevel) => {
    setLoading(true)
    try {
      let url = `${API}/api/ingredients/search?query=${encodeURIComponent(searchQuery)}&page=${pg}`
      if (riskLevel && riskLevel.trim()) {
        url += `&risk=${encodeURIComponent(riskLevel)}`
      }

      console.log("SENDING REQUEST TO:", url) // Open F12 console to see this!

      const res = await fetch(url)
      const data = await res.json()

      setIngredients(data.items || [])
      setTotalPages(data.pages || 1)
      setTotal(data.total || 0)
    } catch (err) {
      console.error("Fetch error:", err)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
      // Reset to page 1 when typing a new search
      if (query !== debouncedQuery) setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    fetchIngredients(debouncedQuery, page, riskFilter)
  }, [debouncedQuery, page, riskFilter])

  const handleSearch = (e) => {
    e.preventDefault()
    setDebouncedQuery(query)
    setPage(1)
  }

  return (
    <div className="fade-in-up">
      {/* Header */}
      <section
        className="text-center py-5 bg-pc-white"
        style={{ paddingBottom: 40 }}
      >
        <Container>
          <h1
            style={{
              fontSize: "2.8rem",
              marginBottom: 12,
              fontFamily: "var(--pc-font-serif)",
            }}
          >
            Ingredient Encyclopedia
          </h1>
          <p
            style={{
              color: "var(--pc-muted)",
              maxWidth: 520,
              margin: "0 auto 40px",
            }}
          >
            Explore our clinical database of over 300+ cosmetic ingredients,
            vetted by dermatological science.
          </p>

          {/* Search */}
          <form className="position-relative mx-auto" style={{ maxWidth: 600 }}>
            <i
              className="bi bi-search position-absolute"
              style={{
                left: 20,
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--pc-muted)",
                zIndex: 1,
              }}
            ></i>
            <input
              type="text"
              className="form-control pc-search"
              placeholder="Search chemical name..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </form>
        </Container>
      </section>

      <Container className="py-5">
        <Row className="g-4">
          {/* Sidebar Filters */}
          <Col lg={3}>
            <div className="pc-card p-4 mb-4">
              <h6
                style={{
                  fontFamily: "var(--pc-font-serif)",
                  fontSize: "1.1rem",
                  marginBottom: 20,
                }}
              >
                Refine Database
              </h6>

              <p
                className="text-uppercase fw-semibold mb-2 mt-4"
                style={{
                  fontSize: "0.72rem",
                  letterSpacing: 1,
                  color: "var(--pc-muted)",
                }}
              >
                Risk Level
              </p>
              <div className="d-flex flex-wrap gap-2">
                {[
                  { label: "Safe", val: "Safe" },
                  { label: "Caution", val: "Moderate" },
                  { label: "Irritant", val: "Irritant" },
                  { label: "Avoid", val: "Avoid" },
                ].map((f) => (
                  <span
                    key={f.val}
                    className={`badge rounded-pill ${riskFilter === f.val ? "bg-dark text-white" : "bg-light text-dark border"}`}
                    style={{ cursor: "pointer", padding: "6px 14px" }}
                    onClick={() => {
                      const newRisk = riskFilter === f.val ? "" : f.val
                      setRiskFilter(newRisk)
                      setPage(1)
                    }}
                  >
                    {f.label}
                  </span>
                ))}
                {riskFilter && (
                  <span
                    className="badge rounded-pill bg-secondary text-white"
                    style={{ cursor: "pointer", padding: "6px 14px" }}
                    onClick={() => {
                      setRiskFilter("")
                      setPage(1)
                    }}
                  >
                    Clear
                  </span>
                )}
              </div>
            </div>

            {/* AI Deep Analysis CTA */}
            <div
              className="rounded-4 p-4"
              style={{ background: "var(--pc-green)", color: "#fff" }}
            >
              <i
                className="bi bi-stars fs-4 mb-2 d-block"
                style={{ color: "var(--pc-gold)" }}
              ></i>
              <h6 style={{ color: "#fff", fontFamily: "var(--pc-font-serif)" }}>
                AI Deep Analysis
              </h6>
              <p
                className="mb-3"
                style={{ fontSize: "0.85rem", color: "#a3afa6" }}
              >
                Upload a photo of any ingredient list for a full toxicity
                breakdown.
              </p>
              <a href="/analyze" className="btn btn-pc-gold btn-sm">
                Launch Scanner
              </a>
            </div>
          </Col>

          {/* Cards Grid */}
          <Col lg={9} style={{ minHeight: "800px" }}>
            {loading ? (
              <Row className="g-4">
                {[1, 2, 3, 4, 5, 6].map((idx) => (
                  <Col md={4} key={idx}>
                    <div className="pc-card p-4 h-100">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <Skeleton
                          width={60}
                          height={20}
                          className="rounded-pill"
                        />
                        <Skeleton circle width={16} height={16} />
                      </div>
                      <Skeleton width="80%" height={24} className="mb-2" />
                      <Skeleton width="60%" height={14} className="mb-3" />
                      <div className="d-flex align-items-center gap-2 mb-2">
                        <Skeleton width={100} height={12} />
                        <Skeleton
                          width={60}
                          height={20}
                          className="rounded-pill"
                        />
                      </div>
                      <Skeleton
                        width="100%"
                        height={8}
                        className="mb-3 rounded"
                      />
                      <Skeleton width="100%" height={12} className="mb-1" />
                      <Skeleton width="90%" height={12} className="mb-1" />
                      <Skeleton width="70%" height={12} className="mb-3" />
                      <Skeleton width="100%" height={32} className="rounded" />
                    </div>
                  </Col>
                ))}
              </Row>
            ) : ingredients.length > 0 ? (
              <>
                <Row className="g-4">
                  {ingredients.map((ing, idx) => (
                    // ... Keep your existing ingredient mapping logic exactly the same ...
                    <Col md={4} key={ing.id}>
                      <div
                        className="pc-card p-4 h-100 fade-in-up"
                        style={{ animationDelay: `${idx * 0.04}s` }}
                      >
                        <div className="d-flex justify-content-between align-items-start mb-2">
                          <span
                            className={`badge rounded-pill ${getBadgeClass(ing.safety_rating)}`}
                            style={{ fontSize: "0.7rem" }}
                          >
                            EWG {Math.floor(Math.random() * 9) + 1}
                          </span>
                          <i
                            className="bi bi-info-circle"
                            style={{
                              color: "var(--pc-muted)",
                              cursor: "pointer",
                            }}
                            onClick={() => openClinicalDetails(ing)}
                          ></i>
                        </div>
                        <h6
                          className="mt-2 mb-0"
                          style={{
                            fontFamily: "var(--pc-font-serif)",
                            fontSize: "1.1rem",
                          }}
                        >
                          {ing.name}
                        </h6>
                        <small
                          className="d-block mb-2"
                          style={{
                            color: "var(--pc-muted)",
                            fontStyle: "italic",
                          }}
                        >
                          {ing.compatible_skin_types}
                        </small>
                        <div className="d-flex align-items-center gap-2 mb-2">
                          <small
                            className="text-uppercase fw-semibold"
                            style={{
                              letterSpacing: 1,
                              color: "var(--pc-muted)",
                              fontSize: "0.68rem",
                            }}
                          >
                            Safety Profile
                          </small>
                          <span
                            className={`badge rounded-pill ${getBadgeClass(ing.safety_rating)}`}
                          >
                            {ing.safety_rating}
                          </span>
                        </div>
                        <div
                          className={`status-bar ${getBarClass(ing.safety_rating)}`}
                        ></div>
                        <p
                          className="mt-2 mb-3"
                          style={{
                            color: "var(--pc-muted)",
                            fontSize: "0.82rem",
                          }}
                        >
                          {ing.description?.substring(0, 100)}
                          {ing.description?.length > 100 ? "..." : ""}
                        </p>
                        <button
                          className="btn btn-sm btn-pc-secondary w-100"
                          onClick={() => openClinicalDetails(ing)}
                        >
                          Clinical Details
                        </button>
                      </div>
                    </Col>
                  ))}
                </Row>

                {/* Pagination */}
                {totalPages > 1 && (
                  // ... Keep your existing Pagination code exactly the same ...
                  <div className="d-flex justify-content-center mt-5">
                    <Pagination className="pc-pagination">
                      {/* Your existing pagination logic */}
                      <Pagination.Prev
                        disabled={page === 1}
                        onClick={() => setPage((p) => p - 1)}
                      />
                      <Pagination.Item
                        active={page === 1}
                        onClick={() => setPage(1)}
                      >
                        1
                      </Pagination.Item>
                      {page > 3 && <Pagination.Ellipsis disabled />}
                      {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter(
                          (p) =>
                            p > 1 && p < totalPages && Math.abs(p - page) <= 1,
                        )
                        .map((p) => (
                          <Pagination.Item
                            key={p}
                            active={p === page}
                            onClick={() => setPage(p)}
                          >
                            {p}
                          </Pagination.Item>
                        ))}
                      {page < totalPages - 2 && (
                        <Pagination.Ellipsis disabled />
                      )}
                      {totalPages > 1 && (
                        <Pagination.Item
                          active={page === totalPages}
                          onClick={() => setPage(totalPages)}
                        >
                          {totalPages}
                        </Pagination.Item>
                      )}
                      <Pagination.Next
                        disabled={page === totalPages}
                        onClick={() => setPage((p) => p + 1)}
                      />
                    </Pagination>
                  </div>
                )}
              </>
            ) : (
              // NEW: Empty State to prevent layout collapse when 0 results are found
              <div
                className="pc-card p-5 text-center d-flex flex-column align-items-center justify-content-center"
                style={{ height: "400px" }}
              >
                <i
                  className="bi bi-search mb-3"
                  style={{ fontSize: "2.5rem", color: "var(--pc-muted)" }}
                ></i>
                <h4 style={{ fontFamily: "var(--pc-font-serif)" }}>
                  No ingredients found
                </h4>
                <p style={{ color: "var(--pc-muted)" }}>
                  We couldn't find any ingredients matching your current
                  filters.
                </p>
                <button
                  className="btn btn-outline-secondary mt-3"
                  onClick={() => {
                    setQuery("")
                    setRiskFilter("")
                    setPage(1)
                  }}
                >
                  Clear Filters
                </button>
              </div>
            )}
          </Col>
        </Row>
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
                  className={`badge rounded-pill ${getBadgeClass(selectedIngredient.safety_rating)}`}
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

export default Encyclopedia
