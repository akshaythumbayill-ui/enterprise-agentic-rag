"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileText, Sparkles, Shield } from "lucide-react";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      router.push("/assistant");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container-app h-16 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-text-primary">
            Cogniflow
          </h1>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/login")}
              className="btn btn-ghost"
            >
              Sign In
            </button>
            <button
              onClick={() => router.push("/register")}
              className="btn btn-primary"
            >
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero section */}
      <main className="container-app py-20">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            <span>Enterprise AI Knowledge Assistant</span>
          </div>

          <h1 className="text-4xl font-semibold text-text-primary mb-6">
            Intelligent Document Analysis
          </h1>

          <p className="text-lg text-text-secondary mb-8 max-w-2xl mx-auto">
            Upload your documents and ask questions. Get accurate answers
            grounded in your knowledge base with retrieval-augmented generation
            and agentic AI.
          </p>

          <div className="flex items-center justify-center gap-4 mb-16">
            <button
              onClick={() => router.push("/register")}
              className="btn btn-primary px-6 py-3"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
            <button
              onClick={() => router.push("/login")}
              className="btn btn-secondary px-6 py-3"
            >
              Sign In
            </button>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <FileText className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-h3 mb-2">Document Upload</h3>
              <p className="text-muted text-sm">
                Upload PDFs and build your knowledge base
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-h3 mb-2">AI-Powered Search</h3>
              <p className="text-muted text-sm">
                Get accurate answers from your documents
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-h3 mb-2">Secure & Private</h3>
              <p className="text-muted text-sm">
                Enterprise-grade security for your data
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
