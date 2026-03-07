import React, { useState, useEffect } from "react";
import { Container, Row, Col, Pagination } from "react-bootstrap";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const getBadgeClass = (rating) => {
  const r = (rating || "").toLowerCase();
  if (r === "avoid") return "badge-avoid";
  if (r === "irritant") return "badge-irritant";
  if (r === "safe") return "badge-safe";
  if (r === "moderate") return "badge-moderate";
  return "badge-unknown";
};

const getBarClass = (rating) => {
  const r = (rating || "").toLowerCase();
  if (r === "avoid") return "status-bar-avoid";
  if (r === "irritant") return "status-bar-irritant";
  if (r === "safe") return "status-bar-safe";
  if (r === "moderate") return "status-bar-moderate";
  return "";
};

const Encyclopedia = () => {
  const [query, setQuery] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // Filters
  const [riskFilter, setRiskFilter] = useState("");

  const fetchIngredients = async (searchQuery, pg, riskLevel) => {
    setLoading(true);
    try {
      // We trim the riskLevel to ensure no extra spaces are sent
      const cleanRisk = riskLevel.trim();
      const url = `${API}/api/ingredients/search?query=${encodeURIComponent(searchQuery)}&page=${pg}&risk=${cleanRisk}`;

      console.log("SENDING REQUEST TO:", url); // Open F12 console to see this!

      const res = await fetch(url);
      const data = await res.json();

      setIngredients(data.items || []);
      setTotalPages(data.pages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Fetch error:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchIngredients(query, 1, riskFilter);
    }, 400);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    fetchIngredients(query, page, riskFilter);
  }, [page, riskFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchIngredients(query, 1, riskFilter);
  };

  return (
    <div className="fade-in-up">
      {/* Header */}
      <section
        className="text-center py-5 mt-5 bg-pc-white"
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
                  { label: "Avoid", val: "Avoid" },
                ].map((f) => (
                  <span
                    key={f.val}
                    className={`badge rounded-pill ${riskFilter === f.val ? "bg-dark text-white" : "bg-light text-dark border"}`}
                    style={{ cursor: "pointer", padding: "6px 14px" }}
                    onClick={() => {
                      const newRisk = riskFilter === f.val ? "" : f.val;
                      setRiskFilter(newRisk);
                      setPage(1); // This will trigger the useEffect automatically
                    }}
                  >
                    {f.label}
                  </span>
                ))}
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
          <Col lg={9}>
            {loading ? (
              <div className="text-center py-5">
                <div
                  className="spinner-border"
                  style={{ color: "var(--pc-gold)" }}
                ></div>
              </div>
            ) : (
              <>
                <Row className="g-4">
                  {ingredients.map((ing, idx) => (
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

                        <button className="btn btn-sm btn-pc-secondary w-100">
                          Clinical Details
                        </button>
                      </div>
                    </Col>
                  ))}
                </Row>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="d-flex justify-content-center mt-5">
                    <Pagination className="pc-pagination">
                      <Pagination.Prev
                        disabled={page === 1}
                        onClick={() => setPage((p) => p - 1)}
                      />

                      {/* Always show page 1 */}
                      <Pagination.Item
                        active={page === 1}
                        onClick={() => setPage(1)}
                      >
                        1
                      </Pagination.Item>

                      {/* Left ellipsis */}
                      {page > 3 && <Pagination.Ellipsis disabled />}

                      {/* Middle pages — sliding window around current page */}
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

                      {/* Right ellipsis */}
                      {page < totalPages - 2 && (
                        <Pagination.Ellipsis disabled />
                      )}

                      {/* Always show last page */}
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
            )}
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default Encyclopedia;
