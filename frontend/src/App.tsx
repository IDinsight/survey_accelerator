"use client"

import type React from "react"
import { useState, useEffect } from "react"
import AdvancedSearchEngine from "./AdvancedSearchEngine"
import AuthPage from "./auth/AuthPage"
import "./App.css"
import { Toaster } from "sonner"

interface User {
  email: string
  access_token: string
  user_id: number
  // Optionally add other fields, like token expiry.
}

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null)

  // On initial load, try to restore auth state from localStorage.
  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    const storedEmail = localStorage.getItem("email")
    const storedUserId = localStorage.getItem("user_id")
    const tokenExpiry = localStorage.getItem("token_expiry")

    if (storedToken && storedEmail && storedUserId && tokenExpiry) {
      if (Date.now() < Number(tokenExpiry)) {
        setUser({
          email: storedEmail,
          access_token: storedToken,
          user_id: Number(storedUserId),
        })
      } else {
        // Token expired—clear the auth data.
        localStorage.removeItem("token")
        localStorage.removeItem("email")
        localStorage.removeItem("user_id")
        localStorage.removeItem("token_expiry")
      }
    }
  }, [])

  const handleLoginSuccess = (userData: User) => {
    localStorage.setItem("token", userData.access_token)
    localStorage.setItem("email", userData.email)
    localStorage.setItem("user_id", userData.user_id.toString())
    // Set token expiry to 1 day (1440 minutes) from now:
    localStorage.setItem("token_expiry", String(Date.now() + 1440 * 60 * 1000))

    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("email")
    localStorage.removeItem("user_id")
    localStorage.removeItem("token_expiry")
    setUser(null)
  }

  return (
    <>
      <Toaster />
      {user ? (
        <AdvancedSearchEngine
          onLogout={handleLogout}
          user={{
            email: user.email,
            user_id: user.user_id,
          }}
        />
      ) : (
        <AuthPage onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  )
}

export default App
