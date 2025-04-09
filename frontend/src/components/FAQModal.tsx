"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion"
import { Loader2 } from 'lucide-react'

interface DocumentInfo {
  title: string
  file_name: string
  preview_link: string
  year: number
  description: string
  countries: string[]
  regions: string[]
}

interface OrganizationDocuments {
  organization: string
  documents: DocumentInfo[]
}

interface FAQModalProps {
  onClose: () => void
}

const FAQModal: React.FC<FAQModalProps> = ({ onClose }) => {
  const [documents, setDocuments] = useState<OrganizationDocuments[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true)
      setError(null)
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000"
        const response = await fetch(`${backendUrl}/documents/list`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        })
        
        if (!response.ok) {
          throw new Error("Failed to fetch documents")
        }
        
        const data = await response.json()
        setDocuments(data)
      } catch (err) {
        console.error("Error fetching documents:", err)
        setError("Failed to load documents. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchDocuments()
  }, [])

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <Card className="w-[90%] max-w-4xl max-h-[90vh] overflow-y-auto bg-black/30 backdrop-blur-sm text-white border-0">
        <CardHeader className="pb-2">
          <CardTitle>Frequently Asked Questions</CardTitle>
          <CardDescription className="text-gray-300">Learn more about Survey Accelerator</CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1" className="border-gray-700">
              <AccordionTrigger className="text-white hover:text-white hover:no-underline">
                What is Survey Accelerator?
              </AccordionTrigger>
              <AccordionContent className="text-gray-300">
                <p>
                  Survey Accelerator is a specialized search engine designed to help researchers, policymakers, and 
                  development professionals quickly find relevant information within high-quality survey instruments.
                </p>
                <p className="mt-2">
                  Our platform allows you to search across multiple survey questionnaires from leading organizations 
                  like UNICEF, World Bank, USAID, and national statistics bureaus, making it easier to discover 
                  questions, methodologies, and best practices for your own research.
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-2" className="border-gray-700">
              <AccordionTrigger className="text-white hover:text-white hover:no-underline">
                How do I use it?
              </AccordionTrigger>
              <AccordionContent className="text-gray-300">
                <ol className="list-decimal pl-5 space-y-2">
                  <li>
                    <strong>Enter your search query</strong> in the search box. You can search for specific topics, 
                    questions, or concepts you're interested in.
                  </li>
                  <li>
                    <strong>Filter your results</strong> by selecting organizations, survey types, or regions if needed.
                  </li>
                  <li>
                    <strong>Review the search results</strong> to find documents that match your query. Each result 
                    shows the document title, organization, and a brief description.
                  </li>
                  <li>
                    <strong>Click on a result card</strong> to view the PDF with highlighted matches to your search query.
                  </li>
                  <li>
                    <strong>Explore the matches</strong> by clicking on them to navigate directly to the relevant page 
                    in the document.
                  </li>
                </ol>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-3" className="border-gray-700">
              <AccordionTrigger className="text-white hover:text-white hover:no-underline">
                What documents are available?
              </AccordionTrigger>
              <AccordionContent className="text-gray-300">
                {loading ? (
                  <div className="flex justify-center items-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-white" />
                  </div>
                ) : error ? (
                  <div className="text-red-400 py-4">{error}</div>
                ) : (
                  <div className="space-y-6">
                    <p>
                      Survey Accelerator currently includes questionnaires from major development organizations and 
                      national statistics bureaus. Below is a breakdown of available documents by organization:
                    </p>
                    
                    {documents.map((org) => (
                      <div key={org.organization} className="mt-4">
                        <h4 className="text-lg font-medium text-white mb-2">{org.organization}</h4>
                        <p className="mb-2 text-sm">{org.documents.length} documents available</p>
                        
                        <Accordion type="single" collapsible className="w-full">
                          <AccordionItem value={`org-${org.organization}`} className="border-gray-700">
                            <AccordionTrigger className="text-sm text-white hover:text-white hover:no-underline">
                              View document list
                            </AccordionTrigger>
                            <AccordionContent>
                              <div className="max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                                <ul className="space-y-3">
                                  {org.documents.map((doc) => (
                                    <li key={doc.file_name} className="text-sm">
                                      <a 
                                        href={doc.preview_link} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-blue-300 hover:text-blue-200 hover:underline"
                                      >
                                        {doc.title}
                                      </a>
                                      <div className="text-xs text-gray-400 mt-1">
                                        {doc.year} • {Array.isArray(doc.regions) ? doc.regions.join(", ") : doc.regions}
                                      </div>
                                      <p className="text-xs mt-1">{doc.description}</p>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </div>
                    ))}
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-4" className="border-gray-700">
              <AccordionTrigger className="text-white hover:text-white hover:no-underline">
                Can I suggest new documents?
              </AccordionTrigger>
              <AccordionContent className="text-gray-300">
                <p>
                  Yes! We're always looking to expand our collection of survey instruments. If you have suggestions 
                  for additional documents that should be included in Survey Accelerator, please email us at:
                </p>
                <p className="mt-2 font-medium">surveyaccelerator@idinsight.org</p>
                <p className="mt-2">
                  Please include the name of the survey, the organization that produced it, and any links or 
                  attachments to the questionnaire if available.
                </p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <div className="flex justify-end pt-4">
            <Button variant="outline" onClick={onClose} className="border-gray-600 text-white hover:bg-white/10">
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default FAQModal
