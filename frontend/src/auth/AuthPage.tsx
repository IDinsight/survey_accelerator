"use client"

import type React from "react"
import { useState, useCallback, useEffect } from "react"
import { login, resetPassword, registerUser } from "../api"
import { toast } from "sonner"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { Label } from "../components/ui/label"
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react"
import Particles from "react-tsparticles"
import type { Engine } from "tsparticles-engine"
import { loadSlim } from "tsparticles-slim"

type AuthMode = "login" | "signup" | "forgot"

interface AuthPageProps {
  onLoginSuccess: (user: {
    email: string
    access_token: string
    user_id: number
    created_at: string
    action_taken: string
  }) => void
}

const MIN_PASSWORD_LENGTH = 8

const AuthPage: React.FC<AuthPageProps> = ({ onLoginSuccess }) => {
  const [authMode, setAuthMode] = useState<AuthMode>("login")
  const [isResetting, setIsResetting] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    organization: "",
    role: "",
  })

  // Password validation states
  const [passwordLengthValid, setPasswordLengthValid] = useState(false)
  const [passwordsMatch, setPasswordsMatch] = useState(false)

  // Validate password on change
  useEffect(() => {
    setPasswordLengthValid(formData.password.length >= MIN_PASSWORD_LENGTH)
    setPasswordsMatch(formData.password === formData.confirmPassword && formData.confirmPassword !== "")
  }, [formData.password, formData.confirmPassword])

  const particlesInit = useCallback(async (engine: Engine) => {
    await loadSlim(engine)
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (authMode === "forgot") {
      setIsResetting(true)
      try {
        await resetPassword(formData.email)
        toast("Password reset email sent", {
          description: "Please check your email for the temporary password.",
          duration: 4000, // 4 secs
        })
        setAuthMode("login")
      } catch (error: any) {
        console.error("Password reset error:", error)
        toast(error.message || "Email not found. Please check and try again.", {
          description: "Failed to send password reset email.",
          action: {
            label: "Retry",
            onClick: () => console.log("Retry password reset"),
          },
        })
      } finally {
        setIsResetting(false)
      }
      return
    }

    if (authMode === "signup") {
      // Frontend validation
      if (!passwordLengthValid) {
        toast.error(`Password must be at least ${MIN_PASSWORD_LENGTH} characters`)
        return
      }

      if (!passwordsMatch) {
        toast.error("Passwords don't match")
        return
      }
    }

    setIsSubmitting(true)

    try {
      if (authMode === "login") {
        const response = await login(formData.email, formData.password)
        onLoginSuccess(response)
      } else if (authMode === "signup") {
        await registerUser(formData.email, formData.password, formData.organization, formData.role)
        toast("User registered successfully!", {
          description: "You can proceed by signing in.",
        })
        // After successful signup, return to login mode.
        setAuthMode("login")
      }
    } catch (error: any) {
      console.error("Authentication error:", error)
      let toastMessage = ""
      let toastDescription = ""
      if (error.response?.status === 401) {
        toastMessage = "Incorrect password"
        toastDescription = "Please try again or select 'Forgot Password'"
      } else if (error.response?.status === 404) {
        toastMessage = "Email not recognized"
        toastDescription = "Please check your credentials or sign up."
      } else {
        toastMessage = error.message || "Authentication error"
        toastDescription = "Please check your credentials or sign up."
      }
      toast(toastMessage, {
        description: toastDescription,
        duration: 4000, // 4secs
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setFormData({
      email: "",
      password: "",
      confirmPassword: "",
      organization: "",
      role: "",
    })
  }

  // When changing auth mode, reset the form
  const changeAuthMode = (mode: AuthMode) => {
    resetForm()
    setAuthMode(mode)
  }

  return (
    <div className="flex min-h-screen bg-black">
      {/* Particles Background */}
      <div className="absolute inset-0 z-0">
        <Particles
          id="tsparticles"
          init={particlesInit}
          options={{
            background: { color: { value: "#111130" } },
            fpsLimit: 60,
            interactivity: {
              events: {
                onClick: { enable: true, mode: "push" },
                onHover: { enable: true, mode: "attract" },
                resize: true,
              },
              modes: {
                attract: { distance: 200, duration: 0.8, speed: 2.7 },
                push: { quantity: 4 },
              },
            },
            particles: {
              color: { value: "#FF4500" },
              links: {
                color: "#FFA500",
                distance: 150,
                enable: true,
                opacity: 0.5,
                width: 2,
              },
              move: {
                direction: "none",
                enable: true,
                outModes: { default: "bounce" },
                random: false,
                speed: 0.2,
                straight: false,
              },
              number: { density: { enable: true, area: 800 }, value: 100 },
              opacity: { value: 0.5 },
              shape: { type: "circle" },
              size: { value: { min: 1, max: 5 } },
            },
            detectRetina: true,
          }}
          className="h-full w-full"
        />
      </div>

      {/* Logo and Text Area */}
      <div className="hidden md:flex md:w-3/4 relative z-10 justify-center items-center">
        <div className="p-8 text-center">
          <img src="/SurveyAcceleratorLogo-White.svg" alt="Survey Accelerator Logo" className="w-[850px] h-auto mb-4" />
          <p className="text-2xl max-w-3xl mx-auto text-white">
            A search engine for the highest quality surveys at your fingertips
            <br />
            <span className="text-yellow-500">Free, fast and completely open source </span>
          </p>
        </div>
      </div>

      {/* Form Side */}
      <div className="w-full md:w-1/3 flex items-center justify-center p-4 md:p-8 relative z-10">
        <Card className="w-full max-w-md border-none bg-black/20 backdrop-blur-sm shadow-xl text-white">
          <CardHeader>
            <CardTitle className="text-center text-2xl">
              {authMode === "login" ? "Sign In" : authMode === "signup" ? "Sign Up" : "Reset Password"}
            </CardTitle>
            {authMode === "forgot" && (
              <CardDescription className="text-center">
                Enter your email to receive a password reset link
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-white">
                  Email
                </Label>
                <Input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="text-white"
                />
              </div>

              {/* For Signup: Organization and Role */}
              {authMode === "signup" && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="organization" className="text-white">
                      Organization
                    </Label>
                    <Input
                      type="text"
                      id="organization"
                      name="organization"
                      placeholder="Your Organization"
                      value={formData.organization}
                      onChange={handleChange}
                      required
                      className="text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role" className="text-white">
                      Role
                    </Label>
                    <Input
                      type="text"
                      id="role"
                      name="role"
                      placeholder="Your Role"
                      value={formData.role}
                      onChange={handleChange}
                      required
                      className="text-white"
                    />
                  </div>
                </>
              )}

              {/* Password Field */}
              {authMode !== "forgot" && (
                <div className="space-y-1">
                  <Label htmlFor="password" className="text-white">
                    Password
                  </Label>
                  <Input
                    type="password"
                    id="password"
                    name="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className={`text-white ${
                      authMode === "signup" && formData.password && !passwordLengthValid ? "border-red-500" : ""
                    }`}
                  />
                  {authMode === "signup" && formData.password && (
                    <p
                      className={`text-xs flex items-center mt-1 ${
                        passwordLengthValid ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {passwordLengthValid ? (
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                      ) : (
                        <AlertCircle className="h-3 w-3 mr-1" />
                      )}
                      Password must be at least {MIN_PASSWORD_LENGTH} characters
                    </p>
                  )}
                </div>
              )}

              {/* For Signup: Confirm Password Field */}
              {authMode === "signup" && (
                <div className="space-y-1">
                  <Label htmlFor="confirmPassword" className="text-white">
                    Confirm Password
                  </Label>
                  <Input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    className={`text-white ${formData.confirmPassword && !passwordsMatch ? "border-red-500" : ""}`}
                  />
                  {formData.confirmPassword && (
                    <p
                      className={`text-xs flex items-center mt-1 ${passwordsMatch ? "text-green-400" : "text-red-400"}`}
                    >
                      {passwordsMatch ? (
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                      ) : (
                        <AlertCircle className="h-3 w-3 mr-1" />
                      )}
                      {passwordsMatch ? "Passwords match" : "Passwords don't match"}
                    </p>
                  )}
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-white text-black"
                disabled={
                  (authMode === "forgot" && isResetting) ||
                  isSubmitting ||
                  (authMode === "signup" && (!passwordLengthValid || !passwordsMatch))
                }
              >
                {(isResetting || isSubmitting) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {authMode === "login" ? "Sign In" : authMode === "signup" ? "Sign Up" : "Reset Password"}
              </Button>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            {authMode === "login" && (
              <Button variant="link" className="px-0 text-yellow-500" onClick={() => changeAuthMode("forgot")}>
                Forgot Password?
              </Button>
            )}

            <div className="text-center w-full">
              {authMode === "login" ? (
                <div className="flex items-center justify-center gap-1">
                  <span className="text-sm text-white">Don't have an account?</span>
                  <Button variant="link" className="p-0 h-auto text-yellow-500" onClick={() => changeAuthMode("signup")}>
                    Sign Up
                  </Button>
                </div>
              ) : authMode === "signup" ? (
                <div className="flex items-center justify-center gap-1">
                  <span className="text-sm text-white">Already have an account?</span>
                  <Button variant="link" className="p-0 h-auto text-white" onClick={() => changeAuthMode("login")}>
                    Sign In
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-1">
                  <span className="text-sm text-white">Remembered your password?</span>
                  <Button variant="link" className="p-0 h-auto text-yellow-500" onClick={() => changeAuthMode("login")}>
                    Sign In
                  </Button>
                </div>
              )}
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}

export default AuthPage
