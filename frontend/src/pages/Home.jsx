import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Container, Row, Col } from "react-bootstrap";
import "./Home.css";

const Home = () => {
  const [activeInsightIndex, setActiveInsightIndex] = useState(0);

  const insightSlides = [
    {
      rawLabel: "Methylparaben",
      insight: "Avoid: Endocrine Disruptor",
      leftDescription:
        "Unprocessed chemical nomenclature often hides potential biological risks.",
      rightDescription:
        "PureCheck AI cross-references clinical trials to provide actionable health advice.",
      fillPercent: 70,
    },
    {
      rawLabel: "Sodium Lauryl Sulfate (SLS)",
      insight: "Use Sparingly: Barrier Disruptor",
      leftDescription:
        "Common foaming agents can strip the skin's natural lipid layer when overused.",
      rightDescription:
        "Our engine flags surfactants that may compromise barrier integrity at higher concentrations.",
      fillPercent: 55,
    },
    {
      rawLabel: "Fragrance / Parfum",
      insight: "Caution: Sensitization Risk",
      leftDescription:
        "Opaque 'fragrance' blends may include hundreds of undisclosed aroma chemicals.",
      rightDescription:
        "We highlight potential allergenic components and suggest fragrance-free alternatives.",
      fillPercent: 80,
    },
  ];

  useEffect(() => {
    const intervalId = setInterval(() => {
      setActiveInsightIndex((prev) => (prev + 1) % insightSlides.length);
    }, 7000);

    return () => clearInterval(intervalId);
  }, [insightSlides.length]);

  const activeInsight = insightSlides[activeInsightIndex];

  return (
    <div className="fade-in-up home-page">
      {/* Hero Section */}
      <section className="hero-section d-flex align-items-center">
        <Container>
          <Row className="align-items-center g-5">
            <Col lg={6} className="fade-in-up order-1 order-lg-1">
              <span
                className="badge rounded-pill mb-3"
                style={{
                  background: "var(--pc-gold-light)",
                  color: "var(--pc-gold)",
                  fontSize: "0.8rem",
                  padding: "8px 16px",
                }}
              >
                <i className="bi bi-stars me-1"></i> Clinical Precision AI
              </span>
              <h1
                style={{
                  fontSize: "4.2rem",
                  lineHeight: 1.05,
                  marginBottom: "24px",
                }}
              >
                Decipher
                <br />
                Your Beauty
              </h1>
              <p
                className="mb-4 hero-subtext"
                style={{
                  color: "var(--pc-muted)",
                  fontSize: "1.1rem",
                  maxWidth: 460,
                  lineHeight: 1.7,
                }}
              >
                Premium AI-powered cosmetic ingredient analysis for the
                conscious consumer. Understand every label with surgical
                precision and clinical transparency.
              </p>
              <div className="d-flex gap-3 hero-buttons">
                <Link to="/analyze" className="btn btn-pc-primary">
                  Start Free Analysis
                </Link>
                <Link to="/ingredients" className="btn btn-pc-secondary">
                  View Sample Report
                </Link>
              </div>
            </Col>
            <Col
              lg={6}
              className="text-center fade-in-up delay-2 order-2 order-lg-2 hero-image-col"
            >
              <img
                src="/bottle.png"
                alt="Premium Cosmetic Bottle"
                className="img-fluid"
                style={{
                  borderRadius: 24,
                  boxShadow: "0 30px 60px rgba(0,0,0,0.12)",
                  maxHeight: 500,
                  objectFit: "cover",
                }}
              />
            </Col>
          </Row>
        </Container>
      </section>

      {/* Chemical-to-Clear Difference */}
      <section className="bg-pc-white py-5 section-padding">
        <Container className="text-center">
          <h2 className="section-title">The Chemical-to-Clear Difference</h2>
          <p
            className="mb-5"
            style={{
              color: "var(--pc-muted)",
              maxWidth: 520,
              margin: "0 auto 48px",
            }}
          >
            Experience the clarity our AI brings to complex formulations.
          </p>

          <div
            className="pc-card mx-auto p-4 p-md-5 text-start insight-card"
            style={{ maxWidth: 780, border: "1px solid var(--pc-border)" }}
          >
            <Row className="mb-3 align-items-center insight-card-header">
              <Col>
                <small
                  className="text-uppercase"
                  style={{
                    letterSpacing: 2,
                    color: "var(--pc-muted)",
                    fontSize: "0.72rem",
                  }}
                >
                  Raw Label
                </small>
                <div
                  className="mt-1"
                  style={{
                    fontSize: "1.4rem",
                    color: "var(--pc-avoid)",
                    fontWeight: 500,
                  }}
                >
                  {activeInsight.rawLabel}
                </div>
              </Col>
              <Col className="text-end">
                <small
                  className="text-uppercase fw-semibold d-block"
                  style={{
                    letterSpacing: 2,
                    color: "var(--pc-gold)",
                    fontSize: "0.72rem",
                  }}
                >
                  PureCheck™ Insights
                </small>
                <div
                  className="mt-1"
                  style={{
                    fontFamily: "var(--pc-font-serif)",
                    fontSize: "1.4rem",
                    fontStyle: "italic",
                    fontWeight: 700,
                  }}
                >
                  {activeInsight.insight}
                </div>
                <div className="mt-2 d-inline-flex align-items-center gap-2">
                  <button
                    type="button"
                    aria-label="Previous insight"
                    onClick={() =>
                      setActiveInsightIndex((prev) =>
                        prev === 0 ? insightSlides.length - 1 : prev - 1,
                      )
                    }
                    className="btn btn-sm btn-outline-light border-0 px-2"
                    style={{ color: "var(--pc-muted)" }}
                  >
                    <i className="bi bi-chevron-left" />
                  </button>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--pc-muted)",
                      letterSpacing: 1,
                      textTransform: "uppercase",
                    }}
                  >
                    {activeInsightIndex + 1} / {insightSlides.length}
                  </span>
                  <button
                    type="button"
                    aria-label="Next insight"
                    onClick={() =>
                      setActiveInsightIndex(
                        (prev) => (prev + 1) % insightSlides.length,
                      )
                    }
                    className="btn btn-sm btn-outline-light border-0 px-2"
                    style={{ color: "var(--pc-muted)" }}
                  >
                    <i className="bi bi-chevron-right" />
                  </button>
                </div>
              </Col>
            </Row>
            {/* Slider */}
            <div
              className="position-relative my-4"
              style={{
                height: 4,
                background: "var(--pc-border)",
                borderRadius: 2,
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: `${activeInsight.fillPercent}%`,
                  background: "var(--pc-gold)",
                  borderRadius: 2,
                }}
              ></div>
              <div
                style={{
                  position: "absolute",
                  left: `${activeInsight.fillPercent}%`,
                  top: "50%",
                  transform: "translate(-50%,-50%)",
                  width: 20,
                  height: 20,
                  border: "3px solid var(--pc-gold)",
                  background: "#fff",
                  borderRadius: "50%",
                }}
              ></div>
            </div>
            <Row className="insight-descriptions">
              <Col
                className="fst-italic"
                style={{ color: "var(--pc-muted)", fontSize: "0.88rem" }}
              >
                {activeInsight.leftDescription}
              </Col>
              <Col
                className="text-end text-md-end fst-italic"
                style={{ color: "var(--pc-muted)", fontSize: "0.88rem" }}
              >
                {activeInsight.rightDescription}
              </Col>
            </Row>
          </div>
        </Container>
      </section>

      {/* Pure Science, Pure Beauty */}
      <section className="bg-pc-dark section-padding">
        <Container>
          <Row className="align-items-end mb-5">
            <Col lg={7}>
              <h2 className="section-title-lg">
                Pure Science,
                <br />
                Pure Beauty
              </h2>
              <p
                style={{
                  color: "#a3afa6",
                  fontSize: "1.05rem",
                  maxWidth: 480,
                  lineHeight: 1.7,
                }}
              >
                Advanced AI algorithms trained on dermatological databases to
                protect your skin's health. We bridge the gap between complex
                chemistry and conscious skincare choices.
              </p>
            </Col>
            <Col
              lg={5}
              className="d-flex justify-content-end gap-3 stats-col stats-row"
            >
              <div
                className="text-center rounded-3 p-3 px-4 stat-box"
                style={{ background: "rgba(255,255,255,0.05)" }}
              >
                <div
                  style={{
                    color: "var(--pc-gold)",
                    fontSize: "2rem",
                    fontFamily: "var(--pc-font-serif)",
                    fontWeight: 700,
                  }}
                >
                  300+
                </div>
                <small
                  className="text-uppercase"
                  style={{
                    letterSpacing: 1,
                    color: "#a3afa6",
                    fontSize: "0.72rem",
                  }}
                >
                  Ingredients
                </small>
              </div>
              <div
                className="text-center rounded-3 p-3 px-4 stat-box"
                style={{ background: "rgba(255,255,255,0.05)" }}
              >
                <div
                  style={{
                    color: "var(--pc-gold)",
                    fontSize: "2rem",
                    fontFamily: "var(--pc-font-serif)",
                    fontWeight: 700,
                  }}
                >
                  99.8%
                </div>
                <small
                  className="text-uppercase"
                  style={{
                    letterSpacing: 1,
                    color: "#a3afa6",
                    fontSize: "0.72rem",
                  }}
                >
                  Accuracy
                </small>
              </div>
            </Col>
          </Row>

          <Row className="g-4">
            {[
              {
                icon: "bi-database",
                title: "Deep Database Scan",
                desc: "Cross-references 300+ ingredients against global safety standards including ECHA, CIR, and FDA.",
              },
              {
                icon: "bi-person-check",
                title: "Personalized Risk Profile",
                desc: "Tailors analysis to your specific skin type, sensitivities, and allergies for a truly bespoke report.",
              },
              {
                icon: "bi-camera",
                title: "Instant Label Scan",
                desc: "Scan any product label with your camera for immediate results, powered by advanced OCR and computer vision.",
              },
            ].map((f, i) => (
              <Col md={4} key={i}>
                <div
                  className="pc-card p-4 h-100"
                  style={{ backgroundColor: "#fff", color: "var(--pc-dark)" }}
                >
                  <div
                    className="rounded-circle d-flex align-items-center justify-content-center mb-3"
                    style={{
                      width: 50,
                      height: 50,
                      background: "var(--pc-cream)",
                    }}
                  >
                    <i className={`bi ${f.icon} fs-5`}></i>
                  </div>
                  <h5
                    className="mb-2"
                    style={{ fontFamily: "var(--pc-font-serif)" }}
                  >
                    {f.title}
                  </h5>
                  <p style={{ color: "var(--pc-muted)", fontSize: "0.9rem" }}>
                    {f.desc}
                  </p>
                </div>
              </Col>
            ))}
          </Row>
        </Container>
      </section>
    </div>
  );
};

export default Home;
