import React, { createContext, useContext, useState, useEffect } from "react"

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedUser =
      localStorage.getItem("skinlens_user") ||
      sessionStorage.getItem("skinlens_user")

    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser))
      } catch (error) {
        localStorage.removeItem("skinlens_user")
        sessionStorage.removeItem("skinlens_user")
      }
    }
    setLoading(false)
  }, [])

  const login = (userData, token = null, remember = true) => {
    setUser(userData)

    const storage = remember ? localStorage : sessionStorage

    storage.setItem("skinlens_user", JSON.stringify(userData))
    if (token) {
      storage.setItem("skinlens_token", token)
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem("skinlens_user")
    localStorage.removeItem("skinlens_token")
    sessionStorage.removeItem("skinlens_user")
    sessionStorage.removeItem("skinlens_token")
  }

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    loading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
