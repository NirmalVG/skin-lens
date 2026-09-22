import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useGoogleLogin } from "@react-oauth/google"
import { useAuth } from "../AuthContext"
import "./Login.css"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

const GoogleIcon = () => (
  <svg
    className="google-icon"
    viewBox="0 0 48 48"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      fill="#EA4335"
      d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
    />
    <path
      fill="#4285F4"
      d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
    />
    <path
      fill="#FBBC05"
      d="M10.53 28.59a14.5 14.5 0 0 1 0-9.18l-7.98-6.19a24.003 24.003 0 0 0 0 21.56l7.98-6.19z"
    />
    <path
      fill="#34A853"
      d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
    />
  </svg>
)

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        setLoading(true)
        const res = await fetch(`${API}/api/auth/google`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: tokenResponse.access_token }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || "Google login failed")
        login(data.user, data.access_token, true)
        navigate("/")
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    onError: () => setError("Google login failed"),
    flow: "implicit",
  })

  return (
    <div className="login-page">
      {/* Left Panel */}
      <div className="login-brand">
        <Link to="/" className="login-brand-logo">
          <img src="/logo.webp" alt="Skin Lens" className="navbar-logo" />
        </Link>
        <div className="login-brand-visual login-animate">
          <img
            src="/login-hero.png"
            alt="Cosmetic ingredient analysis"
            className="login-brand-image"
          />
          <h2 className="login-brand-heading">
            Science-backed clarity for your skin.
          </h2>
          <p className="login-brand-subtitle">
            Decipher ingredients with surgical precision and clinical
            transparency.
          </p>
        </div>
      </div>

      {/* Right Panel */}
      <div className="login-form-side">
        <div className="login-form-container">
          <h1 className="login-form-heading text-center login-animate">
            Welcome to Skin Lens
          </h1>
          <p className="login-form-subtitle text-center login-animate login-animate-delay-1">
            Sign in to access your personalized skincare analysis.
          </p>

          {error && (
            <div
              className="login-animate"
              style={{
                background: "#fff0f0",
                border: "1.5px solid #f5c6c6",
                color: "#c0392b",
                borderRadius: "10px",
                padding: "12px 16px",
                fontSize: "0.88rem",
                marginBottom: "20px",
                textAlign: "center",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="button"
            className="btn-google-sso login-animate login-animate-delay-2"
            onClick={() => handleGoogleLogin()}
            disabled={loading}
          >
            <GoogleIcon />
            {loading ? "Signing in..." : "Sign in with Google"}
          </button>
        </div>
      </div>
    </div>
  )
}
