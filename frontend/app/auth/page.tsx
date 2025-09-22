"use client"

import { useState } from "react"
import { LoginForm } from "@/components/auth/login-form"
import { RegisterForm } from "@/components/auth/register-form"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/components/auth/auth-provider"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [error, setError] = useState<string | undefined>()
  const { login, register, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/")
    }
  }, [isAuthenticated, router])

  const handleLogin = async (username: string, password: string) => {
    try {
      setError(undefined)
      await login(username, password)
      router.push("/")
    } catch (err: any) {
      setError(err.message || "Login failed")
    }
  }

  const handleRegister = async (username: string, email: string, password: string) => {
    try {
      setError(undefined)
      await register(username, email, password)
      router.push("/")
    } catch (err: any) {
      setError(err.message || "Registration failed")
    }
  }

  if (isAuthenticated) {
    return null // Will redirect
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">LectureAI</h1>
          <p className="text-gray-400">
            Intelligent course assistant for organizing and analyzing your materials
          </p>
        </div>

        {/* Auth Forms */}
        <div className="mb-6">
          <div className="flex justify-center space-x-4 mb-6">
            <Button
              variant={isLogin ? "default" : "outline"}
              onClick={() => {
                setIsLogin(true)
                setError(undefined)
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
            >
              Sign In
            </Button>
            <Button
              variant={!isLogin ? "default" : "outline"}
              onClick={() => {
                setIsLogin(false)
                setError(undefined)
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
            >
              Sign Up
            </Button>
          </div>

          {isLogin ? (
            <LoginForm
              onLogin={handleLogin}
              isLoading={isLoading}
              error={error}
            />
          ) : (
            <RegisterForm
              onRegister={handleRegister}
              isLoading={isLoading}
              error={error}
            />
          )}
        </div>

        {/* Features */}
        <Card className="bg-gray-900 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white">Features</CardTitle>
            <CardDescription className="text-gray-400">
              What you can do with LectureAI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-gray-300">
            <div>• Upload and organize course materials</div>
            <div>• Generate AI-powered notes from documents</div>
            <div>• Search across all your course content</div>
            <div>• Transcribe audio lectures automatically</div>
            <div>• Track your usage and storage</div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
