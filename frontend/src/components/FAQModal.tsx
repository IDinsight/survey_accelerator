"use client"

import type React from "react"
import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion"
import { Loader2 } from "lucide-react"
import { Badge } from "./ui/badge"
import { fetchDocumentsByOrganization } from "../api"

// Define types inline for now
interface DocumentPreview {
  title: string | null
  file_name: string
  preview_link: string | null
  year: number | null
  description: string | null
  countries: string[] | null
  regions: string[] | null
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

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto bg-black/80 backdrop-blur-md text-white border border-white/20">
        <DialogHeader>
          <DialogTitle className="text-white">Resources & Help</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="faq" className="mt-4">
          <TabsList className="grid w-full grid-cols-2 bg-black/50">
            <TabsTrigger value="faq" className="text-white data-[state=active]:bg-white/10">
              FAQ
            </TabsTrigger>
            <TabsTrigger value="documents" className="text-white data-[state=active]:bg-white/10">
              Document Library
            </TabsTrigger>
          </TabsList>

          <TabsContent value="faq" className="mt-4">
            <div className="space-y-4">
              <div className="bg-black/50 p-4 rounded-md border border-white/10">
                <h3 className="text-lg font-medium text-white">How do I search for documents?</h3>
                <p className="text-white/80">
                  Enter your search query in the search box and press Enter or click the search button. You can filter
                  results by country, organization, or region using the dropdown menus.
                </p>
              </div>

              <div className="bg-black/50 p-4 rounded-md border border-white/10">
                <h3 className="text-lg font-medium text-white">How are search results ranked?</h3>
                <p className="text-white/80">
                  Search results are ranked based on relevance to your query. Documents with more "Strong" matches will
                  appear higher in the results.
                </p>
              </div>

              <div className="bg-black/50 p-4 rounded-md border border-white/10">
                <h3 className="text-lg font-medium text-white">Can I download documents?</h3>
                <p className="text-white/80">
                  Yes, you can download documents by clicking on the "View Document" link in the search results or in
                  the Document Library. This will open the document in a new tab where you can download it.
                </p>
              </div>

              <div className="bg-black/50 p-4 rounded-md border border-white/10">
                <h3 className="text-lg font-medium text-white">How do I view specific matches in a document?</h3>
                <p className="text-white/80">
                  Click on a search result card to view the document. Then, click on any match in the expanded card to
                  navigate directly to that page in the document.
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="documents" className="mt-4">
            {/* Document Library content */}
            <div className="documents-library">
              <h2 className="text-xl font-semibold mb-4 text-white">Document Library</h2>

              {loading ? (
                <div className="flex justify-center items-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-white" />
                </div>
              ) : error ? (
                <div className="text-center py-4 text-red-400">
                  <p>{error}</p>
                  <p className="text-sm mt-2 text-white/70">Please try again later or contact support.</p>
                </div>
              ) : organizationDocs.length === 0 ? (
                <p className="text-center py-4 text-white">No documents available.</p>
              ) : (
                <Accordion type="single" collapsible className="w-full">
                  {organizationDocs.map((orgDoc, index) => (
                    <AccordionItem key={index} value={`org-${index}`} className="border-b border-white/20">
                      <AccordionTrigger className="text-left font-medium hover:no-underline text-white px-4 py-2">
                        {orgDoc.organization}{" "}
                        <Badge className="ml-2 bg-white/20 text-white">{orgDoc.documents.length}</Badge>
                      </AccordionTrigger>
                      <AccordionContent className="px-4 pt-2 pb-4">
                        <div className="space-y-3 pl-2">
                          {orgDoc.documents.map((doc, docIndex) => (
                            <div key={docIndex} className="p-3 bg-black/40 rounded-md border border-white/10">
                              <div className="font-medium text-white">{doc.title || doc.file_name}</div>

                              {doc.year && <div className="text-sm text-white/70 mt-1">Year: {doc.year}</div>}

                              {doc.description && <div className="text-sm mt-2 text-white/90">{doc.description}</div>}

                              <div className="flex flex-wrap gap-2 mt-3">
                                {doc.countries && doc.countries.length > 0 && (
                                  <div className="flex flex-wrap gap-1">
                                    {doc.countries.map((country, idx) => (
                                      <Badge key={idx} variant="outline" className="text-xs text-white border-white/30">
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
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

export default FAQModal
