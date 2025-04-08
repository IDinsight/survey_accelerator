"use client"

import type React from "react"
import AnimatedBackground from "./AnimatedBackground"

interface IslandLayoutProps {
  children: React.ReactNode
}

const IslandLayout: React.FC<IslandLayoutProps> = ({ children }) => {
  return (
    <div className="relative min-h-screen bg-black">
      {/* Animated background */}
      <AnimatedBackground />

      {/* Content container with z-index to appear above background */}
      <div className="relative z-10 w-full h-full">{children}</div>
    </div>
  )
}

export default IslandLayout
