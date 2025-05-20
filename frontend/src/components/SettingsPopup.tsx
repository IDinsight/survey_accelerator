"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Slider } from "./ui/slider"
import { toast } from "sonner"
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle2 } from "lucide-react"
import { changePassword, updateResultsCountPreference } from "../api"

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

const MIN_PASSWORD_LENGTH = 8

const SettingsPopup: React.FC<SettingsPopupProps> = ({ user, onClose, onUpdateResultsCount, resultsCount }) => {
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localResultsCount, setLocalResultsCount] = useState(resultsCount)
  const [isOpen, setIsOpen] = useState(true)

  // Password validation states
  const [passwordLengthValid, setPasswordLengthValid] = useState(false)
  const [passwordsMatch, setPasswordsMatch] = useState(false)
  const [currentPasswordValid, setCurrentPasswordValid] = useState(false)

  // Ensure user object has required properties
  const safeUser = {
    email: user?.email || "Not available",
  }

  // Validate password on change
  useEffect(() => {
    setPasswordLengthValid(newPassword.length >= MIN_PASSWORD_LENGTH)
    setPasswordsMatch(newPassword === confirmPassword && confirmPassword !== "")
    setCurrentPasswordValid(currentPassword.length >= MIN_PASSWORD_LENGTH)
  }, [newPassword, confirmPassword, currentPassword])

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()

    // Frontend validation
    if (!currentPasswordValid) {
      toast.error(`Current password must be at least ${MIN_PASSWORD_LENGTH} characters`)
      return
    }

    if (!passwordLengthValid) {
      toast.error(`New password must be at least ${MIN_PASSWORD_LENGTH} characters`)
      return
    }

    if (!passwordsMatch) {
      toast.error("New passwords don't match")
      return
    }

    setIsSubmitting(true)

    try {
      // Use the API function to change password
      const response = await changePassword(currentPassword, newPassword)

      // Success path
      toast.success(response.message || "Password changed successfully")
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
      setShowPasswordChange(false)
    } catch (error: any) {
      // Display error message
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

      try {
        // Use the API function to update results count preference
        const response = await updateResultsCountPreference(localResultsCount)
        console.log("Preferences saved successfully:", response)
      } catch (serverError: any) {
        // Log error but continue (we have localStorage as backup)
        console.warn("Could not save preferences to server:", serverError)
      }

      // Update local state
      onUpdateResultsCount(localResultsCount)
      toast.success(`Results count updated to ${localResultsCount}`)
    } catch (error: any) {
      // Ensure we're displaying a string message, not an object
      const errorMessage = error instanceof Error ? error.message : "Failed to save preferences"
      toast.error(errorMessage)
      console.error("Error saving preferences:", error)
    }
  }

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] bg-black/80 backdrop-blur-md text-white border border-white/20 flex flex-col overflow-y-auto">
        <DialogHeader className="pb-2">
          <DialogTitle className="text-white">Settings</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* User Information */}
          <div>
            <h3 className="text-sm font-medium mb-2">User Information</h3>
            <p className="text-sm text-white/70">Email: {safeUser.email}</p>
          </div>

          {/* Password Change Toggle */}
          <div>
            <Button
              type="button"
              variant="ghost"
              className={`flex w-full justify-between items-center ${
                showPasswordChange
                  ? "p-0 hover:bg-transparent hover:text-white"
                  : "border-2 border-white text-white hover:bg-white/10 p-2"
              }`}
              onClick={() => setShowPasswordChange(!showPasswordChange)}
            >
              <span className="text-sm font-medium">Change Password</span>
              {showPasswordChange ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>

            {showPasswordChange && (
              <form onSubmit={handlePasswordChange} className="mt-3 space-y-3 p-3 border border-white/20 rounded-md bg-white/5">
                <div className="space-y-1">
                  <Label htmlFor="current-password">Current Password</Label>
                  <Input
                    id="current-password"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className={`bg-black/30 border-white/20 ${
                      currentPassword && !currentPasswordValid ? "border-red-500" : ""
                    }`}
                    required
                  />
                  {currentPassword && !currentPasswordValid && (
                    <p className="text-xs text-red-400 flex items-center mt-1">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      Password must be at least {MIN_PASSWORD_LENGTH} characters
                    </p>
                  )}
                </div>

                <div className="space-y-1">
                  <Label htmlFor="new-password">New Password</Label>
                  <Input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className={`bg-black/30 border-white/20 ${
                      newPassword && !passwordLengthValid ? "border-red-500" : ""
                    }`}
                    required
                  />
                  {newPassword && (
                    <p
                      className={`text-xs flex items-center mt-1 ${passwordLengthValid ? "text-green-400" : "text-red-400"}`}
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

                <div className="space-y-1">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`bg-black/30 border-white/20 ${
                      confirmPassword && !passwordsMatch ? "border-red-500" : ""
                    }`}
                    required
                  />
                  {confirmPassword && (
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

                <Button
                  type="submit"
                  className="w-full bg-white text-black hover:bg-gray-200"
                  disabled={isSubmitting || !passwordLengthValid || !passwordsMatch || !currentPasswordValid}
                >
                  {isSubmitting ? "Changing..." : "Change Password"}
                </Button>
              </form>
            )}
          </div>

          {/* Search Results Count Preference */}
          <div>
            <h3 className="text-sm font-medium mb-2">Search Results Count</h3>
            <p className="text-sm text-white/70 mb-4">
              Set the maximum number of results to display: <span className="font-bold">{localResultsCount}</span>
            </p>

            <div className="py-2">
              <Slider
                defaultValue={[localResultsCount]}
                max={50}
                min={5}
                step={1}
                onValueChange={handleResultsCountChange}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-white/50 mt-1">
                <span>5</span>
                <span>50</span>
              </div>
            </div>

            <Button onClick={saveResultsCount} className="w-full bg-white text-black hover:bg-gray-200 mt-2">
              Save Preferences
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default SettingsPopup
