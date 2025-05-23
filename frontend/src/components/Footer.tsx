"use client"

import { FC } from "react"

interface FooterProps {
  showFooter?: boolean
  isPdfShowing?: boolean
}

const Footer: FC<FooterProps> = ({ showFooter = true, isPdfShowing = false }) => {
  if (!showFooter) return null

  return (
    <div className="absolute bottom-4 left-0 right-0 z-20 text-center">
      <div className="flex flex-col gap-1">
        {!isPdfShowing && (
          <>
            <p className="text-white text-base md:text-lg">
              Contact{" "}
              <a
                href="mailto:surveyaccelerator@idinsight.org"
                className="text-yellow-500 hover:text-yellow-400 transition-colors font-medium"
              >
                surveyaccelerator@idinsight.org
              </a>{" "}
              for support
            </p>
            <p className="text-white text-base md:text-lg">
              Made by the Tech Team at{" "}
              <a
                href="https://www.idinsight.org/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-yellow-500 hover:text-yellow-400 transition-colors font-medium"
              >
                IDinsight
              </a>
              {" | "}
              <a
                href="https://dsem.idinsight.io/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-yellow-500 hover:text-yellow-400 transition-colors font-medium"
              >
                DSEM @ IDinsight
              </a>
            </p>
          </>
        )}
      </div>
    </div>
  )
}

export default Footer
