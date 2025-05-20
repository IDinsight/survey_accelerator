"use client"

import { FC } from "react"

interface FooterProps {
  showFooter?: boolean
}

const Footer: FC<FooterProps> = ({ showFooter = true }) => {
  if (!showFooter) return null

  return (
    <div className="absolute bottom-4 left-0 right-0 z-20 text-center">
      <p className="text-white/70 text-base md:text-lg">
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
    </div>
  )
}

export default Footer
