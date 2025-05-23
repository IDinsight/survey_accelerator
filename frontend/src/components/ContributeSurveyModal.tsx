"use client"

import React, { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./ui/dialog"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Textarea } from "./ui/textarea"
import { Upload, Loader2, Check } from "lucide-react"
import { toast } from "sonner"
import { contributeSurvey } from "../api"
import { Checkbox } from "./ui/checkbox"

interface ContributeSurveyModalProps {
  isOpen: boolean
  onClose: () => void
}

const ContributeSurveyModal: React.FC<ContributeSurveyModalProps> = ({ isOpen, onClose }) => {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [formData, setFormData] = useState({
    surveyTitle: "",
    surveyType: "",
    originOrganization: "",
    justification: "",
    consentToShare: false
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleCheckboxChange = (checked: boolean) => {
    setFormData((prev) => ({ ...prev, consentToShare: checked }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const resetForm = () => {
    setFormData({
      surveyTitle: "",
      surveyType: "",
      originOrganization: "",
      justification: "",
      consentToShare: false
    })
    setSelectedFile(null)
    setIsSuccess(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.surveyTitle.trim()) {
      toast.error("Please provide a survey title")
      return
    }

    if (!formData.justification) {
      toast.error("Please provide a justification for why this survey should be included")
      return
    }

    if (!formData.consentToShare) {
      toast.error("You must confirm that you have the right to share this survey")
      return
    }

    setIsSubmitting(true)

    try {
      // Create form data for submission
      const submitData = new FormData()
      if (selectedFile) {
        submitData.append("file", selectedFile)
      }
      submitData.append("survey_title", formData.surveyTitle)
      submitData.append("justification", formData.justification)
      submitData.append("survey_type", formData.surveyType)
      submitData.append("origin_organization", formData.originOrganization)

      // Submit the contribution - user info will be handled on the backend
      await contributeSurvey(submitData)

      setIsSuccess(true)
      toast.success("Survey contribution submitted successfully", {
        description: "The IDinsight team will review your submission and get back to you soon.",
      })
    } catch (error: any) {
      console.error("Error submitting survey contribution:", error)
      toast.error(error.message || "Failed to submit survey contribution", {
        description: "Please try again or contact support.",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (isSuccess) {
      resetForm()
    }
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[550px] max-h-[80vh] bg-black/80 backdrop-blur-md text-white border border-white/20 overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Contribute a Survey
          </DialogTitle>
        </DialogHeader>

        {isSuccess ? (
          <div className="py-8 text-center">
            <div className="mb-4 mx-auto flex items-center justify-center">
              <div className="rounded-full bg-green-600/20 p-3">
                <Check className="h-8 w-8 text-green-500" />
              </div>
            </div>
            <h3 className="text-xl font-medium mb-2">Thank You!</h3>
            <p className="text-white/80 mb-6">
              Your survey contribution has been submitted for review. The IDinsight economics team will
              review your submission and may contact you for additional information.
            </p>
            <Button onClick={handleClose} className="bg-white text-black hover:bg-white/90">
              Close
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="surveyTitle">Survey Title <span className="text-red-500">*</span></Label>
              <Input
                id="surveyTitle"
                name="surveyTitle"
                value={formData.surveyTitle}
                onChange={handleInputChange}
                placeholder="Enter the title of the survey"
                required
                className="bg-black/30 border-white/20 text-white placeholder:text-white/50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="surveyType">Survey Type <span className="text-white/50">(optional)</span></Label>
              <Input
                id="surveyType"
                name="surveyType"
                value={formData.surveyType}
                onChange={handleInputChange}
                placeholder="e.g., Household, Business, Health"
                className="bg-black/30 border-white/20 text-white placeholder:text-white/50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="originOrganization">Origin Organization <span className="text-white/50">(optional)</span></Label>
              <Input
                id="originOrganization"
                name="originOrganization"
                value={formData.originOrganization}
                onChange={handleInputChange}
                placeholder="e.g., World Bank, UNICEF, Government of Kenya"
                className="bg-black/30 border-white/20 text-white placeholder:text-white/50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">Upload Survey PDF <span className="text-white/50">(optional)</span></Label>
              <div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => document.getElementById('file')?.click()}
                  className="border-white/30 text-white hover:bg-white/10 mb-2"
                >
                  {selectedFile ? 'Change File' : 'Choose File'}
                </Button>
                <Input
                  id="file"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
              {selectedFile && (
                <p className="text-xs text-white/70">Selected: {selectedFile.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="justification">
                Why should this survey be included in the Survey Accelerator? <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="justification"
                name="justification"
                value={formData.justification}
                onChange={handleInputChange}
                placeholder="Please explain why this survey is valuable and should be included in the Survey Accelerator database"
                required
                className="min-h-[120px] bg-black/30 border-white/20 text-white placeholder:text-white/50"
              />
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <Checkbox
                id="consentToShare"
                checked={formData.consentToShare}
                onCheckedChange={handleCheckboxChange}
                required
              />
              <Label htmlFor="consentToShare" className="text-sm">
                I confirm that this survey is publicly available and/or I have the right to share it via the Survey Accelerator tool <span className="text-red-500">*</span>
              </Label>
            </div>

            <DialogFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                className="border-white/30 text-white hover:bg-white/10"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-white text-black hover:bg-white/90"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Contribution"
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default ContributeSurveyModal
