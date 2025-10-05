"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

interface ThemeContextType {
  livMode: boolean
  setLivMode: (mode: boolean) => void
  primaryColor: string
  primaryColor300: string
  primaryColor600: string
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [livMode, setLivMode] = useState(false)

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('livMode')
    if (savedTheme !== null) {
      setLivMode(JSON.parse(savedTheme))
    }
  }, [])

  // Save theme to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('livMode', JSON.stringify(livMode))
  }, [livMode])

  const primaryColor = livMode ? "pink-400" : "blue-400"
  const primaryColor300 = livMode ? "pink-300" : "blue-300"
  const primaryColor600 = livMode ? "pink-600" : "blue-600"

  return (
    <ThemeContext.Provider value={{
      livMode,
      setLivMode,
      primaryColor,
      primaryColor300,
      primaryColor600
    }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
