"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, User, Shield } from "lucide-react";
import AppLayout from "@/components/AppLayout";

export default function SettingsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
    } else {
      setToken(storedToken);
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <AppLayout>
      <div className="min-h-screen">
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="text-h1">Settings</h1>
            <p className="text-muted mt-1">Manage your account settings</p>
          </div>
        </header>

        {/* Main content */}
        <main className="container-app py-6">
          <div className="max-w-2xl">
            {/* Account section */}
            <div className="card mb-6">
              <div className="card-header">
                <h2 className="text-h3 flex items-center gap-2">
                  <User className="w-5 h-5" />
                  Account
                </h2>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                      Status
                    </label>
                    <p className="text-sm text-text-primary">
                      {token ? "Authenticated" : "Not authenticated"}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Security section */}
            <div className="card mb-6">
              <div className="card-header">
                <h2 className="text-h3 flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Security
                </h2>
              </div>
              <div className="card-body">
                <p className="text-sm text-text-secondary mb-4">
                  Your session is secured with JWT authentication.
                </p>
                <button
                  onClick={handleLogout}
                  className="btn btn-danger flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>

            {/* App info */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-h3">About</h2>
              </div>
              <div className="card-body">
                <div className="space-y-2 text-sm">
                  <p className="text-text-primary">
                    <span className="text-text-secondary">App:</span> Cogniflow
                  </p>
                  <p className="text-text-primary">
                    <span className="text-text-secondary">Version:</span> 1.0.0
                  </p>
                  <p className="text-text-primary">
                    <span className="text-text-secondary">Features:</span> RAG,
                    Agentic AI, Web Search
                  </p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </AppLayout>
  );
}
