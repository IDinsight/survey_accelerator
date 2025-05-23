"use client";

import { useMemo, useState, useEffect } from "react";
import { ThumbsUp, ThumbsDown, Send } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { toast } from "sonner";
import { submitFeedback } from "../api";

interface PDFViewerProps {
  // A fully constructed PDF URL returned by the backend
  pdfUrl: string;
  // Optionally, the page number to display
  pageNumber?: number;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pageNumber }) => {
  const exampleQueries = [
    "child mortality rates",
    "vaccination coverage",
    "maternal health indicators",
    "school enrollment statistics",
    "agricultural productivity",
    "clean water access",
    "gender equality metrics",
    "community health programs",
  ];

  const [currentQueryIndex, setCurrentQueryIndex] = useState(0);
  const [nextQueryIndex, setNextQueryIndex] = useState(1);
  const [animationState, setAnimationState] = useState("idle"); // "idle" | "animating"
  const [feedbackType, setFeedbackType] = useState<"like" | "dislike" | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Rotate through example queries with sliding animation
  useEffect(() => {
    const queryDisplayTime = 2500; // Change frequency: every 2.5 seconds
    const animationDuration = 1800; // Keep the same slow, smooth animation duration

    const rotationInterval = setInterval(() => {
      // Start the animation
      setAnimationState("animating");

      // After animation completes, update indices and reset animation state
      setTimeout(() => {
        setCurrentQueryIndex(nextQueryIndex);
        setNextQueryIndex((nextQueryIndex + 1) % exampleQueries.length);
        setAnimationState("idle");
      }, animationDuration);

    }, queryDisplayTime);

    return () => clearInterval(rotationInterval);
  }, [nextQueryIndex, exampleQueries.length]);

  const processedUrl = useMemo(() => {
    if (!pdfUrl) return "";
    // If a pageNumber is provided, append the page anchor to the provided URL.
    return pageNumber ? `${pdfUrl}#page=${pageNumber}` : pdfUrl;
  }, [pdfUrl, pageNumber]);

  const handleFeedback = async (type: "like" | "dislike") => {
    setFeedbackType(type);
    setShowFeedbackForm(true);
  };

  const handleSubmitFeedback = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await submitFeedback({
        feedbackType,
        comment: feedbackText,
        pdfUrl
      });
      toast.success("Thank you for your feedback!");
      setShowFeedbackForm(false);
      setFeedbackText("");
      setFeedbackType(null);
    } catch (error) {
      toast.error("Failed to submit feedback. Please try again.");
      console.error("Feedback submission error:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative w-full h-full rounded-lg overflow-hidden">
      {pdfUrl ? (
        <div className="w-full h-full bg-black/30 backdrop-blur-sm rounded-lg">
          <object
            key={`pdf-${pdfUrl}-${pageNumber || "default"}`}
            data={processedUrl}
            type="application/pdf"
            className="w-full h-full"
            style={{ border: "none", display: "block" }}
          >
            <div className="w-full h-full flex items-center justify-center bg-gray-100 p-4">
              <p>Unable to display PDF.</p>
            </div>
          </object>

          {/* Feedback Component */}
          <div className="absolute bottom-4 left-0 right-0 flex flex-col items-center">
            {!showFeedbackForm ? (
              <div className="flex items-center gap-2 p-2 bg-black/50 backdrop-blur-sm rounded-lg">
                <span className="text-white text-sm mr-1">Feedback</span>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-white hover:bg-white/20 rounded-full p-1"
                  onClick={() => handleFeedback("like")}
                  title="This result was helpful"
                >
                  <ThumbsUp className="h-4 w-4" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-white hover:bg-white/20 rounded-full p-1"
                  onClick={() => handleFeedback("dislike")}
                  title="This result was not helpful"
                >
                  <ThumbsDown className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="flex flex-col bg-black/70 backdrop-blur-sm rounded-lg p-3 max-w-sm w-full">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white text-sm">
                    {feedbackType === "like" ? "What was helpful?" : "What could be improved?"}
                  </span>
                  <div className="flex items-center">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className={`text-white p-1 rounded-full ${feedbackType === "like" ? "bg-green-700/30" : ""}`}
                      disabled
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className={`text-white p-1 rounded-full ${feedbackType === "dislike" ? "bg-red-700/30" : ""}`}
                      disabled
                    >
                      <ThumbsDown className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
                <Textarea 
                  placeholder="Optional comments..."
                  className="bg-black/30 border-white/30 text-white placeholder:text-white/50 text-sm resize-none min-h-[60px]"
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                />
                <div className="flex justify-between mt-2">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className="text-white/70 hover:text-white hover:bg-transparent p-0 h-auto text-xs"
                    onClick={() => {
                      setShowFeedbackForm(false);
                      setFeedbackText("");
                    }}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button 
                    size="sm"
                    className="bg-white text-black hover:bg-white/90 flex items-center gap-1 px-2 py-1 h-7 text-xs"
                    onClick={handleSubmitFeedback}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "Submitting..." : (
                      <>
                        Submit <Send className="h-3 w-3 ml-1" />
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-white text-center text-3xl font-inter mb-4">
            Try searching for
          </p>
          {/* Outer wrapper with mask to clip content outside boundaries */}
          <div
            className="relative h-16 w-full"
            style={{
              maskImage: 'linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%)',
              WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%)'
            }}
          >
            {/* Inner animation container */}
            <div className="relative h-full w-full overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center">
                {/* Current query - visible and slides down and out when animating */}
                <div
                  key={`current-${currentQueryIndex}`}
                  className={`absolute text-white text-center transition-transform duration-[1800ms] ease-in-out ${
                    animationState === "animating" ? 'transform translate-y-[130%]' : 'transform translate-y-0'
                  }`}
                >
                  <p className="text-4xl font-bold font-inter">{exampleQueries[currentQueryIndex]}</p>
                </div>

                {/* Next query that slides in from above */}
                <div
                  key={`next-${nextQueryIndex}`}
                  className={`absolute text-white text-center transition-transform duration-[1800ms] ease-in-out ${
                    animationState === "animating" ? 'transform translate-y-0' : 'transform -translate-y-[130%]'
                  }`}
                >
                  <p className="text-4xl font-bold font-inter">{exampleQueries[nextQueryIndex]}</p>
                </div>
              </div>
            </div>
          </div>
          <p className="text-white text-center text-3xl font-inter mt-4">
            then select a card to view results
          </p>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;
