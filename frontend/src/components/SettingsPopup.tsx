"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Slider } from "./ui/slider"
import { toast } from "sonner"
import { ChevronDown, ChevronUp } from "lucide-react"

interface User {
  email: string
  user_id: number
}

interface SettingsPopupProps {
  user: User
  onClose: () => void
  onUpdateResultsCount: (count: number) => void
  resultsCount: number
}

const SettingsPopup: React.FC<SettingsPopupProps> = ({ user, onClose, onUpdateResultsCount, resultsCount }) => {
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localResultsCount, setLocalResultsCount] = useState(resultsCount)

  // Ensure user object has required properties
  const safeUser = {
    email: user?.email || "Not available",
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()

    if (newPassword !== confirmPassword) {
      toast.error("New passwords don't match")
      return
    }

    setIsSubmitting(true)

    try {
      // Use the correct endpoint from your FastAPI backend
      const response = await fetch("http://localhost:8000/users/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      // Handle non-JSON responses
      const contentType = response.headers.get("content-type")
      let errorMessage = "Failed to change password"

      if (contentType && contentType.includes("application/json")) {
        const data = await response.json()
        if (!response.ok) {
          errorMessage = data.detail || errorMessage
          throw new Error(errorMessage)
        }

        // Success path
        toast.success(data.message || "Password changed successfully")
        setCurrentPassword("")
        setNewPassword("")
        setConfirmPassword("")
        setShowPasswordChange(false)
      } else {
        // Handle non-JSON response (like HTML error pages)
        const text = await response.text()
        console.error("Non-JSON response:", text)
        throw new Error("Server returned an invalid response. Please try again later.")
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to change password")
      console.error("Password change error:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResultsCountChange = (value: number[]) => {
    setLocalResultsCount(value[0])
  }

  const saveResultsCount = async () => {
    try {
      // Save to localStorage as a fallback
      localStorage.setItem("resultsCount", localResultsCount.toString())

      // Save to backend if you have an API endpoint for it
      const response = await fetch("http://localhost:8000/users/preferences", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          results_count: localResultsCount,
        }),
      }).catch((err) => {
        console.error("Failed to save preferences to server:", err)
        // Continue even if server save fails
        return null
      })

      // Update local state
      onUpdateResultsCount(localResultsCount)
      toast.success(`Results count updated to ${localResultsCount}`)
    } catch (error) {
      console.error("Error saving preferences:", error)
      toast.error("Failed to save preferences")
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <Card className="w-[90%] max-w-md bg-black/30 backdrop-blur-sm text-white border-0">
        <CardHeader className="pb-2">
          <CardTitle>Settings</CardTitle>
          <CardDescription className="text-gray-300">Manage your account and preferences</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* User Information */}
          <div>
            <h3 className="text-sm font-medium mb-2">User Information</h3>
            <p className="text-sm text-gray-300">Email: {safeUser.email}</p>
          </div>

          {/* Password Change Toggle */}
          <div>
            <Button
              type="button"
              variant="ghost"
              className="flex w-full justify-between items-center p-0 hover:bg-transparent hover:text-white"
              onClick={() => setShowPasswordChange(!showPasswordChange)}
            >
              <span className="text-sm font-medium">Change Password</span>
              {showPasswordChange ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>

            {showPasswordChange && (
              <form onSubmit={handlePasswordChange} className="mt-3 space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="current-password">Current Password</Label>
                  <Input
                    id="current-password"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="bg-black/30 border-gray-700"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="new-password">New Password</Label>
                  <Input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="bg-black/30 border-gray-700"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="bg-black/30 border-gray-700"
                    required
                  />
                </div>

                <Button type="submit" className="w-full bg-[#CC7722] hover:bg-[#b88a01]" disabled={isSubmitting}>
                  {isSubmitting ? "Changing..." : "Change Password"}
                </Button>
              </form>
            )}
          </div>

          {/* Search Results Count Preference */}
          <div>
            <h3 className="text-sm font-medium mb-2">Search Results Count</h3>
            <p className="text-sm text-gray-300 mb-4">
              Set the maximum number of results to display: <span className="font-bold">{localResultsCount}</span>
            </p>

            <div className="py-2">
              <Slider
                defaultValue={[localResultsCount]}
                max={50}
                min={5}
                step={5}
                onValueChange={handleResultsCountChange}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>5</span>
                <span>25</span>
                <span>50</span>
              </div>
            </div>

            <Button onClick={saveResultsCount} className="w-full bg-[#CC7722] hover:bg-[#b88a01] mt-2">
              Save Preferences
            </Button>
          </div>

          {/* Close Button */}
          <div className="flex justify-end pt-2">
            <Button variant="outline" onClick={onClose} className="border-gray-600 text-white hover:bg-white/10">
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default SettingsPopup
