import React, { useState, useEffect } from "react"
import { Container, Row, Col } from "react-bootstrap"
import Skeleton from "react-loading-skeleton"
import "react-loading-skeleton/dist/skeleton.css"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

// Skin type quiz questions
const quizData = [
  {
    topic: "Skin Type Assessment",
    category: "SKIN PROFILE",
    question: "How does your skin typically feel by midday?",
    options: [
      "Oily and shiny all over",
      "Dry and tight",
      "Oily in T-zone, dry on cheeks",
      "Comfortable and balanced",
    ],
    skinMap: ["Oily", "Dry", "Combination", "Normal"],
    tip: "Understanding your skin type is the first step to choosing safe, effective products.",
  },
  {
    topic: "Skin Type Assessment",
    category: "SKIN PROFILE",
    question: "How does your skin react to new products?",
    options: [
      "Rarely any reaction",
      "Often turns red or itchy",
      "Sometimes breaks out",
      "Gets flaky or peeling",
    ],
    skinMap: ["Normal", "Sensitive", "Oily", "Dry"],
    tip: "Sensitive skin needs fragrance-free and hypoallergenic formulations.",
  },
  {
    topic: "Skin Type Assessment",
    category: "SKIN PROFILE",
    question: "How visible are the pores on your nose and cheeks?",
    options: [
      "Very visible and large",
      "Almost invisible",
      "Only visible on nose",
      "Moderately visible",
    ],
    skinMap: ["Oily", "Dry", "Combination", "Normal"],
    tip: "Large pores often correlate with oily skin types that benefit from niacinamide.",
  },
  {
    topic: "Skin Type Assessment",
    category: "SKIN PROFILE",
    question: "What is your main skin concern?",
    options: [
      "Aging and wrinkles",
      "Acne and breakouts",
      "Dullness and uneven tone",
      "Redness and sensitivity",
    ],
    skinMap: ["Aging", "Oily", "Normal", "Sensitive"],
    tip: "Targeting your primary concern helps narrow down the safest ingredients for your profile.",
  },
  {
    topic: "Skin Type Assessment",
    category: "SKIN PROFILE",
    question: "How often does your skin feel dehydrated?",
    options: [
      "Almost never",
      "All the time",
      "Only in winter",
      "After washing my face",
    ],
    skinMap: ["Oily", "Dry", "Combination", "Normal"],
    tip: "Dehydrated skin can benefit from hyaluronic acid regardless of your skin type.",
  },
]

const Quiz = () => {
  const [currentQ, setCurrentQ] = useState(0)
  const [selected, setSelected] = useState(null)
  const [answered, setAnswered] = useState(false)
  const [skinScores, setSkinScores] = useState({})
  const [finished, setFinished] = useState(false)
  const [recommendations, setRecommendations] = useState(null)
  const [previousResult, setPreviousResult] = useState(null)
  const [checkingResult, setCheckingResult] = useState(true)
  const [retaking, setRetaking] = useState(false)

  const q = quizData[currentQ]
  const progress = ((currentQ + 1) / quizData.length) * 100

  const handleSelect = (idx) => {
    if (answered) return
    setSelected(idx)
    setAnswered(true)

    // Track skin type based on answer
    if (q.skinMap) {
      const chosenType = q.skinMap[idx]
      setSkinScores((prev) => ({
        ...prev,
        [chosenType]: (prev[chosenType] || 0) + 1,
      }))
    }
  }

  useEffect(() => {
    const checkPreviousResult = async () => {
      const token = localStorage.getItem("skinlens_token")
      if (!token) {
        setCheckingResult(false)
        return
      }
      try {
        const res = await fetch(`${API}/api/quiz/my-result`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        if (data.has_result) setPreviousResult(data)
      } catch (err) {
        console.error(err)
      } finally {
        setCheckingResult(false)
      }
    }
    checkPreviousResult()
  }, [])

  const nextQuestion = async () => {
    if (currentQ < quizData.length - 1) {
      setCurrentQ((c) => c + 1)
      setSelected(null)
      setAnswered(false)
    } else {
      // Finished!
      setFinished(true)

      // Determine skin type from accumulated scores
      const bestType =
        Object.entries(skinScores).sort((a, b) => b[1] - a[1])[0]?.[0] ||
        "Normal"

      try {
        const fd = new FormData()
        fd.append("skin_type", bestType)
        fd.append("sensitivities", "none")
        const res = await fetch(`${API}/api/quiz/recommendations`, {
          method: "POST",
          body: fd,
        })
        const data = await res.json()
        setRecommendations(data)

        const token = localStorage.getItem("skinlens_token")
        if (token) {
          const savefd = new FormData()
          savefd.append("skin_type", bestType)
          savefd.append("sensitivities", "none")

          await fetch(`${API}/api/quiz/save`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: savefd,
          })

          // Update state so Retake shows on next visit
          setPreviousResult({
            has_result: true,
            skin_type: bestType,
            taken_on: new Date().toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            }),
            recommended_ingredients: data.recommended_ingredients,
          })
        }
      } catch (err) {
        console.error(err)
      }
    }
  }

  const getOptionClass = (idx) => {
    if (!answered) return selected === idx ? "selected" : ""
    return idx === selected ? "selected" : ""
  }

  if (finished) {
    const bestType =
      Object.entries(skinScores).sort((a, b) => b[1] - a[1])[0]?.[0] || "Normal"
    return (
      <div className="fade-in-up">
        <Container className="py-5">
          <div className="text-center mb-5">
            <h1 style={{ fontSize: "2.6rem" }}>Your Results</h1>
            <p style={{ color: "var(--pc-muted)" }}>
              Here's what we learned about your skin
            </p>
          </div>

          <Row className="g-4 justify-content-center">
            <Col md={8}>
              <div className="pc-card p-5 text-center">
                <div
                  className="rounded-circle mx-auto d-flex align-items-center justify-content-center mb-3"
                  style={{
                    width: 80,
                    height: 80,
                    background: "var(--pc-gold-light)",
                  }}
                >
                  <i
                    className="bi bi-person-check fs-2"
                    style={{ color: "var(--pc-gold)" }}
                  ></i>
                </div>
                <h3 style={{ fontFamily: "var(--pc-font-serif)" }}>
                  Skin Type: {bestType}
                </h3>
                <p className="mt-2" style={{ color: "var(--pc-muted)" }}>
                  Based on your answers, your skin profile has been classified
                  as <strong>{bestType}</strong>.
                </p>
              </div>
            </Col>
          </Row>

          {/* Recommendations */}
          {recommendations && (
            <div className="mt-5">
              <h3
                className="text-center mb-4"
                style={{ fontFamily: "var(--pc-font-serif)" }}
              >
                <i
                  className="bi bi-stars me-2"
                  style={{ color: "var(--pc-gold)" }}
                ></i>
                Recommended Ingredients for {recommendations.skin_type} Skin
              </h3>
              <Row className="g-3 justify-content-center">
                {recommendations.recommended_ingredients.map((ing, idx) => (
                  <Col md={4} key={idx}>
                    <div className="pc-card p-4 h-100">
                      <div className="d-flex align-items-center gap-2 mb-2">
                        <i
                          className="bi bi-check-circle-fill"
                          style={{ color: "var(--pc-safe)" }}
                        ></i>
                        <strong>{ing.name}</strong>
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
                  </Col>
                ))}
              </Row>
            </div>
          )}

          <div className="text-center mt-5">
            <button
              className="btn btn-pc-primary"
              onClick={() => {
                setCurrentQ(0)
                setSelected(null)
                setAnswered(false)
                setSkinScores({})
                setFinished(false)
                setRecommendations(null)
                setRetaking(false)
              }}
            >
              <i className="bi bi-arrow-repeat me-2"></i>Retake Quiz
            </button>
          </div>
        </Container>
      </div>
    )
  }

  if (checkingResult) {
    return (
      <div className="fade-in-up">
        <Container className="py-5">
          {/* Header skeleton */}
          <div className="text-center mb-5">
            <Skeleton width={300} height={48} className="mx-auto mb-3" />
            <Skeleton width={400} height={20} className="mx-auto" />
          </div>

          {/* Skin type card skeleton */}
          <Row className="g-4 justify-content-center">
            <Col md={8}>
              <div className="pc-card p-5 text-center">
                <Skeleton
                  circle
                  width={80}
                  height={80}
                  className="mx-auto mb-3"
                />
                <Skeleton width={200} height={28} className="mx-auto mb-3" />
                <Skeleton width={350} height={16} className="mx-auto mb-2" />
                <Skeleton width={250} height={14} className="mx-auto" />
              </div>
            </Col>
          </Row>

          {/* Recommendations section skeleton */}
          <div className="mt-5">
            <Skeleton width={400} height={32} className="mx-auto  mb-4" />
            <Row className="g-3 justify-content-center">
              {[1, 2, 3].map((idx) => (
                <Col md={4} key={idx}>
                  <div className="pc-card p-4 h-100">
                    <div className="d-flex align-items-center gap-2 mb-2">
                      <Skeleton circle width={20} height={20} />
                      <Skeleton width="70%" height={18} />
                    </div>
                    <Skeleton width="90%" height={14} className="mb-1" />
                    <Skeleton width="80%" height={14} className="mb-1" />
                    <Skeleton width="60%" height={14} />
                  </div>
                </Col>
              ))}
            </Row>
          </div>

          {/* Button skeleton */}
          <div className="text-center mt-5">
            <Skeleton width={150} height={44} className="mx-auto rounded" />
          </div>
        </Container>
      </div>
    )
  }

  // Previous result exists and not retaking
  if (previousResult && !retaking) {
    return (
      <div className="fade-in-up">
        <Container className="py-5">
          <div className="text-center mb-5">
            <h1 style={{ fontSize: "2.6rem" }}>Your Results</h1>
            <p style={{ color: "var(--pc-muted)" }}>
              Here's what we learned about your skin
            </p>
          </div>

          <Row className="g-4 justify-content-center">
            <Col md={8}>
              <div className="pc-card p-5 text-center">
                <div
                  className="rounded-circle mx-auto d-flex align-items-center justify-content-center mb-3"
                  style={{
                    width: 80,
                    height: 80,
                    background: "var(--pc-gold-light)",
                  }}
                >
                  <i
                    className="bi bi-person-check fs-2"
                    style={{ color: "var(--pc-gold)" }}
                  ></i>
                </div>
                <h3 style={{ fontFamily: "var(--pc-font-serif)" }}>
                  Skin Type: {previousResult.skin_type}
                </h3>
                <p className="mt-2" style={{ color: "var(--pc-muted)" }}>
                  Based on your previous quiz, your skin profile has been
                  classified as <strong>{previousResult.skin_type}</strong>.
                </p>
                <p style={{ color: "var(--pc-muted)", fontSize: "0.88rem" }}>
                  Quiz taken on {previousResult.taken_on}
                </p>
              </div>
            </Col>
          </Row>

          {/* Recommendations */}
          {previousResult.recommended_ingredients && (
            <div className="mt-5">
              <h3
                className="text-center mb-4"
                style={{ fontFamily: "var(--pc-font-serif)" }}
              >
                <i
                  className="bi bi-stars me-2"
                  style={{ color: "var(--pc-gold)" }}
                ></i>
                Recommended Ingredients for {previousResult.skin_type} Skin
              </h3>
              <Row className="g-3 justify-content-center">
                {previousResult.recommended_ingredients.map((ing, idx) => (
                  <Col md={4} key={idx}>
                    <div className="pc-card p-4 h-100">
                      <div className="d-flex align-items-center gap-2 mb-2">
                        <i
                          className="bi bi-check-circle-fill"
                          style={{ color: "var(--pc-safe)" }}
                        ></i>
                        <strong>{ing.name}</strong>
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
                  </Col>
                ))}
              </Row>
            </div>
          )}

          <div className="text-center mt-5">
            <button
              className="btn btn-pc-primary"
              onClick={() => setRetaking(true)}
            >
              <i className="bi bi-arrow-repeat me-2"></i>Retake Quiz
            </button>
          </div>
        </Container>
      </div>
    )
  }

  return (
    <div
      className="fade-in-up"
      style={{ background: "var(--pc-cream)", minHeight: "80vh" }}
    >
      <Container className="py-4">
        {/* Top bar */}
        <div className="d-flex justify-content-between align-items-center mb-3 pt-3">
          <div>
            <small
              className="text-uppercase fw-semibold"
              style={{
                letterSpacing: 2,
                color: "var(--pc-muted)",
                fontSize: "0.75rem",
              }}
            >
              Question {currentQ + 1} of {quizData.length}
            </small>
            <div className="pc-progress mt-2" style={{ width: 200 }}>
              <div
                className="progress-bar"
                style={{ width: `${progress}%`, transition: "width 0.5s" }}
              ></div>
            </div>
          </div>
          <div className="text-end">
            <small className="fst-italic" style={{ color: "var(--pc-gold)" }}>
              Topic: {q.topic}
            </small>
          </div>
        </div>

        {/* Question Card */}
        <div
          className="pc-card p-5 text-center mx-auto"
          style={{ maxWidth: 780 }}
        >
          <span
            className="badge rounded-pill bg-light text-dark border mb-4"
            style={{ fontSize: "0.72rem", letterSpacing: 1 }}
          >
            {q.category}
          </span>

          <h2
            className="mb-5"
            style={{
              fontSize: "1.8rem",
              lineHeight: 1.3,
              maxWidth: 560,
              margin: "0 auto 40px",
            }}
          >
            {q.question}
          </h2>

          <Row className="g-3 justify-content-center">
            {q.options.map((opt, idx) => (
              <Col md={6} key={idx}>
                <div
                  className={`quiz-option ${getOptionClass(idx)}`}
                  onClick={() => handleSelect(idx)}
                >
                  <span className="quiz-letter">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span style={{ fontSize: "0.95rem", fontWeight: 500 }}>
                    {opt}
                  </span>
                </div>
              </Col>
            ))}
          </Row>

          {answered && (
            <div className="mt-4">
              <hr />
              <button
                className="btn btn-pc-primary mt-3"
                onClick={nextQuestion}
              >
                {currentQ < quizData.length - 1
                  ? "Next Question →"
                  : "See My Results →"}
              </button>
            </div>
          )}
        </div>

        {/* Expert Tip */}
        {answered && q.tip && (
          <div
            className="pc-card p-4 mt-4 d-flex gap-3 mx-auto fade-in-up"
            style={{ maxWidth: 780 }}
          >
            <div
              className="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
              style={{
                width: 44,
                height: 44,
                background: "var(--pc-gold-light)",
              }}
            >
              <i
                className="bi bi-lightbulb-fill"
                style={{ color: "var(--pc-gold)" }}
              ></i>
            </div>
            <div>
              <strong
                className="text-uppercase"
                style={{ fontSize: "0.75rem", letterSpacing: 1 }}
              >
                Expert Tip
              </strong>
              <p
                className="mb-0 mt-1"
                style={{ color: "var(--pc-muted)", fontSize: "0.9rem" }}
              >
                {q.tip}
              </p>
            </div>
          </div>
        )}
      </Container>
    </div>
  )
}

export default Quiz
