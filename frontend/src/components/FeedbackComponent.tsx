import React, { useState } from "react";
import { ThumbsUp, ThumbsDown, Send } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { toast } from "sonner";
import { submitFeedback } from "../api";

interface FeedbackComponentProps {
  searchTerm: string;
  onFeedbackSubmitted: () => void;
}

const FeedbackComponent: React.FC<FeedbackComponentProps> = ({ searchTerm, onFeedbackSubmitted }) => {
  const [feedbackType, setFeedbackType] = useState<"like" | "dislike" | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (type: "like" | "dislike") => {
    setFeedbackType(type);
    setShowFeedbackForm(true);

    // Submit the initial feedback (like/dislike) immediately
    try {
      await submitFeedback({
        feedbackType: type,
        search_term: searchTerm
      });

      // Show a toast notification when like/dislike is submitted
      toast.success(
        type === "like"
          ? "Thanks for the positive feedback!"
          : "Thanks for your feedback!"
      );

      // If the user doesn't proceed to add text feedback within 3 seconds,
      // consider feedback completed
      const timer = setTimeout(() => {
        if (showFeedbackForm) {
          onFeedbackSubmitted();
        }
      }, 3000);

      // Clean up timer if component unmounts or user starts entering text
      return () => clearTimeout(timer);
    } catch (error) {
      console.error("Error submitting initial feedback:", error);
      toast.error("Failed to submit feedback. Please try again.");
    }
  };

  const handleSubmitFeedbackText = async () => {
    if (isSubmitting || !feedbackType) return;

    setIsSubmitting(true);
    try {
      await submitFeedback({
        feedbackType,
        comment: feedbackText,
        search_term: searchTerm
      });
      toast.success("Thank you for your detailed feedback!");
      setShowFeedbackForm(false);
      setFeedbackText("");
      setFeedbackType(null);
      onFeedbackSubmitted();
    } catch (error) {
      toast.error("Failed to submit feedback. Please try again.");
      console.error("Feedback submission error:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!searchTerm) return null;

  return (
    <div className="mb-4 mt-3">
      {!showFeedbackForm ? (
        <div className="flex items-center justify-between p-3 bg-black/30 backdrop-blur-sm rounded-lg">
          <span className="text-white text-sm">Was this search helpful?</span>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/20 rounded-full p-1"
              onClick={() => handleFeedback("like")}
              title="Yes, this was helpful"
            >
              <ThumbsUp className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/20 rounded-full p-1"
              onClick={() => handleFeedback("dislike")}
              title="No, this was not helpful"
            >
              <ThumbsDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col bg-black/30 backdrop-blur-sm rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white text-sm">
              {feedbackType === "like" ? "What was helpful?" : "What could be improved?"}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className={`text-white p-1 rounded-full ${feedbackType === "like" ? "bg-green-700/30" : "bg-red-700/30"}`}
              disabled
            >
              {feedbackType === "like" ? <ThumbsUp className="h-3 w-3" /> : <ThumbsDown className="h-3 w-3" />}
            </Button>
          </div>
          <Textarea
            placeholder="Tell us more (optional)..."
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
                // If user cancels text feedback, consider the initial like/dislike as complete
                onFeedbackSubmitted();
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
              onClick={handleSubmitFeedbackText}
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
  );
};

export default FeedbackComponent;
