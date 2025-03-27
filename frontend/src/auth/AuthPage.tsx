"use client"

import type React from "react"
import { useState, useCallback } from "react"
import { login, resetPassword } from "../api"
import { toast } from "sonner"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { Label } from "../components/ui/label"
import { Loader2 } from "lucide-react"
import Particles from "react-tsparticles"
import type { Engine } from "tsparticles-engine"
// Import the slim bundle instead
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

const AuthPage: React.FC<AuthPageProps> = ({ onLoginSuccess }) => {
  const [authMode, setAuthMode] = useState<AuthMode>("login")
  const [isResetting, setIsResetting] = useState<boolean>(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  })

  // Updated initialization function using loadSlim
  const particlesInit = useCallback(async (engine: Engine) => {
    // Use loadSlim instead of loadFull to avoid compatibility issues
    await loadSlim(engine)
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (authMode === "forgot") {
      // Only email is needed.
      setIsResetting(true)
      try {
        await resetPassword(formData.email)
        toast("Password reset email sent", {
          description: "Please check your email for the temporary password.",
        })
        // Optionally, switch back to login mode.
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

    // For login and signup.
    if (authMode !== "login" && formData.password !== formData.confirmPassword) {
      toast("Passwords do not match", {
        description: "Please ensure both passwords are identical.",
      })
      return
    }

    try {
      if (authMode === "login") {
        const response = await login(formData.email, formData.password)
        onLoginSuccess(response)
      } else {
        // Registration logic here...
        console.log("Registering...", formData)
      }
    } catch (error: any) {
      console.error("Authentication error:", error)
      toast(error.message || "Incorrect email or password.", {
        description: "Please check your credentials and try again.",
      })
    }

    // Clear form data after submission.
    setFormData({ email: "", password: "", confirmPassword: "" })
  }

  return (
    <div className="flex min-h-screen bg-black">
      {/* Particles Background - Using a simplified configuration */}
      <div className="absolute inset-0 z-0">
      <Particles
  id="tsparticles"
  init={particlesInit}
  options={{
    background: {
      color: { value: "#111130" },
    },
    fpsLimit: 60,
    interactivity: {
      events: {
        onClick: {
          enable: true,
          mode: "push", // you can still keep push for click events
        },
        onHover: {
          enable: true,
          mode: "attract", // switch from "repulse" to "attract"
        },
        resize: true,
      },
      modes: {
        attract: {
          distance: 200, // distance at which particles are attracted
          duration: 0.8, // duration of the attraction effect
          speed: 3.2,      // speed factor for the attraction movement
        },
        push: {
          quantity: 4,
        },
        // you can define other modes if needed
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
        speed: 1,
        straight: false,
      },
      number: {
        density: {
          enable: true,
          area: 800,
        },
        value: 100,
      },
      opacity: {
        value: 0.5,
      },
      shape: {
        type: "circle",
      },
      size: {
        value: { min: 1, max: 5 },
      },
    },
    detectRetina: true,
  }}
  className="h-full w-full"
/>

      </div>

      {/* Logo and Text Area */}
        <div className="hidden md:flex md:w-2/3 relative z-10 justify-center items-center">
          <div className="p-8 text-center">
            <img
              src="/SurveyAcceleratorLogo-White.svg"
              alt="Survey Accelerator Logo"
              className="max-w-full h-auto mb-4"
            />
            <p className="text-xl max-w-lg mx-auto text-white">
              Search a database of the highest quality surveys in seconds.
            </p>
          </div>
        </div>

      {/* Form Side */}
      <div className="w-full md:w-1/3 flex items-center justify-center p-4 md:p-8 relative z-10">
  <Card className="w-full max-w-md border-none bg-black/20 backdrop-blur-sm shadow-xl text-white">
    <CardHeader>
      <CardTitle className="text-center text-2xl">
        {authMode === "login"
          ? "Sign In"
          : authMode === "signup"
          ? "Sign Up"
          : "Reset Password"}
      </CardTitle>
      {authMode === "forgot" && (
        <CardDescription className="text-center">
          Enter your email to receive a password reset link
        </CardDescription>
      )}
    </CardHeader>
    <CardContent>
      <form onSubmit={handleSubmit} className="space-y-4">
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

        {authMode !== "forgot" && (
          <div className="space-y-2">
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
              className="text-white"
            />
          </div>
        )}

        {authMode === "signup" && (
          <div className="space-y-2">
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
              className="text-white"
            />
          </div>
        )}

        <Button
          type="submit"
          className={`w-full ${
            authMode === "login" ? "bg-white text-black" : ""
          }`}
          disabled={authMode === "forgot" && isResetting}
        >
          {isResetting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {authMode === "login"
            ? "Sign In"
            : authMode === "signup"
            ? "Sign Up"
            : "Reset Password"}
        </Button>
      </form>
    </CardContent>
    <CardFooter className="flex flex-col space-y-4">
      {authMode === "login" && (
        <Button
          variant="link"
          className="px-0 text-white"
          onClick={() => setAuthMode("forgot")}
        >
          Forgot Password?
        </Button>
      )}

      <div className="text-center w-full">
        {authMode === "login" ? (
          <div className="flex items-center justify-center gap-1">
            <span className="text-sm text-white">
              Don't have an account?
            </span>
            <Button
              variant="link"
              className="p-0 h-auto text-white"
              onClick={() => setAuthMode("signup")}
            >
              Sign Up
            </Button>
          </div>
        ) : authMode === "signup" ? (
          <div className="flex items-center justify-center gap-1">
            <span className="text-sm text-white">
              Already have an account?
            </span>
            <Button
              variant="link"
              className="p-0 h-auto text-white"
              onClick={() => setAuthMode("login")}
            >
              Sign In
            </Button>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-1">
            <span className="text-sm text-white">
              Remembered your password?
            </span>
            <Button
              variant="link"
              className="p-0 h-auto text-white"
              onClick={() => setAuthMode("login")}
            >
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
