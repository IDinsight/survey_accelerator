"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion"
import { Loader2, Search } from "lucide-react"
import { Badge } from "./ui/badge"
import { Input } from "./ui/input"
import { fetchDocumentsByOrganization } from "../api"
import "../styles/scrollbar.css" // Import the custom scrollbar styles

// Define types inline for now
interface DocumentPreview {
  title: string | null
  file_name: string
  preview_link: string | null
  year: number | null
  description: string | null
  countries: string[] | null
  regions: string[] | null
  survey_type: string | null
}

interface OrganizationDocuments {
  organization: string
  documents: DocumentPreview[]
}

interface FAQModalProps {
  onClose: () => void
  isOpen?: boolean
}

const FAQModal: React.FC<FAQModalProps> = ({ onClose, isOpen = false }) => {
  // State for document library
  const [organizationDocs, setOrganizationDocs] = useState<OrganizationDocuments[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState("faq")
  const [groupBy, setGroupBy] = useState<"organization" | "survey_type">("organization")

  // Fetch documents when the modal is opened
  useEffect(() => {
    if (isOpen) {
      async function loadDocuments() {
        setLoading(true)
        try {
          const data = await fetchDocumentsByOrganization()
          setOrganizationDocs(data)
          setError(null)
        } catch (err) {
          setError("Failed to load documents")
          console.error(err)
        } finally {
          setLoading(false)
        }
      }

      loadDocuments()
    }
  }, [isOpen])

  // Filter documents based on search term
  const filteredOrganizationDocs = organizationDocs
    .map((orgDoc) => {
      // Filter documents by title or filename
      const filteredDocs = orgDoc.documents.filter((doc) => {
        const title = doc.title || doc.file_name || ""
        return title.toLowerCase().includes(searchTerm.toLowerCase())
      })

      // Return a new object with filtered documents
      return {
        ...orgDoc,
        documents: filteredDocs,
      }
    })
    .filter((orgDoc) => orgDoc.documents.length > 0) // Only include orgs with matching documents

  // Function to transform documents based on groupBy selection
  const getGroupedDocuments = () => {
    if (groupBy === "organization") {
      return filteredOrganizationDocs
    } else {
      // Group by survey type
      const surveyTypeMap: Record<string, { organization: string; documents: DocumentPreview[] }> = {}

      filteredOrganizationDocs.forEach((orgDoc) => {
        orgDoc.documents.forEach((doc) => {
          // Handle case where document doesn't have survey type info
          const surveyType = doc.survey_type || "Uncategorized"

          if (!surveyTypeMap[surveyType]) {
            surveyTypeMap[surveyType] = {
              organization: surveyType,
              documents: [],
            }
          }

          surveyTypeMap[surveyType].documents.push(doc)
        })
      })

      return Object.values(surveyTypeMap)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="sm:max-w-[800px] max-h-[80vh] bg-black/80 backdrop-blur-md text-white border border-white/20 flex flex-col"
        style={{ width: "800px" }}
      >
        <DialogHeader className="pb-2">
          <DialogTitle className="text-white">Resources & Help</DialogTitle>
        </DialogHeader>

        <Tabs
          defaultValue="faq"
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <TabsList className="grid w-full grid-cols-2 bg-black/50 mb-4">
            <TabsTrigger
              value="faq"
              className="text-white data-[state=active]:bg-[#CC7722] data-[state=active]:text-white data-[state=inactive]:bg-white/10"
            >
              FAQ
            </TabsTrigger>
            <TabsTrigger
              value="documents"
              className="text-white data-[state=active]:bg-[#CC7722] data-[state=active]:text-white data-[state=inactive]:bg-white/10"
            >
              Document Library
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-hidden">
            {activeTab === "faq" && (
              <div className="h-[calc(80vh-140px)] overflow-y-auto custom-scrollbar pr-2">
                <Accordion type="single" collapsible className="w-full pb-8">
                  <AccordionItem value="what-is" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      What is Survey Accelerator?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      Survey Accelerator is a specialized search engine designed to help researchers, policymakers, and
                      development practitioners quickly find relevant information across a wide range of high-quality
                      surveys and research documents. It uses advanced search algorithms to identify the most relevant
                      matches to your queries within documents from organizations like IDHS, IDinsight, UNICEF, and
                      more.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="cost" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      Does it cost anything to use?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      No, Survey Accelerator is completely free to use. It was developed as a public good to help
                      researchers, policymakers, and development practitioners access and utilize survey data more
                      effectively. There are no subscription fees, usage limits, or premium tiers. All features are
                      available to all registered users at no cost.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="how-to-use" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      How do I use it?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      <p>To use Survey Accelerator:</p>
                      <ol className="list-decimal pl-5 space-y-2 mt-2">
                        <li>Enter your search query in the search box</li>
                        <li>Optionally filter by organization or survey type using the dropdown menus</li>
                        <li>Click the Search button or press Enter</li>
                        <li>Browse the results and click on any document card to view it</li>
                        <li>Click on specific matches within a document to navigate directly to that page</li>
                      </ol>
                      <p className="mt-2">
                        Results are ranked by relevance, with "Strong" matches appearing at the top.
                      </p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="available-docs" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      What documents are available?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      Survey Accelerator includes documents from various organizations including IDHS, IDinsight,
                      National Statistics Bureau, UNICEF, USAID, and World Bank. Document types include DHS Surveys,
                      MICS7 questionnaires, household income surveys, labor force surveys, and more. You can browse the
                      full collection in the Document Library tab.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="add-to-database" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      Can I add to the database of surveys?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      Yes! You can contribute surveys to the database by clicking the "Contribute Survey" button in the
                      top navigation bar. You'll be asked to provide the survey title, optional details like survey
                      type and origin organization, and a justification for why the survey should be included. If you
                      have a PDF version of the survey, you can optionally upload it. All submissions are reviewed by
                      the Survey Accelerator team before being added to the database. Please ensure you have the right
                      to share any survey you contribute.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="results-count" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      Can I increase/decrease the number of docs returned?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      Yes! You can adjust the number of search results displayed by clicking the Settings icon in the
                      top right corner. In the Settings popup, you'll find a slider to set your preferred number of
                      results (from 5 to 50). This preference will be saved for future searches.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="see-code" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      Can I see the code behind Survey Accelerator?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      Yes! Survey Accelerator is an open-source project. The source code is available on GitHub at
                      <a
                        href="https://github.com/IDinsight/survey-accelerator"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-300 hover:underline ml-1"
                      >
                        github.com/IDinsight/survey-accelerator
                      </a>
                      . We welcome contributions, bug reports, and feature requests from the community. If you're
                      interested in contributing to the project, please check the repository's README for guidelines on
                      how to get started.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="who-built" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      Who built Survey Accelerator?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      Survey Accelerator was built by IDinsight, a global advisory, data analytics, and research
                      organization that helps development leaders maximize their social impact. The project was
                      developed with support from various partners and is maintained by IDinsight's data science team.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="match-types" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      What's the difference between direct and contextual matches?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      <p><strong>Direct matches:</strong> Strong matches with the source text; the page highlighted contains text which directly relates to what you are looking for.</p>
                      <p className="mt-2"><strong>Contextual matches:</strong> Pages that lie within a section that matches the broader context of what you are searching for, but may not itself contain text relating to your query.</p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="change-password" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      How do I change my password?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      To change your password:
                      <ol className="list-decimal pl-5 space-y-2 mt-2">
                        <li>Click the Settings icon in the top right corner</li>
                        <li>In the Settings popup, click on "Change Password"</li>
                        <li>Enter your current password and your new password twice</li>
                        <li>Click the "Change Password" button to save your changes</li>
                      </ol>
                      <p className="mt-2">
                        If you've forgotten your password, use the "Forgot Password" option on the login screen.
                      </p>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="delete-account" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      How do I delete my account and data?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      To request account deletion, please email surveyaccelerator@idinsight.org with the subject
                      "Account Deletion Request" and include your registered email address. The team will process your
                      request and confirm when your account and associated data have been removed from the system.
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="support" className="border-b border-white/20">
                    <AccordionTrigger className="text-white hover:no-underline py-4 px-4">
                      Who do I reach out to if something is broken?
                    </AccordionTrigger>
                    <AccordionContent className="text-white/80 px-4 pb-4">
                      If you encounter any issues, bugs, or have suggestions for improvements, please contact the Survey
                      Accelerator support team at surveyaccelerator@idinsight.org. Please include details about the
                      problem you're experiencing, steps to reproduce it, and screenshots if possible.
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {activeTab === "documents" && (
              <div className="flex flex-col h-[calc(80vh-140px)]">
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-xl font-semibold text-white">Document Library</h2>

                    <div className="relative ml-auto w-1/3">
                      <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-white/70" />
                      <Input
                        placeholder="Search documents by title..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-8 bg-black/30 border-white/30 text-white placeholder:text-white/50 focus:ring-0 focus:ring-offset-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:outline-none"
                      />
                    </div>
                  </div>

                  {/* Group by toggle switch - moved down and left-aligned */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-white mr-1">Group by:</span>
                    <span className={`text-sm ${groupBy === "organization" ? "text-white" : "text-white/60"}`}>
                      Organization
                    </span>
                    <div
                      className="relative w-12 h-6 bg-black/50 rounded-full cursor-pointer border border-white/30"
                      onClick={() =>
                        setGroupBy(groupBy === "organization" ? "survey_type" : "organization")
                      }
                    >
                      <div
                        className={`absolute top-[1px] w-5 h-5 rounded-full transition-transform duration-200 ease-in-out ${
                          groupBy === "organization" ? "left-0.5 bg-white" : "left-6 bg-[#CC7722]"
                        }`}
                      />
                    </div>
                    <span className={`text-sm ${groupBy === "survey_type" ? "text-white" : "text-white/60"}`}>
                      Survey Type
                    </span>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                  {loading ? (
                    <div className="flex justify-center items-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-white" />
                    </div>
                  ) : error ? (
                    <div className="text-center py-4 text-red-400">
                      <p>{error}</p>
                      <p className="text-sm mt-2 text-white/70">Please try again later or contact support.</p>
                    </div>
                  ) : filteredOrganizationDocs.length === 0 ? (
                    <div className="text-center py-4 text-white min-h-[400px] flex items-center justify-center">
                      <p>{searchTerm ? "No documents match your search." : "No documents available."}</p>
                    </div>
                  ) : (
                    <Accordion type="multiple" className="w-full pb-8">
                      {getGroupedDocuments().map((orgDoc, index) => (
                        <AccordionItem key={index} value={`org-${index}`} className="border-b border-white/20">
                          <AccordionTrigger className="text-left font-medium hover:no-underline text-white px-4 py-2 flex justify-between">
                            <span>{orgDoc.organization}</span>
                            <Badge className="ml-auto mr-2 bg-white/20 text-white min-w-[2.5rem] justify-center">
                              {orgDoc.documents.length}
                            </Badge>
                          </AccordionTrigger>
                          <AccordionContent className="px-4 pt-2 pb-4">
                            <div className="space-y-3 pl-2">
                              {orgDoc.documents.map((doc, docIndex) => (
                                <div key={docIndex} className="p-3 bg-black/40 rounded-md border border-white/10">
                                  <div className="font-medium text-white">{doc.title || doc.file_name}</div>

                                  {doc.year && <div className="text-sm text-white/70 mt-1">Year: {doc.year}</div>}

                                  {doc.description && (
                                    <div className="text-sm mt-2 text-white/90">{doc.description}</div>
                                  )}

                                  <div className="flex flex-wrap gap-2 mt-3">
                                    {doc.countries && doc.countries.length > 0 && (
                                      <div className="flex flex-wrap gap-1">
                                        {doc.countries.map((country, idx) => (
                                          <Badge
                                            key={idx}
                                            variant="outline"
                                            className="text-xs text-white border-white/30"
                                          >
                                            {country}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}

                                    {doc.regions && doc.regions.length > 0 && (
                                      <div className="flex flex-wrap gap-1">
                                        {doc.regions.map((region, idx) => (
                                          <Badge key={idx} className="text-xs bg-white/20 text-white">
                                            {region}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {doc.preview_link && (
                                    <a
                                      href={doc.preview_link}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-block mt-3 text-sm text-blue-300 hover:underline"
                                    >
                                      View Document
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  )}
                </div>
              </div>
            )}
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

export default FAQModal
