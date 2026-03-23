import React from "react"
import { Link } from "react-router-dom"
import { Container, Row, Col } from "react-bootstrap"
import "./Home.css"

const Home = () => {
  return (
    <div className="fade-in-up home-page">
      {/* Hero Section */}
      <section className="hero-section d-flex align-items-center pb-5">
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
                  Check Product Safety
                </Link>
                <Link to="/ingredients" className="btn btn-pc-secondary">
                  Explore Ingredients
                </Link>
              </div>
            </Col>
            <Col
              lg={6}
              className="text-center fade-in-up delay-2 order-2 order-lg-2 hero-image-col"
            >
              <img
                src="/bottle.webp"
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
                  350+
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
                  Gemini
                </div>
                <small
                  className="text-uppercase"
                  style={{
                    letterSpacing: 1,
                    color: "#a3afa6",
                    fontSize: "0.72rem",
                  }}
                >
                  AI Powered
                </small>
              </div>
            </Col>
          </Row>

          <Row className="g-4">
            {[
              {
                icon: "bi-database",
                title: "350+ Ingredients Analyzed",
                desc: "Our database covers 350+ cosmetic ingredients rated across four safety levels — Safe, Moderate, Irritant, and Avoid.",
              },
              {
                icon: "bi-patch-question",
                title: "Skin Type Quiz",
                desc: "Answer 5 quick questions to discover your skin type and get personalized ingredient recommendations saved to your profile.",
              },
              {
                icon: "bi-camera",
                title: "AI Label Scanner",
                desc: "Upload a photo of any product label and Gemini Vision AI instantly extracts and rates every ingredient for your skin.",
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
  )
}

export default Home
