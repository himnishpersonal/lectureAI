import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import { Suspense } from "react"
import { Navigation } from "@/components/navigation"
import { AuthProvider } from "@/components/auth/auth-provider"
import "./globals.css"

export const metadata: Metadata = {
  title: "LectureAI - Smart Study Companion",
  description:
    "AI-powered educational platform for course management, document processing, and intelligent study notes",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable} min-h-screen bg-black text-white`}>
        <AuthProvider>
          <Navigation />
          <main>
            <Suspense fallback={null}>{children}</Suspense>
          </main>
        </AuthProvider>
        <Analytics />
      </body>
    </html>
  )
}
