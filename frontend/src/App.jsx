import { useState, useEffect } from "react"
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  NavLink,
  useLocation,
  Outlet,
  Navigate,
} from "react-router-dom"
import { Navbar, Nav, Container } from "react-bootstrap"
import { useAuth } from "./AuthContext"
import Home from "./pages/Home"
import Analyze from "./pages/Analyze"
import Encyclopedia from "./pages/Encyclopedia"
import Quiz from "./pages/Quiz"
import Login from "./pages/Login"

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ paddingTop: "80px" }}>
        <Container className="py-5">
          <Row className="align-items-center g-5">
            <Col lg={6}>
              <Skeleton width={120} height={28} className="mb-3" />
              <Skeleton width="80%" height={50} className="mb-2" />
              <Skeleton width="60%" height={50} className="mb-4" />
              <Skeleton width="90%" height={16} className="mb-2" />
              <Skeleton width="75%" height={16} className="mb-2" />
              <Skeleton width="60%" height={16} className="mb-4" />
              <div className="d-flex gap-3">
                <Skeleton width={140} height={44} borderRadius={40} />
                <Skeleton width={140} height={44} borderRadius={40} />
              </div>
            </Col>
            <Col lg={6} className="text-center d-none d-lg-block">
              <Skeleton width="100%" height={400} borderRadius={24} />
            </Col>
          </Row>
        </Container>
      </div>
    )
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

const AppNavbar = () => {
  const [expanded, setExpanded] = useState(false)
  const location = useLocation()
  const { logout, isAuthenticated, user } = useAuth()

  useEffect(() => {
    setExpanded(false)
  }, [location.pathname])

  return (
    <Navbar
      expand="lg"
      expanded={expanded}
      onToggle={() => setExpanded(!expanded)}
      className="pc-navbar"
      fixed="top"
      style={{
        backdropFilter: "blur(12px)",
        backgroundColor: "rgba(255,255,255,0.85)",
      }}
    >
      <Container>
        <Navbar.Brand as={Link} to="/" onClick={() => setExpanded(false)}>
          <img src="/logo.webp" alt="Skin Lens" className="navbar-logo" />
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="main-nav" />
        <Navbar.Collapse id="main-nav">
          <Nav className="mx-auto">
            <Nav.Link as={NavLink} to="/analyze">
              Analysis
            </Nav.Link>
            <Nav.Link as={NavLink} to="/ingredients">
              Ingredients
            </Nav.Link>
            <Nav.Link as={NavLink} to="/quiz">
              Quiz
            </Nav.Link>
          </Nav>
          {isAuthenticated ? (
            <div className="d-flex align-items-center gap-3">
              <div className="d-flex align-items-center gap-2">
                {user?.picture && (
                  <img
                    src={user.picture}
                    alt={user?.name || "User"}
                    className="rounded-circle"
                    referrerPolicy="no-referrer" // ← add this line
                    style={{
                      width: "32px",
                      height: "32px",
                      objectFit: "cover",
                    }}
                  />
                )}
                <span className="text-dark fw-medium">
                  {user?.name || user?.email || "User"}
                </span>
              </div>
              <button
                className="btn btn-outline-secondary btn-sm"
                onClick={() => {
                  logout()
                  setExpanded(false)
                }}
              >
                Logout
              </button>
            </div>
          ) : (
            <Link to="/analyze" className="btn btn-pc-primary btn-sm">
              Get Started
            </Link>
          )}
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}

const Footer = () => {
  return (
    <footer className="pc-footer">
      <Container>
        <div className="row">
          <div className="col-md-4 mb-4">
            <Link to="/" className="d-inline-block mb-3">
              <img src="/logo.webp" alt="Skin Lens" className="footer-logo" />
            </Link>
            <p style={{ maxWidth: 300 }}>
              The world's most sophisticated cosmetic ingredient analyzer.
              Dedicated to transparency in the beauty industry.
            </p>
          </div>
          <div className="col-md-2 offset-md-2 mb-4">
            <h6>Platform</h6>
            <Link to="/">How it Works</Link>
            <Link to="/">Pricing</Link>
            <Link to="/">API Access</Link>
          </div>
          <div className="col-md-2 mb-4">
            <h6>Company</h6>
            <Link to="/">Privacy Policy</Link>
            <Link to="/">Terms of Service</Link>
          </div>
        </div>
        <hr style={{ borderColor: "var(--pc-border)" }} />
        <div className="d-flex justify-content-between align-items-center">
          <small>© 2026 Skin Lens. All rights reserved.</small>
          <div className="d-flex gap-3">
            <i className="bi bi-globe2"></i>
            <i className="bi bi-envelope"></i>
          </div>
        </div>
      </Container>
    </footer>
  )
}

/** Layout wrapper that includes navbar + footer for main pages */
const MainLayout = () => (
  <>
    <AppNavbar />
    <main style={{ paddingTop: "80px", minHeight: "100vh" }}>
      <Outlet />
    </main>
    <Footer />
  </>
)

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Standalone full-page routes (no navbar/footer) */}
        <Route path="/login" element={<Login />} />
        {/* Main app routes with shared layout - protected */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/ingredients" element={<Encyclopedia />} />
          <Route path="/quiz" element={<Quiz />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
