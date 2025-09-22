"use client"

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react"
import { api } from "@/lib/api"

export interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
  daily_api_calls: number
  daily_api_limit: number
  total_documents: number
  total_storage_bytes: number
  storage_limit_bytes: number
}

export interface Session {
  session_id: string
  user: User
  expires_at: string
  created_at: string
}

export interface UsageStats {
  user_id: number
  username: string
  api_usage: {
    daily_calls: number
    daily_limit: number
    percentage: number
    remaining: number
  }
  storage_usage: {
    used_bytes: number
    limit_bytes: number
    percentage: number
    remaining_bytes: number
    used_mb: number
    limit_mb: number
  }
  document_count: number
}

interface AuthContextType {
  user: User | null
  session: Session | null
  usageStats: UsageStats | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUsageStats: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!session

  // Load session from localStorage on mount
  useEffect(() => {
    const loadSession = async () => {
      try {
        const savedSession = localStorage.getItem("lectureai_session")
        if (savedSession) {
          const sessionData = JSON.parse(savedSession)
          
          // Check if session is still valid (not expired)
          if (new Date(sessionData.expires_at) > new Date()) {
            setSession(sessionData)
            setUser(sessionData.user)
            
            // Verify session with server
            try {
              const userData = await api.getCurrentUser(sessionData.session_id)
              setUser(userData)
              
              // Refresh usage stats
              const stats = await api.getUserUsageStats(sessionData.session_id)
              setUsageStats(stats)
            } catch (error) {
              // Session is invalid, clear it
              localStorage.removeItem("lectureai_session")
              setSession(null)
              setUser(null)
              setUsageStats(null)
            }
          } else {
            // Session expired, clear it
            localStorage.removeItem("lectureai_session")
          }
        }
      } catch (error) {
        console.error("Error loading session:", error)
        localStorage.removeItem("lectureai_session")
      } finally {
        setIsLoading(false)
      }
    }

    loadSession()
  }, [])

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true)
      const sessionData = await api.login(username, password)
      
      setSession(sessionData)
      setUser(sessionData.user)
      
      // Save session to localStorage
      localStorage.setItem("lectureai_session", JSON.stringify(sessionData))
      
      // Get usage stats
      const stats = await api.getUserUsageStats(sessionData.session_id)
      setUsageStats(stats)
      
    } catch (error) {
      console.error("Login error:", error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (username: string, email: string, password: string) => {
    try {
      setIsLoading(true)
      const sessionData = await api.register(username, email, password)
      
      setSession(sessionData)
      setUser(sessionData.user)
      
      // Save session to localStorage
      localStorage.setItem("lectureai_session", JSON.stringify(sessionData))
      
      // Get usage stats
      const stats = await api.getUserUsageStats(sessionData.session_id)
      setUsageStats(stats)
      
    } catch (error) {
      console.error("Registration error:", error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      if (session?.session_id) {
        await api.logout(session.session_id)
      }
    } catch (error) {
      console.error("Logout error:", error)
    } finally {
      // Clear session regardless of API call success
      localStorage.removeItem("lectureai_session")
      setSession(null)
      setUser(null)
      setUsageStats(null)
    }
  }

  const refreshUsageStats = async () => {
    if (session?.session_id) {
      try {
        const stats = await api.getUserUsageStats(session.session_id)
        setUsageStats(stats)
      } catch (error) {
        console.error("Error refreshing usage stats:", error)
      }
    }
  }

  const value: AuthContextType = {
    user,
    session,
    usageStats,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUsageStats
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
