import { Dashboard } from "@/components/dashboard"
import { AuthGuard } from "@/components/auth/auth-guard"

export default function HomePage() {
  return (
    <AuthGuard>
      <div className="container mx-auto px-4 py-8">
        <Dashboard />
      </div>
    </AuthGuard>
  )
}
